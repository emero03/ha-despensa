"""Voz: "He usado dos latas de atún", "Se ha acabado la leche", "¿Cuánto arroz queda?"...

Dos vías, que comparten la misma lógica:

1. Intents de Home Assistant (DespensaUseItem, DespensaAddItem...). Los usan los agentes
   de conversación con IA (OpenAI, Claude, Gemini, Ollama… con la API de Assist activada)
   y una skill personalizada de Alexa a través de la integración `alexa`.
2. Frases en español para el agente de Assist de Home Assistant (Home Assistant Voice,
   la app del móvil, satélites ESPHome…). Se registran solas al cargar la integración.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
import logging
import re
from typing import Any

import voluptuous as vol

from homeassistant.const import EVENT_COMPONENT_LOADED
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import config_validation as cv, intent

from .catalog import normalize
from .const import DOMAIN, KIND_EMPTY, KIND_USED, SOURCE_VOICE
from .manager import DespensaError, DespensaManager

_LOGGER = logging.getLogger(__name__)

INTENT_USE = "DespensaUseItem"
INTENT_EMPTY = "DespensaEmptyItem"
INTENT_ADD = "DespensaAddItem"
INTENT_STOCK = "DespensaGetStock"
INTENT_LOW = "DespensaListLow"
INTENT_TO_CESTA = "DespensaAddLowToCesta"

# ------------------------------------------------------------------ frases (Assist)
# Sintaxis de Home Assistant: (a|b) alternativas, [x] opcional, {producto} lo que se diga.
_V_USE = "(usado|gastado|consumido|cogido|abierto|tomado|utilizado|sacado)"
_V_USE_PAST = "(usé|use|gasté|gaste|consumí|consumi|cogí|cogi|abrí|abri|utilicé|utilice|saqué|saque)"
_HOW_MUCH = "(cuánto|cuánta|cuántos|cuántas|cuanto|cuanta|cuantos|cuantas)"
_LEFT = "(queda|quedan|tengo|tenemos|me queda|me quedan|nos queda|nos quedan)"
_WHERE = "en (la despensa|casa)"
# "hay" solo junto a "en la despensa": "¿cuántas personas hay en casa?" es de Home Assistant.
_LOW_WHAT = "lo que (falta|se está acabando|se esta acabando|hay que reponer|hay que comprar)"
_CESTA = "la (cesta|lista de la compra|compra)"

SENTENCES: dict[str, list[str]] = {
    INTENT_USE: [
        f"(he|hemos) {_V_USE} {{producto}}",
        f"{_V_USE_PAST} {{producto}}",
        f"apunta que (he|hemos) {_V_USE} {{producto}}",
        "(resta|quita|descuenta|saca) {producto} de la despensa",
    ],
    INTENT_EMPTY: [
        "se (ha|han) (acabado|terminado|agotado) {producto}",
        "se (acabó|acabo|acabaron|terminó|termino|terminaron|agotó|agoto|agotaron) {producto}",
        "{producto} se (ha|han) (acabado|terminado|agotado)",
        "(he|hemos) (acabado|terminado|vaciado) {producto}",
        "(acabé|acabe|terminé|termine|vacié|vacie|acabamos|terminamos) {producto}",
    ],
    INTENT_ADD: [
        "(he|hemos) (comprado|repuesto|traído|traido) {producto}",
        "(compré|compre|traje|repuse|compramos) {producto}",
        "(añade|añadir|mete|guarda|suma|pon) {producto} (a|en) la despensa",
    ],
    INTENT_STOCK: [
        f"{_HOW_MUCH} {{producto}} {_LEFT} [{_WHERE}]",
        f"{_HOW_MUCH} {{producto}} hay en la despensa",
        f"{_HOW_MUCH} (queda|hay) de {{producto}} en la despensa",
        f"qué cantidad de {{producto}} (queda|quedan|hay|tengo|tenemos) [{_WHERE}]",
        "(queda|quedan|hay) {producto} en la despensa",
        f"(tengo|tenemos) {{producto}} {_WHERE}",
        "(me|nos) (queda|quedan) {producto}",
    ],
    INTENT_LOW: [
        "qué (falta|hace falta|tengo que comprar|hay que comprar|tenemos que comprar|necesito comprar"
        f"|necesitamos comprar|hay que reponer|tengo que reponer) [{_WHERE}]",
        "qué (se está acabando|se esta acabando|está por reponer|esta por reponer)",
        "qué (hay|tengo|tenemos) (por reponer|que reponer)",
        f"(dime|lee|léeme|leeme) {_LOW_WHAT} [{_WHERE}]",
    ],
    INTENT_TO_CESTA: [
        f"(añade|pon|mete|apunta|pasa|manda) [todo] {_LOW_WHAT} (a|en) {_CESTA}",
        f"(añade|pon|mete|apunta|pasa|manda) (a|en) {_CESTA} [todo] {_LOW_WHAT}",
    ],
}

# ------------------------------------------------------------- lectura de lo dicho
_NUMBERS = {
    "un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6,
    "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "once": 11, "doce": 12, "quince": 15,
    "veinte": 20, "treinta": 30,
}
_ARTICLES = {
    "el", "la", "los", "las", "lo", "unos", "unas", "del", "al", "mi", "mis", "nuestro",
    "nuestra", "nuestros", "nuestras", "otro", "otra", "otros", "otras", "ultimo", "ultima",
    "ultimos", "ultimas", "poco", "poquito", "algo", "de",
}
_ALL = {"todo", "toda", "todos", "todas"}
_CONTAINERS = {
    "lata", "bote", "brick", "botella", "paquete", "caja", "bolsa", "rollo", "pieza", "sobre",
    "tarro", "pack", "unidad", "ud", "kilo", "kg", "litro", "tableta", "barra", "docena",
    "carton", "envase", "tarrina", "bandeja", "rebanada", "trozo", "vaso", "taza", "capsula",
    "bolsita", "garrafa", "frasco", "tubo", "loncha", "filete", "racion", "plato",
}
_TRAILING = [
    ["de", "la", "despensa"], ["en", "la", "despensa"], ["de", "casa"], ["en", "casa"],
    ["por", "favor"], ["ya"], ["entero"], ["entera"], ["enteros"], ["enteras"],
    ["me"], ["nos"],  # "¿cuántos huevos nos quedan?" deja "huevos nos"
]


def _singular(word: str) -> str:
    """Singular aproximado de una unidad: latas → lata, unidades → unidad, botes → bote."""
    if word.endswith("es") and len(word) > 4 and word[-3] in "dlnzj":
        return word[:-2]
    if word.endswith("s") and len(word) > 2:
        return word[:-1]
    return word


def _is_container(word: str) -> bool:
    return word in _CONTAINERS or _singular(word) in _CONTAINERS or word[:-2] in _CONTAINERS


def parse_spoken(text: str) -> tuple[int | None, bool, list[str]]:
    """Separa cantidad y producto: "dos latas de atún" → (2, False, ["latas de atún", "atún"]).

    Devuelve (cantidad o None, si se dijo "todo", textos candidatos de más a menos literal).
    """
    raw = re.sub(r"[¿?¡!.,;:]", " ", str(text)).split()
    words = [normalize(w) for w in raw]
    trimmed = True
    while trimmed:
        trimmed = False
        for tail in _TRAILING:
            if len(words) > len(tail) and words[-len(tail) :] == tail:
                raw, words = raw[: -len(tail)], words[: -len(tail)]
                trimmed = True

    quantity: int | None = None
    take_all = False
    start = 0
    while start < len(words):
        word = words[start]
        nxt = words[start + 1] if start + 1 < len(words) else ""
        if word.isdigit():
            quantity = int(word)
        elif word == "media" and nxt == "docena":
            quantity = 6
            start += 1
        elif word == "docena":
            quantity = 12 * (quantity or 1)
        elif word == "par" and quantity in (None, 1):
            quantity = 2
        elif word in _NUMBERS and quantity is None:
            quantity = _NUMBERS[word]
        elif word in _ALL:
            take_all = True
        elif word not in _ARTICLES:
            break
        start += 1
    raw, words = raw[start:], words[start:]
    candidates = []
    if raw:
        candidates.append(" ".join(raw))
        # "latas de atún" → "atún" ("cápsulas de café" se prueba antes tal cual)
        if len(words) > 2 and _is_container(words[0]) and words[1] == "de":
            candidates.append(" ".join(raw[2:]))
    return quantity, take_all, candidates


def _resolve(manager: DespensaManager, text: str) -> tuple[dict[str, Any], int | None, bool]:
    quantity, take_all, candidates = parse_spoken(text)
    if not candidates:
        raise DespensaError("not_found", "No he entendido qué producto")
    error: DespensaError | None = None
    for candidate in candidates:
        try:
            return manager.find(candidate), quantity, take_all
        except DespensaError as err:
            if err.code == "ambiguous":
                raise
            error = error or err
    assert error is not None
    raise error


# --------------------------------------------------------------- textos hablados
def _unit(unit: str, count: int) -> str:
    unit = unit.strip()
    if count == 1 and unit.endswith("s") and len(unit) > 2:
        return _singular(unit)
    return unit


def _lname(item: dict[str, Any]) -> str:
    return item["name"][:1].lower() + item["name"][1:]


def _name_with_unit(item: dict[str, Any]) -> str:
    """Nombre sin repetir la unidad: "Atún en lata" contado en latas → "atún"."""
    name = _lname(item)
    unit = normalize(item.get("unit") or "")
    if not unit:
        return name
    key = normalize(name)
    for u in {unit, _singular(unit)}:
        if key.endswith(f" en {u}") and len(key) > len(u) + 4:
            return name[: -len(u) - 4]
        if key.startswith(f"{u} de ") and len(key) > len(u) + 4:
            return name[len(u) + 4 :]
    return name


def describe_stock(item: dict[str, Any]) -> str:
    """"Te quedan 3 bricks de leche." / "De arroz te queda 1." / "No queda nada de café."."""
    stock = item["stock"]
    if stock <= 0:
        return f"No queda nada de {_lname(item)}."
    verb = "queda" if stock == 1 else "quedan"
    if item.get("unit"):
        return f"Te {verb} {stock} {_unit(item['unit'], stock)} de {_name_with_unit(item)}."
    return f"De {_lname(item)} te {verb} {stock}."


def _join(names: list[str]) -> str:
    names = [n[:1].lower() + n[1:] for n in names]
    if len(names) <= 1:
        return "".join(names)
    return ", ".join(names[:-1]) + " y " + names[-1]


def _low_suffix(manager: DespensaManager, item: dict[str, Any], was_low: bool, in_cesta: bool) -> str:
    """Aviso al llegar al mínimo (in_cesta: si ya estaba en la Cesta antes de usarlo)."""
    if was_low or not manager.is_low(item):
        return ""
    empty = item["stock"] <= 0  # "no queda nada" ya lo dice todo
    if in_cesta:
        return " Ya está en la Cesta." if empty else " Ya estás en el mínimo y ya está en la Cesta."
    if manager.settings.get("auto_cesta") and manager.cesta_available:
        return " Lo añado a la Cesta." if empty else " Ya estás en el mínimo: lo añado a la Cesta."
    return "" if empty else " Ya estás en el mínimo."


def _manager(hass: HomeAssistant) -> DespensaManager:
    manager = hass.data.get(DOMAIN)
    if manager is None:
        raise DespensaError("not_loaded", "La despensa no está configurada")
    return manager


# --------------------------------------------------------------------- acciones
async def async_use(hass: HomeAssistant, text: str, quantity: int | None = None, *, empty: bool = False) -> str:
    """He usado / se ha acabado."""
    manager = _manager(hass)
    item, said_quantity, take_all = _resolve(manager, text)
    was_low = manager.is_low(item)
    in_cesta = normalize(item["name"]) in manager.cesta_in_list
    before = item["stock"]
    if empty or take_all:
        manager.set_stock(item["id"], 0, kind=KIND_EMPTY, source=SOURCE_VOICE)
        speech = f"Apuntado: no queda nada de {_lname(item)}."
    else:
        manager.adjust(item["id"], -(quantity or said_quantity or 1), kind=KIND_USED, source=SOURCE_VOICE)
        if before <= 0:
            speech = f"Según la despensa ya no quedaba {_lname(item)}; lo dejo a cero."
        else:
            speech = "Hecho. " + describe_stock(item)
    return speech + _low_suffix(manager, item, was_low, in_cesta)


async def async_add(hass: HomeAssistant, text: str, quantity: int | None = None) -> str:
    """He comprado / añade a la despensa."""
    manager = _manager(hass)
    said_quantity: int | None = None
    try:
        item, said_quantity, _all = _resolve(manager, text)
        amount = quantity or said_quantity or item.get("pack", 1)
        manager.adjust(item["id"], amount, source=SOURCE_VOICE)
        return "Hecho. " + describe_stock(item)
    except DespensaError as err:
        if err.code != "not_found":
            raise
    said_quantity, _all, candidates = parse_spoken(text)
    if not candidates:
        raise DespensaError("not_found", "No he entendido qué producto")
    name = candidates[-1] if len(candidates) > 1 else candidates[0]
    item, _entry = manager.create_item(name, stock=quantity or said_quantity or 1, source=SOURCE_VOICE)
    return f"He añadido {_lname(item)} a la despensa. " + describe_stock(item)


async def async_stock(hass: HomeAssistant, text: str) -> str:
    manager = _manager(hass)
    item, _q, _a = _resolve(manager, text)
    speech = describe_stock(item)
    if manager.is_low(item):
        if normalize(item["name"]) in manager.cesta_in_list:
            speech += " Ya está en la Cesta."
        elif item["stock"] > 0:
            speech += " Está en el mínimo."
    return speech


async def async_list_low(hass: HomeAssistant) -> str:
    manager = _manager(hass)
    low = manager.low_items()
    if not low:
        return "No falta nada: todo está por encima del mínimo."
    names = [i["name"] for i in low]
    speech = f"Hay que reponer {_join(names)}."
    in_cesta = [i for i in low if normalize(i["name"]) in manager.cesta_in_list]
    if in_cesta and len(in_cesta) == len(low):
        speech += " Ya está todo en la Cesta."
    elif in_cesta:
        speech += f" Ya están en la Cesta: {_join([i['name'] for i in in_cesta])}."
    return speech


async def async_low_to_cesta(hass: HomeAssistant) -> str:
    manager = _manager(hass)
    bridge = hass.data.get(f"{DOMAIN}_bridge")
    if bridge is None or not bridge.available:
        raise DespensaError("no_cesta", "Cesta no está instalada")
    if not manager.low_items():
        return "No hay nada por reponer."
    added = await bridge.async_add_low()
    if not added:
        return "Ya estaba todo en la Cesta."
    count = len(added)
    return f"He añadido {count} {'producto' if count == 1 else 'productos'} a la Cesta: {_join(added)}."


def error_speech(err: DespensaError) -> str:
    if err.code == "ambiguous" and err.candidates:
        return f"¿Cuál? En la despensa tengo {_join(err.candidates)}."
    if err.code == "not_found":
        return f"{err}."
    return f"No he podido hacerlo: {err}."


# ---------------------------------------------------------------- intents de HA
_ITEM = vol.All(cv.string, vol.Length(min=1, max=120))
_QUANTITY = vol.All(vol.Coerce(int), vol.Range(min=1, max=999))


class _DespensaIntent(intent.IntentHandler):
    """Base: convierte los errores en una respuesta hablada."""

    platforms = None
    response_type = intent.IntentResponseType.ACTION_DONE

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def _run(self, slots: dict[str, Any]) -> str:
        raise NotImplementedError

    async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        slots = self.async_validate_slots(intent_obj.slots)
        values = {key: value.get("value") for key, value in slots.items()}
        response = intent_obj.create_response()
        try:
            speech = await self._run(values)
        except DespensaError as err:
            response.async_set_error(intent.IntentResponseErrorCode.NO_VALID_TARGETS, error_speech(err))
            return response
        response.response_type = self.response_type
        response.async_set_speech(speech)
        return response


class UseItemIntent(_DespensaIntent):
    intent_type = INTENT_USE
    description = (
        "Resta unidades de un producto de la despensa de casa porque se ha usado o consumido "
        "(por ejemplo, «he usado dos latas de atún»)."
    )

    @property
    def slot_schema(self) -> dict:
        return {vol.Required("item"): _ITEM, vol.Optional("quantity"): _QUANTITY}

    async def _run(self, slots: dict[str, Any]) -> str:
        return await async_use(self.hass, slots["item"], slots.get("quantity"))


class EmptyItemIntent(_DespensaIntent):
    intent_type = INTENT_EMPTY
    description = "Marca que un producto de la despensa se ha acabado (stock a cero)."

    @property
    def slot_schema(self) -> dict:
        return {vol.Required("item"): _ITEM}

    async def _run(self, slots: dict[str, Any]) -> str:
        return await async_use(self.hass, slots["item"], empty=True)


class AddItemIntent(_DespensaIntent):
    intent_type = INTENT_ADD
    description = "Suma unidades de un producto a la despensa de casa (o lo añade si no estaba)."

    @property
    def slot_schema(self) -> dict:
        return {vol.Required("item"): _ITEM, vol.Optional("quantity"): _QUANTITY}

    async def _run(self, slots: dict[str, Any]) -> str:
        return await async_add(self.hass, slots["item"], slots.get("quantity"))


class GetStockIntent(_DespensaIntent):
    intent_type = INTENT_STOCK
    description = "Dice cuántas unidades quedan de un producto en la despensa de casa."
    response_type = intent.IntentResponseType.QUERY_ANSWER

    @property
    def slot_schema(self) -> dict:
        return {vol.Required("item"): _ITEM}

    async def _run(self, slots: dict[str, Any]) -> str:
        return await async_stock(self.hass, slots["item"])


class ListLowIntent(_DespensaIntent):
    intent_type = INTENT_LOW
    description = "Dice qué productos de la despensa han llegado a su stock mínimo y hay que reponer."
    response_type = intent.IntentResponseType.QUERY_ANSWER

    async def _run(self, slots: dict[str, Any]) -> str:
        return await async_list_low(self.hass)


class AddLowToCestaIntent(_DespensaIntent):
    intent_type = INTENT_TO_CESTA
    description = "Añade a la lista de la compra (Cesta) todo lo que hay que reponer en la despensa."

    async def _run(self, slots: dict[str, Any]) -> str:
        return await async_low_to_cesta(self.hass)


INTENT_HANDLERS = (
    UseItemIntent, EmptyItemIntent, AddItemIntent, GetStockIntent, ListLowIntent, AddLowToCestaIntent,
)

_TRIGGER_ACTIONS: dict[str, Callable[[HomeAssistant, str], Awaitable[str]]] = {
    INTENT_USE: lambda hass, text: async_use(hass, text),
    INTENT_EMPTY: lambda hass, text: async_use(hass, text, empty=True),
    INTENT_ADD: lambda hass, text: async_add(hass, text),
    INTENT_STOCK: async_stock,
    INTENT_LOW: lambda hass, _text: async_list_low(hass),
    INTENT_TO_CESTA: lambda hass, _text: async_low_to_cesta(hass),
}


@callback
def async_register_intents(hass: HomeAssistant) -> None:
    for handler in INTENT_HANDLERS:
        intent.async_register(hass, handler(hass))


@callback
def async_remove_intents(hass: HomeAssistant) -> None:
    for handler in INTENT_HANDLERS:
        intent.async_remove(hass, handler.intent_type)


# -------------------------------------------------- frases para el agente de Assist
def _register_trigger(hass: HomeAssistant, sentences: list[str], cb: Any) -> Callable[[], None] | None:
    """Registra frases en el agente de Assist (la API cambió en 2025.x; se admiten ambas)."""
    try:
        from homeassistant.components.conversation.agent_manager import get_agent_manager  # noqa: PLC0415
        from homeassistant.components.conversation.trigger import TriggerDetails  # noqa: PLC0415
    except ImportError:
        TriggerDetails = None  # type: ignore[assignment]  # noqa: N806
    if TriggerDetails is not None and hasattr(get_agent_manager(hass), "register_trigger"):
        return get_agent_manager(hass).register_trigger(TriggerDetails(sentences=sentences, callback=cb))
    try:  # Home Assistant 2025.1 – 2025.x
        from homeassistant.components.conversation.const import DATA_DEFAULT_ENTITY  # noqa: PLC0415
    except ImportError:
        return None
    agent = hass.data.get(DATA_DEFAULT_ENTITY)
    if agent is None or not hasattr(agent, "register_trigger"):
        return None
    return agent.register_trigger(sentences, cb)


class VoiceSentences:
    """Activa o desactiva las frases según el ajuste "Frases de voz" del panel."""

    def __init__(self, hass: HomeAssistant, manager: DespensaManager) -> None:
        self.hass = hass
        self.manager = manager
        self._unregister: list[Callable[[], None]] = []
        self._unsubs: list[Callable[[], None]] = []

    @callback
    def async_start(self) -> None:
        self._unsubs.append(self.manager.async_add_listener(self._sync))
        # Si Assist se carga después que Despensa, las frases se registran entonces.
        self._unsubs.append(self.hass.bus.async_listen(EVENT_COMPONENT_LOADED, self._on_loaded))
        self._sync()

    @callback
    def async_stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        self._disable()

    @callback
    def _on_loaded(self, event: Event) -> None:
        if event.data.get("component") == "conversation":
            self._sync()

    @property
    def active(self) -> bool:
        return bool(self._unregister)

    @callback
    def _sync(self) -> None:
        wanted = bool(self.manager.settings.get("voice", True))
        if wanted and not self._unregister:
            self._enable()
        elif not wanted and self._unregister:
            self._disable()

    @callback
    def _enable(self) -> None:
        if "conversation" not in self.hass.config.components:
            _LOGGER.debug("Assist no está cargado: las frases de voz no se registran")
            return
        for intent_type, sentences in SENTENCES.items():
            unregister = _register_trigger(self.hass, sentences, self._make_callback(intent_type))
            if unregister is None:
                _LOGGER.warning(
                    "Esta versión de Home Assistant no permite registrar frases; "
                    "los intents de Despensa siguen disponibles"
                )
                self._disable()
                return
            self._unregister.append(unregister)

    @callback
    def _disable(self) -> None:
        for unregister in self._unregister:
            unregister()
        self._unregister.clear()

    def _make_callback(self, intent_type: str) -> Callable[..., Awaitable[str]]:
        action = _TRIGGER_ACTIONS[intent_type]

        async def handle(user_input: Any, result: Any, *_args: Any) -> str:
            entity = result.entities.get("producto") if result is not None else None
            text = str(entity.value if entity is not None else "").strip()
            try:
                return await action(self.hass, text)
            except DespensaError as err:
                return error_speech(err)

        return handle
