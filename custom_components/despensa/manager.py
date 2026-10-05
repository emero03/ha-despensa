"""Gestor de datos de Despensa: inventario, stock mínimo y movimientos."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
import logging
import re
from typing import Any
import uuid

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .catalog import _stems, canonical_product, guess_product, normalize
from .const import (
    DEFAULT_DEPARTMENTS,
    DEFAULT_ICON,
    DEFAULT_SETTINGS,
    EVENT_LOW_STOCK,
    FALLBACK_DEPARTMENT,
    KIND_ADDED,
    KIND_PURCHASED,
    KIND_SET,
    KIND_USED,
    MAX_DELETED,
    MAX_LOG,
    MAX_STOCK,
    MERGE_WINDOW,
    SAVE_DELAY,
    SOURCE_CESTA,
    SOURCE_PANEL,
    STORAGE_KEY,
    STORAGE_VERSION,
)

_LOGGER = logging.getLogger(__name__)

UNSET: Any = object()

# "6", "x6", "6 uds", "pack de 6", "6 latas"... → 6. "2 L" o "1 kg" no cuentan como unidades.
_NOTE_QTY = re.compile(
    r"^(?:pack\s+de\s+|x\s*)?(\d{1,3})\s*(?:x|u|uds?\.?|unidades?|latas?|botes?|bricks?|"
    r"botellas?|paquetes?|cajas?|bolsas?|rollos?|piezas?|sobres?|tarros?|packs?)?$"
)


class DespensaError(Exception):
    """Error de operación (producto inexistente, nombre vacío...)."""

    def __init__(self, code: str, message: str, candidates: list[str] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.candidates = candidates or []


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


def _clean_name(name: str) -> str:
    name = re.sub(r"\s+", " ", str(name)).strip()
    return name[:1].upper() + name[1:] if name else name


def _now() -> float:
    return round(dt_util.utcnow().timestamp(), 3)


def _clamp_stock(value: Any) -> int:
    try:
        number = int(round(float(value)))
    except (TypeError, ValueError) as err:
        raise DespensaError("invalid_stock", f"Cantidad no válida: {value}") from err
    return max(0, min(MAX_STOCK, number))


def _clean_min(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return max(0, min(999, _clamp_stock(value)))


def quantity_from_note(note: str | None) -> int | None:
    """Unidades que indica el detalle de un producto de Cesta, si es un número de unidades."""
    text = normalize(note or "")
    if not text:
        return None
    if text in ("docena", "una docena"):
        return 12
    if text == "media docena":
        return 6
    if match := _NOTE_QTY.match(text):
        value = int(match.group(1))
        return value if value > 0 else None
    return None


class DespensaManager:
    """Fuente única de verdad del inventario. Las operaciones son síncronas
    (bucle de eventos) y avisan a los suscriptores (panel, sensor, puente con Cesta)."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.data: dict[str, Any] = {}
        self._listeners: list[Callable[[], None]] = []
        self._deleted: list[tuple[dict[str, Any], bool]] = []
        # Lo rellena el puente con Cesta
        self.cesta_available = False
        self.cesta_departments: list[dict[str, Any]] | None = None
        self.cesta_in_list: set[str] = set()
        # Se llama cuando un producto llega a su mínimo (lo usa el puente para la Cesta automática)
        self.on_low: Callable[[dict[str, Any]], None] | None = None

    # ------------------------------------------------------------------ carga
    async def async_load(self) -> None:
        stored = await self._store.async_load() or {}
        self.data = {
            "items": stored.get("items", []),
            "log": stored.get("log", []),
            "settings": {**DEFAULT_SETTINGS, **stored.get("settings", {})},
            "ignored": stored.get("ignored", {}),
            "cesta": stored.get("cesta") or {"watermark": _now(), "watermark_keys": []},
        }

    @callback
    def async_add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        self._listeners.append(listener)

        @callback
        def remove() -> None:
            if listener in self._listeners:
                self._listeners.remove(listener)

        return remove

    @callback
    def _changed(self, save: bool = True) -> None:
        if save:
            self._store.async_delay_save(lambda: self.data, SAVE_DELAY)
        for listener in list(self._listeners):
            try:
                listener()
            except Exception:  # pragma: no cover - un oyente roto no debe romper el resto
                _LOGGER.exception("Error notificando un cambio de Despensa")

    @callback
    def snapshot(self) -> dict[str, Any]:
        """Estado completo para el panel."""
        return {
            "items": deepcopy(self.items),
            "log": deepcopy(self.log),
            "settings": dict(self.settings),
            "ignored": sorted(self.data["ignored"].values(), key=normalize),
            "departments": self.departments,
            "cesta": {"available": self.cesta_available, "in_list": sorted(self.cesta_in_list)},
        }

    # -------------------------------------------------------------- utilidades
    @property
    def items(self) -> list[dict[str, Any]]:
        return self.data["items"]

    @property
    def log(self) -> list[dict[str, Any]]:
        return self.data["log"]

    @property
    def settings(self) -> dict[str, Any]:
        return self.data["settings"]

    @property
    def departments(self) -> list[dict[str, Any]]:
        """Baldas: los departamentos de Cesta si está instalada; si no, los de serie."""
        return deepcopy(self.cesta_departments or DEFAULT_DEPARTMENTS)

    def department_ids(self) -> list[str]:
        return [d["id"] for d in self.departments]

    def _fallback_department(self) -> str:
        ids = self.department_ids()
        return FALLBACK_DEPARTMENT if FALLBACK_DEPARTMENT in ids else ids[-1]

    def resolve_department(self, value: str | None) -> str | None:
        """Acepta el id o el nombre de un departamento."""
        if not value:
            return None
        key = normalize(value)
        for dept in self.departments:
            if dept["id"] == value or normalize(dept["name"]) == key:
                return dept["id"]
        return None

    @staticmethod
    def is_low(item: dict[str, Any]) -> bool:
        """Por reponer: el stock ha llegado al mínimo (o por debajo)."""
        return item.get("min_stock") is not None and item["stock"] <= item["min_stock"]

    def low_items(self) -> list[dict[str, Any]]:
        return [i for i in self.sorted_items() if self.is_low(i)]

    def sorted_items(self) -> list[dict[str, Any]]:
        order = {dept_id: n for n, dept_id in enumerate(self.department_ids())}
        return sorted(self.items, key=lambda i: (order.get(i["department"], 999), normalize(i["name"])))

    def get_item(self, item_id: str) -> dict[str, Any]:
        for item in self.items:
            if item["id"] == item_id:
                return item
        raise DespensaError("not_found", f"No hay ningún producto con id {item_id}")

    def find_by_name(self, name: str) -> dict[str, Any] | None:
        """Producto con ese nombre (sin tildes/mayúsculas; acepta singular/plural)."""
        key = normalize(name)
        if not key:
            return None
        for item in self.items:
            if normalize(item["name"]) == key:
                return item
        stems = _stems(name)
        return next((i for i in self.items if _stems(i["name"]) == stems), None)

    def find(self, text: str) -> dict[str, Any]:
        """Busca un producto a partir de lo que dice una persona ("atún", "leche entera").

        Lanza DespensaError("not_found") o DespensaError("ambiguous", candidates=[...]).
        """
        if item := self.find_by_name(text):
            return item
        if (canon := canonical_product(text)) and (item := self.find_by_name(canon["name"])):
            return item
        words = _stems(text)
        if not words:
            raise DespensaError("not_found", "No has dicho qué producto")

        def contains(haystack: list[str], needle: list[str]) -> bool:
            size = len(needle)
            return any(haystack[i : i + size] == needle for i in range(len(haystack) - size + 1))

        # "atún" → "Atún en lata"
        wider = [i for i in self.items if contains(_stems(i["name"]), words)]
        if len(wider) > 1:
            in_stock = [i for i in wider if i["stock"] > 0]
            wider = in_stock if len(in_stock) == 1 else wider
        if len(wider) == 1:
            return wider[0]
        if len(wider) > 1:
            names = [i["name"] for i in sorted(wider, key=lambda i: normalize(i["name"]))]
            raise DespensaError("ambiguous", f"Hay varios productos: {', '.join(names)}", names)

        # "leche entera de oferta" → "Leche": el producto más largo contenido en lo dicho
        narrower = [i for i in self.items if contains(words, _stems(i["name"]))]
        if narrower:
            return max(narrower, key=lambda i: len(_stems(i["name"])))
        raise DespensaError("not_found", f"«{_clean_name(text)}» no está en la despensa")

    # ------------------------------------------------------------- movimientos
    def _log(
        self, item: dict[str, Any], delta: int, kind: str, source: str, *, created: bool = False
    ) -> dict[str, Any]:
        """Apunta un movimiento. Varias pulsaciones seguidas en el panel se agrupan."""
        now = _now()
        last = self.log[0] if self.log else None
        if (
            last is not None
            and source == SOURCE_PANEL
            and not created
            and not last.get("created")
            and last["item_id"] == item["id"]
            and last["source"] == source
            and last["kind"] == kind
            and now - last["ts"] <= MERGE_WINDOW
        ):
            last["delta"] += delta
            last["stock"] = item["stock"]
            last["ts"] = now
            if last["delta"] == 0 and kind != KIND_SET:
                self.log.pop(0)
                return {**last, "id": None}
            return last
        entry = {
            "id": _new_id(),
            "ts": now,
            "item_id": item["id"],
            "name": item["name"],
            "icon": item["icon"],
            "department": item["department"],
            "delta": delta,
            "stock": item["stock"],
            "kind": kind,
            "source": source,
            "created": created,
        }
        self.log.insert(0, entry)
        del self.log[MAX_LOG:]
        return entry

    def _stock_changed(self, item: dict[str, Any], was_low: bool) -> None:
        """Si acaba de llegar al mínimo: evento para automatizaciones y Cesta automática."""
        item["updated_at"] = _now()
        if was_low or not self.is_low(item):
            return
        self.hass.bus.async_fire(
            EVENT_LOW_STOCK,
            {
                "name": item["name"],
                "icon": item["icon"],
                "stock": item["stock"],
                "min_stock": item["min_stock"],
                "unit": item.get("unit", ""),
                "in_cesta": normalize(item["name"]) in self.cesta_in_list,
            },
        )
        if self.on_low is not None:
            self.on_low(item)

    # ------------------------------------------------------------- operaciones
    @callback
    def create_item(
        self,
        name: str,
        *,
        stock: int | None = None,
        icon: str | None = None,
        department: str | None = None,
        min_stock: Any = UNSET,
        unit: str | None = None,
        pack: int | None = None,
        source: str = SOURCE_PANEL,
        kind: str = KIND_ADDED,
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        """Añade un producto. Si ya existe, suma las unidades. Devuelve (producto, movimiento)."""
        name = _clean_name(name)
        if not name:
            raise DespensaError("invalid_name", "El nombre no puede estar vacío")
        amount = 1 if stock is None else _clamp_stock(stock)

        if existing := self.find_by_name(name):
            if not amount:
                return existing, None
            return existing, self.adjust(existing["id"], amount, kind=kind, source=source)

        if canon := canonical_product(name):
            name = canon["name"]  # "tomate" → "Tomates", como en Cesta
        guess = guess_product(name)
        dept = self.resolve_department(department)
        if dept is None:
            dept = guess["department"] if guess else None
        if dept not in self.department_ids():
            dept = self._fallback_department()

        item = {
            "id": _new_id(),
            "name": name,
            "icon": (icon or "").strip() or (guess["icon"] if guess else DEFAULT_ICON),
            "department": dept,
            "stock": amount,
            "min_stock": _clean_min(self.settings.get("default_min") if min_stock is UNSET else min_stock),
            "unit": (unit or "").strip()[:20],
            "pack": max(1, min(999, int(pack or 1))),
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.items.append(item)
        self.data["ignored"].pop(normalize(name), None)
        entry = self._log(item, amount, kind, source, created=True)
        self._stock_changed(item, was_low=False)
        self._changed()
        return item, entry

    @callback
    def adjust(
        self, item_id: str, delta: int, *, kind: str | None = None, source: str = SOURCE_PANEL
    ) -> dict[str, Any]:
        """Suma o resta unidades (sin bajar de 0). Devuelve el movimiento."""
        item = self.get_item(item_id)
        was_low = self.is_low(item)
        before = item["stock"]
        item["stock"] = _clamp_stock(before + int(delta))
        real = item["stock"] - before
        if kind is None:
            kind = KIND_ADDED if real >= 0 else KIND_USED
        entry = self._log(item, real, kind, source)
        self._stock_changed(item, was_low)
        self._changed()
        return entry

    @callback
    def set_stock(
        self, item_id: str, stock: int, *, kind: str = KIND_SET, source: str = SOURCE_PANEL
    ) -> dict[str, Any]:
        """Fija el stock (por ejemplo, a 0 cuando "se ha acabado")."""
        item = self.get_item(item_id)
        was_low = self.is_low(item)
        before = item["stock"]
        item["stock"] = _clamp_stock(stock)
        entry = self._log(item, item["stock"] - before, kind, source)
        self._stock_changed(item, was_low)
        self._changed()
        return entry

    @callback
    def update_item(self, item_id: str, **changes: Any) -> dict[str, Any]:
        """Edita nombre, icono, balda, mínimo, unidad o unidades por compra."""
        item = self.get_item(item_id)
        if changes.get("name") is not None:
            name = _clean_name(changes["name"])
            if not name:
                raise DespensaError("invalid_name", "El nombre no puede estar vacío")
            other = self.find_by_name(name)
            if other is not None and other is not item:
                raise DespensaError("duplicate", f"Ya tienes «{other['name']}» en la despensa")
            item["name"] = name
        if changes.get("icon"):
            item["icon"] = str(changes["icon"]).strip()
        if changes.get("department") is not None:
            item["department"] = (
                self.resolve_department(changes["department"]) or self._fallback_department()
            )
        if "min_stock" in changes:
            item["min_stock"] = _clean_min(changes["min_stock"])
        if changes.get("unit") is not None:
            item["unit"] = str(changes["unit"]).strip()[:20]
        if changes.get("pack") is not None:
            item["pack"] = max(1, min(999, _clamp_stock(changes["pack"])))
        if changes.get("stock") is not None and _clamp_stock(changes["stock"]) != item["stock"]:
            self.set_stock(item_id, changes["stock"])
            return item
        item["updated_at"] = _now()
        self._changed()
        return item

    @callback
    def delete_item(self, item_id: str, ignore: bool = False) -> dict[str, Any]:
        """Quita un producto. Con ignore=True no se volverá a añadir al comprarlo en Cesta."""
        item = self.get_item(item_id)
        self.items.remove(item)
        key = normalize(item["name"])
        newly_ignored = ignore and key not in self.data["ignored"]
        if ignore:
            self.data["ignored"][key] = item["name"]
        self._deleted.insert(0, (item, newly_ignored))
        del self._deleted[MAX_DELETED:]
        self._changed()
        return item

    @callback
    def restore_deleted(self, item_id: str) -> dict[str, Any]:
        """Deshace "Quitar de la despensa"."""
        for index, (item, newly_ignored) in enumerate(self._deleted):
            if item["id"] == item_id:
                self._deleted.pop(index)
                if self.find_by_name(item["name"]) is None:
                    self.items.append(item)
                if newly_ignored:
                    self.data["ignored"].pop(normalize(item["name"]), None)
                self._changed()
                return item
        raise DespensaError("not_found", "Ya no se puede recuperar")

    @callback
    def undo(self, log_id: str) -> dict[str, Any] | None:
        """Deshace un movimiento: devuelve las unidades y lo borra del historial."""
        entry = next((e for e in self.log if e["id"] == log_id), None)
        if entry is None:
            raise DespensaError("not_found", "Ese movimiento ya no existe")
        self.log.remove(entry)
        item = next((i for i in self.items if i["id"] == entry["item_id"]), None)
        if item is None:
            self._changed()
            return None
        if entry.get("created") and not any(e["item_id"] == item["id"] for e in self.log):
            self.items.remove(item)  # se creó con este movimiento: deshacer lo quita
            self._changed()
            return None
        was_low = self.is_low(item)
        item["stock"] = _clamp_stock(item["stock"] - entry["delta"])
        self._stock_changed(item, was_low)
        self._changed()
        return item

    @callback
    def clear_log(self) -> None:
        self.log.clear()
        self._changed()

    @callback
    def set_settings(self, **changes: Any) -> None:
        for key, value in changes.items():
            if key not in DEFAULT_SETTINGS:
                continue
            if key == "default_min":
                value = _clean_min(value)
            else:
                value = bool(value)
            self.settings[key] = value
        self._changed()

    @callback
    def unignore(self, name: str) -> None:
        self.data["ignored"].pop(normalize(name), None)
        self._changed()

    # ------------------------------------------------------------------ Cesta
    @callback
    def apply_purchase(self, entry: dict[str, Any]) -> dict[str, Any] | None:
        """Algo se ha marcado como comprado en Cesta: suma las unidades.

        Devuelve el movimiento creado (para poder revertirlo si en Cesta se deshace)
        o None si el producto no se controla en la despensa.
        """
        name = entry.get("name") or ""
        key = normalize(name)
        if not key or key in self.data["ignored"]:
            return None
        item = self.find_by_name(name)
        if item is None and not self.settings.get("add_from_cesta", True):
            return None
        amount = quantity_from_note(entry.get("note"))
        if item is not None:
            return self.adjust(
                item["id"], amount or item.get("pack", 1), kind=KIND_PURCHASED, source=SOURCE_CESTA
            )
        _item, log_entry = self.create_item(
            name,
            stock=amount or 1,
            icon=entry.get("icon"),
            department=entry.get("department"),
            source=SOURCE_CESTA,
            kind=KIND_PURCHASED,
        )
        return log_entry

    @callback
    def revert_purchase(self, log_entry: dict[str, Any]) -> None:
        """En Cesta se ha deshecho una compra: se quita lo que se había sumado."""
        if any(e["id"] == log_entry["id"] for e in self.log):
            self.undo(log_entry["id"])
            return
        # El movimiento ya no está en el historial (lo vaciaron): solo se restan las unidades.
        item = next((i for i in self.items if i["id"] == log_entry["item_id"]), None)
        if item is not None:
            was_low = self.is_low(item)
            item["stock"] = _clamp_stock(item["stock"] - log_entry["delta"])
            self._stock_changed(item, was_low)
            self._changed()

    @callback
    def set_cesta_info(
        self,
        available: bool,
        departments: list[dict[str, Any]] | None,
        in_list: set[str],
    ) -> None:
        """El puente informa de lo que hay en Cesta (baldas, colores, qué está en la lista)."""
        departments = deepcopy(departments) if departments else None
        if (
            available == self.cesta_available
            and departments == self.cesta_departments
            and in_list == self.cesta_in_list
        ):
            return
        self.cesta_available = available
        self.cesta_departments = departments
        self.cesta_in_list = set(in_list)
        self._changed(save=False)

    @callback
    def set_cesta_watermark(self, watermark: float, keys: list[str]) -> None:
        self.data["cesta"] = {"watermark": watermark, "watermark_keys": keys}
        self._store.async_delay_save(lambda: self.data, SAVE_DELAY)
