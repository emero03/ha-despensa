"""Puente con Cesta (https://github.com/emero03/ha-cesta).

No modifica Cesta: se suscribe a los cambios de su gestor (el mismo mecanismo que usan
su panel y su entidad todo) y compara su lista de "Comprado recientemente":

- Cada compra nueva suma unidades en la despensa (o crea el producto en su balda).
- Si en Cesta se pulsa "Deshacer", la compra desaparece de su historial y aquí se resta.
- Se copian las baldas (departamentos, orden y colores) y qué productos están en la lista.

Para añadir a la Cesta se usa su acción pública `cesta.add_item`.
"""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.const import EVENT_COMPONENT_LOADED
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from .catalog import normalize
from .const import CESTA_DOMAIN, CESTA_UNDO_WINDOW
from .manager import DespensaError, DespensaManager

_LOGGER = logging.getLogger(__name__)

CHECK_INTERVAL = timedelta(seconds=30)


def _looks_like_cesta(obj: Any) -> bool:
    data = getattr(obj, "data", None)
    return (
        obj is not None
        and callable(getattr(obj, "async_add_listener", None))
        and isinstance(data, dict)
        and isinstance(data.get("recent"), list)
        and isinstance(data.get("items"), list)
    )


class CestaBridge:
    """Mantiene la despensa sincronizada con Cesta."""

    def __init__(self, hass: HomeAssistant, manager: DespensaManager) -> None:
        self.hass = hass
        self.manager = manager
        self._cesta: Any = None
        self._unsub_cesta: Any = None
        self._unsubs: list[Any] = []
        # Compras aplicadas que aún se pueden deshacer en Cesta:
        # (id en Cesta, fecha) → (movimiento, nombre normalizado, cuándo se aplicó)
        self._pending: dict[tuple[str, float], tuple[dict[str, Any], str, float]] = {}

    @property
    def available(self) -> bool:
        return self._cesta is not None

    # ------------------------------------------------------------ ciclo de vida
    @callback
    def async_start(self) -> None:
        self.manager.on_low = self._on_low
        self._unsubs.append(async_track_time_interval(self.hass, self._tick, CHECK_INTERVAL))
        self._unsubs.append(self.hass.bus.async_listen(EVENT_COMPONENT_LOADED, self._on_loaded))
        self._attach()

    @callback
    def async_stop(self) -> None:
        self.manager.on_low = None
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        self._detach()

    @callback
    def _on_loaded(self, event: Event) -> None:
        if event.data.get("component") == CESTA_DOMAIN:
            self._attach()

    @callback
    def _tick(self, _now: Any = None) -> None:
        """Se vuelve a enganchar si Cesta se ha recargado, y caducan los 'Deshacer'."""
        self._attach()
        limit = dt_util.utcnow().timestamp() - CESTA_UNDO_WINDOW
        for key, (_entry, _name, applied) in list(self._pending.items()):
            if applied < limit:
                del self._pending[key]

    @callback
    def _attach(self) -> None:
        cesta = self.hass.data.get(CESTA_DOMAIN)
        if not _looks_like_cesta(cesta):
            cesta = None
        if cesta is self._cesta:
            return
        self._detach()
        if cesta is None:
            self.manager.set_cesta_info(False, None, set())
            return
        self._cesta = cesta
        self._unsub_cesta = cesta.async_add_listener(self._on_cesta_change)
        _LOGGER.debug("Conectada con Cesta")
        self._on_cesta_change()

    @callback
    def _detach(self) -> None:
        if self._unsub_cesta is not None:
            self._unsub_cesta()
        self._unsub_cesta = None
        self._cesta = None

    # ------------------------------------------------------------ cambios en Cesta
    @callback
    def _on_cesta_change(self) -> None:
        if self._cesta is None:
            return
        data = self._cesta.data
        recent: list[dict[str, Any]] = data.get("recent", [])
        self.manager.set_cesta_info(
            True,
            data.get("departments"),
            {normalize(item.get("name", "")) for item in data.get("items", [])},
        )
        self._apply_new_purchases(recent)
        self._detect_undo(recent, data.get("products", {}))

    def _apply_new_purchases(self, recent: list[dict[str, Any]]) -> None:
        state = self.manager.data["cesta"]
        watermark: float = state.get("watermark", 0)
        seen = set(state.get("watermark_keys", []))
        new = []
        for entry in recent:
            if entry.get("kind") != "purchased":
                continue
            ts = entry.get("purchased_at") or 0
            key = str(entry.get("id", ""))
            if ts > watermark or (ts == watermark and key not in seen):
                new.append((ts, key, entry))
        if not new:
            return
        new.sort(key=lambda n: n[0])
        now = dt_util.utcnow().timestamp()
        for ts, key, entry in new:
            log_entry = self.manager.apply_purchase(entry)
            if log_entry is not None:
                self._pending[(key, ts)] = (dict(log_entry), normalize(entry.get("name", "")), now)
        top = new[-1][0]
        keys = [key for ts, key, _ in new if ts == top]
        if top == watermark:
            keys = sorted(seen | set(keys))
        self.manager.set_cesta_watermark(top, keys)

    def _detect_undo(self, recent: list[dict[str, Any]], products: dict[str, Any]) -> None:
        if not self._pending:
            return
        present = {
            (str(r.get("id", "")), r.get("purchased_at")) for r in recent if r.get("kind") == "purchased"
        }
        for key, (log_entry, name, _applied) in list(self._pending.items()):
            if key in present:
                continue
            del self._pending[key]
            # Deshacer en Cesta quita la fecha del historial de compras; volver a añadirlo
            # a la lista o borrarlo de "recientes" no la quita (sí se compró).
            purchases = (products.get(name) or {}).get("purchases", [])
            if key[1] not in purchases:
                _LOGGER.debug("Compra deshecha en Cesta: %s", name)
                self.manager.revert_purchase(log_entry)

    # ------------------------------------------------------------ añadir a Cesta
    def in_cesta(self, item: dict[str, Any]) -> bool:
        return normalize(item["name"]) in self.manager.cesta_in_list

    async def async_add(self, item: dict[str, Any]) -> bool:
        """Añade un producto a la lista de Cesta. Devuelve False si ya estaba."""
        if not self.hass.services.has_service(CESTA_DOMAIN, "add_item"):
            raise DespensaError("no_cesta", "Cesta no está instalada o no está configurada")
        if self.in_cesta(item):
            return False
        await self.hass.services.async_call(
            CESTA_DOMAIN,
            "add_item",
            {"name": item["name"], "icon": item["icon"], "department": item["department"]},
            blocking=True,
        )
        return True

    async def async_add_low(self) -> list[str]:
        """Añade a la Cesta todo lo que está por reponer. Devuelve lo que se ha añadido."""
        added = []
        for item in self.manager.low_items():
            if await self.async_add(item):
                added.append(item["name"])
        return added

    @callback
    def _on_low(self, item: dict[str, Any]) -> None:
        if not self.manager.settings.get("auto_cesta") or not self.available or self.in_cesta(item):
            return
        self.hass.async_create_task(self._auto_add(dict(item)), eager_start=True)

    async def _auto_add(self, item: dict[str, Any]) -> None:
        try:
            await self.async_add(item)
        except Exception:  # noqa: BLE001 - un fallo aquí no debe romper el uso por voz
            _LOGGER.warning("No se pudo añadir %s a la Cesta automáticamente", item["name"], exc_info=True)
