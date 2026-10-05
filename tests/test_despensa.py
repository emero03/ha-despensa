"""Tests de la integración Despensa."""

from __future__ import annotations

from datetime import timedelta
import logging

from hassil import Intents, recognize_all
from hassil.intents import TextSlotList, WildcardSlotList
from hassil.sample import sample_intents
from home_assistant_intents import get_intents
import pytest

from homeassistant import config_entries
from homeassistant.components import frontend
from homeassistant.components.conversation import async_converse
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import Context, HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import intent, llm
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_capture_events,
    async_fire_time_changed,
)

from custom_components.despensa.catalog import CATALOG
from custom_components.despensa.const import DEFAULT_DEPARTMENTS, DOMAIN, EVENT_LOW_STOCK
from custom_components.despensa.manager import DespensaError, quantity_from_note
from custom_components.despensa.voice import SENTENCES, parse_spoken

from .conftest import HAS_CESTA

SENSOR = "sensor.despensa_por_reponer"
needs_cesta = pytest.mark.skipif(not HAS_CESTA, reason="Cesta no está disponible (define CESTA_REPO)")


def _manager(hass: HomeAssistant):
    return hass.data[DOMAIN]


def _cesta(hass: HomeAssistant):
    return hass.data["cesta"]


async def _say(hass: HomeAssistant, text: str) -> str:
    result = await async_converse(hass, text, None, Context(), language="es")
    return result.response.speech["plain"]["speech"]


# ----------------------------------------------------------- piezas sueltas
def test_catalog_matches_departments() -> None:
    dept_ids = {d["id"] for d in DEFAULT_DEPARTMENTS}
    assert all(e["department"] in dept_ids for e in CATALOG)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("dos latas de atún", (2, False, ["latas de atún", "atún"])),
        ("una lata de atún de la despensa", (1, False, ["lata de atún", "atún"])),
        ("el último yogur", (None, False, ["yogur"])),
        ("la leche", (None, False, ["leche"])),
        ("3 bricks de leche", (3, False, ["bricks de leche", "leche"])),
        ("media docena de huevos", (6, False, ["huevos"])),
        ("una docena de huevos", (12, False, ["huevos"])),
        ("un par de cápsulas de café", (2, False, ["cápsulas de café", "café"])),
        ("todo el arroz", (None, True, ["arroz"])),
        ("un poco de aceite de oliva", (1, False, ["aceite de oliva"])),
        ("bolsas de basura", (None, False, ["bolsas de basura", "basura"])),
        ("Pan de molde", (None, False, ["Pan de molde"])),
        ("", (None, False, [])),
    ],
)
def test_parse_spoken(text: str, expected) -> None:
    assert parse_spoken(text) == expected


@pytest.mark.parametrize(
    ("note", "expected"),
    [("6", 6), ("x6", 6), ("6 uds", 6), ("pack de 4", 4), ("12 latas", 12), ("docena", 12),
     ("2 L", None), ("1 kg", None), ("sin lactosa", None), ("", None), (None, None), ("0", None)],
)
def test_quantity_from_note(note, expected) -> None:
    assert quantity_from_note(note) == expected


# -------------------------------------------------------------- alta / baja
async def test_config_flow(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_setup_and_unload(hass: HomeAssistant, setup_despensa: MockConfigEntry, hass_client) -> None:
    panel = hass.data[frontend.DATA_PANELS]["despensa"]
    assert panel.sidebar_title == "Despensa"
    assert panel.sidebar_icon == "mdi:cupboard-outline"
    module_url = panel.config["_panel_custom"]["module_url"]
    assert module_url.startswith("/despensa_static/despensa.js?v=")
    assert module_url in hass.data[frontend.DATA_EXTRA_MODULE_URL].urls

    client = await hass_client()
    resp = await client.get("/despensa_static/despensa.js")
    assert resp.status == 200

    assert hass.states.get(SENSOR).state == "0"
    assert "DespensaUseItem" in {h.intent_type for h in intent.async_get(hass)}
    # Sin Cesta, las baldas son las de serie
    assert _manager(hass).snapshot()["cesta"]["available"] is False

    assert await hass.config_entries.async_unload(setup_despensa.entry_id)
    await hass.async_block_till_done()
    assert setup_despensa.state is ConfigEntryState.NOT_LOADED
    assert "despensa" not in hass.data[frontend.DATA_PANELS]
    assert "DespensaUseItem" not in {h.intent_type for h in intent.async_get(hass)}

    assert await hass.config_entries.async_setup(setup_despensa.entry_id)
    await hass.async_block_till_done()
    assert "despensa" in hass.data[frontend.DATA_PANELS]


# ------------------------------------------------------------------ gestor
async def test_stock_minimum_and_low_event(hass: HomeAssistant, setup_despensa: MockConfigEntry) -> None:
    manager = _manager(hass)
    events = async_capture_events(hass, EVENT_LOW_STOCK)

    leche, entry = manager.create_item("leche", stock=4, min_stock=2, unit="bricks")
    assert (leche["name"], leche["icon"], leche["department"], leche["stock"]) == ("Leche", "🥛", "lacteos", 4)
    assert entry["created"] and entry["delta"] == 4
    assert not manager.is_low(leche)

    manager.adjust(leche["id"], -1)
    assert leche["stock"] == 3 and not manager.is_low(leche)
    manager.adjust(leche["id"], -1)  # llega al mínimo: aviso
    await hass.async_block_till_done()
    assert manager.is_low(leche)
    assert len(events) == 1
    assert events[0].data["name"] == "Leche" and events[0].data["stock"] == 2
    manager.adjust(leche["id"], -5)  # ya estaba por reponer: no se repite el aviso; no baja de 0
    await hass.async_block_till_done()
    assert leche["stock"] == 0 and len(events) == 1

    state = hass.states.get(SENSOR)
    assert state.state == "1"
    assert state.attributes["productos"] == ["Leche"]
    assert state.attributes["detalle"][0]["unit"] == "bricks"
    assert state.attributes["agotados"] == 1

    # Mínimo por defecto para productos nuevos: 0 (avisa al acabarse)
    arroz, _ = manager.create_item("arroz", stock=1)
    assert arroz["min_stock"] == 0
    manager.set_settings(default_min=None)
    sal, _ = manager.create_item("sal")
    assert sal["min_stock"] is None and sal["stock"] == 1
    manager.adjust(sal["id"], -1)
    assert not manager.is_low(sal)  # sin aviso

    # Añadir algo que ya existe suma
    item, entry = manager.create_item("Arroz", stock=2)
    assert item is arroz and arroz["stock"] == 3 and not entry["created"]


async def test_log_merge_and_undo(hass: HomeAssistant, setup_despensa: MockConfigEntry) -> None:
    manager = _manager(hass)
    cafe, created = manager.create_item("café", stock=1)
    e1 = manager.adjust(cafe["id"], 1)
    e2 = manager.adjust(cafe["id"], 1)
    assert e1["id"] == e2["id"] and e2["delta"] == 2  # pulsaciones seguidas: un movimiento
    assert cafe["stock"] == 3
    manager.undo(e2["id"])
    assert cafe["stock"] == 1
    # Deshacer la creación quita el producto
    manager.undo(created["id"])
    assert manager.find_by_name("café") is None
    with pytest.raises(DespensaError):
        manager.undo("nada")


async def test_find(hass: HomeAssistant, setup_despensa: MockConfigEntry) -> None:
    manager = _manager(hass)
    manager.create_item("Atún en lata", stock=3)
    manager.create_item("Yogures", stock=4)
    manager.create_item("Leche", stock=1)
    manager.create_item("Leche sin lactosa", stock=1)
    assert manager.find("atun")["name"] == "Atún en lata"
    assert manager.find("yogur")["name"] == "Yogures"
    assert manager.find("LECHE")["name"] == "Leche"
    assert manager.find("leche entera")["name"] == "Leche"
    manager.create_item("Atún fresco", stock=0)
    assert manager.find("atún")["name"] == "Atún en lata"  # el que hay en casa
    manager.adjust(manager.find("atún fresco")["id"], 1)
    with pytest.raises(DespensaError) as err:
        manager.find("atún")
    assert err.value.code == "ambiguous"
    assert err.value.candidates == ["Atún en lata", "Atún fresco"]
    with pytest.raises(DespensaError) as err:
        manager.find("caviar")
    assert err.value.code == "not_found"


async def test_delete_restore_and_ignore(hass: HomeAssistant, setup_despensa: MockConfigEntry) -> None:
    manager = _manager(hass)
    flores, _ = manager.create_item("Flores", stock=1)
    manager.delete_item(flores["id"], ignore=True)
    assert manager.items == []
    assert manager.snapshot()["ignored"] == ["Flores"]
    manager.restore_deleted(flores["id"])
    assert manager.items[0]["name"] == "Flores"
    assert manager.snapshot()["ignored"] == []
    manager.delete_item(flores["id"], ignore=True)
    assert manager.apply_purchase({"name": "Flores", "kind": "purchased"}) is None
    manager.unignore("flores")
    assert manager.apply_purchase({"name": "Flores", "kind": "purchased"}) is not None


# --------------------------------------------------------------- websocket
async def test_websocket_flow(hass: HomeAssistant, setup_despensa: MockConfigEntry, hass_ws_client) -> None:
    client = await hass_ws_client(hass)

    await client.send_json_auto_id({"type": "despensa/catalog"})
    msg = await client.receive_json()
    assert any(e["name"] == "Leche" for e in msg["result"]["catalog"])

    await client.send_json_auto_id({"type": "despensa/subscribe"})
    assert (await client.receive_json())["success"]
    state = (await client.receive_json())["event"]
    assert state["items"] == [] and len(state["departments"]) == 14
    assert state["settings"]["default_min"] == 0

    async def call(payload):
        await client.send_json_auto_id(payload)
        while True:
            msg = await client.receive_json()
            if msg["type"] == "result":
                return msg

    msg = await call({"type": "despensa/item/create", "name": "huevos", "stock": 12, "min_stock": 4})
    huevos = msg["result"]["item"]
    assert (huevos["name"], huevos["icon"], huevos["stock"], huevos["min_stock"]) == ("Huevos", "🥚", 12, 4)

    msg = await call({"type": "despensa/item/adjust", "item_id": huevos["id"], "delta": -8})
    assert msg["result"]["item"]["stock"] == 4 and msg["result"]["low"] is True
    log_id = msg["result"]["log"]["id"]

    msg = await call({"type": "despensa/item/update", "item_id": huevos["id"], "min_stock": None, "unit": "uds", "pack": 12})
    assert msg["result"]["low"] is False and msg["result"]["item"]["pack"] == 12

    msg = await call({"type": "despensa/log/undo", "log_id": log_id})
    assert msg["result"]["stock"] == 12

    msg = await call({"type": "despensa/item/empty", "item_id": huevos["id"]})
    assert msg["result"]["item"]["stock"] == 0 and msg["result"]["log"]["kind"] == "empty"

    msg = await call({"type": "despensa/item/delete", "item_id": huevos["id"]})
    assert msg["success"] and _manager(hass).items == []
    msg = await call({"type": "despensa/item/restore", "item_id": huevos["id"]})
    assert msg["success"] and len(_manager(hass).items) == 1

    msg = await call({"type": "despensa/settings/set", "auto_cesta": True, "default_min": 1})
    assert _manager(hass).settings["auto_cesta"] is True and _manager(hass).settings["default_min"] == 1

    msg = await call({"type": "despensa/cesta/add", "item_id": huevos["id"]})
    assert msg["success"] is False and msg["error"]["code"] == "no_cesta"

    msg = await call({"type": "despensa/item/adjust", "item_id": "nada", "delta": 1})
    assert msg["error"]["code"] == "not_found"


# ------------------------------------------------------------------ acciones
async def test_services(hass: HomeAssistant, setup_despensa: MockConfigEntry) -> None:
    res = await hass.services.async_call(
        DOMAIN, "add_item", {"name": "tomate frito", "quantity": 6, "min_stock": 2, "unit": "botes"},
        blocking=True, return_response=True,
    )
    assert (res["name"], res["icon"], res["stock"], res["min_stock"], res["unit"]) == ("Tomate frito", "🥫", 6, 2, "botes")

    res = await hass.services.async_call(
        DOMAIN, "use_item", {"name": "TOMATE FRITO", "quantity": 4}, blocking=True, return_response=True
    )
    assert res["stock"] == 2 and res["low"] is True
    assert res["text"] == "Te quedan 2 botes de tomate frito."

    # La unidad no se repite: "Atún en lata" contado en latas
    res = await hass.services.async_call(
        DOMAIN, "add_item", {"name": "Atún en lata", "quantity": 4, "unit": "latas"}, blocking=True, return_response=True
    )
    assert res["text"] == "Te quedan 4 latas de atún."
    res = await hass.services.async_call(
        DOMAIN, "add_item", {"name": "Latas de cerveza", "quantity": 1, "unit": "latas"}, blocking=True, return_response=True
    )
    assert res["text"] == "Te queda 1 lata de cerveza."

    res = await hass.services.async_call(
        DOMAIN, "set_stock", {"name": "Tomate frito", "stock": 9, "min_stock": 3}, blocking=True, return_response=True
    )
    assert res["stock"] == 9 and res["min_stock"] == 3

    await hass.services.async_call(DOMAIN, "add_item", {"name": "Lejía", "quantity": 1, "min_stock": 1}, blocking=True)
    res = await hass.services.async_call(DOMAIN, "get_items", {"low_only": True}, blocking=True, return_response=True)
    assert res["count"] == 1 and res["items"][0]["name"] == "Lejía"
    assert res["items"][0]["department"] == "Limpieza y hogar"
    assert "⚠️" in res["text"]

    res = await hass.services.async_call(
        DOMAIN, "get_items", {"department": "Limpieza y hogar"}, blocking=True, return_response=True
    )
    assert [i["name"] for i in res["items"]] == ["Lejía"]

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(DOMAIN, "use_item", {"name": "caviar"}, blocking=True)
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(DOMAIN, "add_low_to_cesta", {}, blocking=True)


# ----------------------------------------------------------------------- voz
@pytest.fixture
async def with_assist(hass: HomeAssistant, setup_despensa: MockConfigEntry) -> MockConfigEntry:
    assert await async_setup_component(hass, "homeassistant", {})
    assert await async_setup_component(hass, "conversation", {})
    assert await async_setup_component(hass, "intent", {})
    await hass.async_block_till_done()
    # Assist se carga después que Despensa en este test: las frases se registran al cargar
    assert hass.data["despensa_voice"].active
    manager = _manager(hass)
    manager.create_item("Atún en lata", stock=6, min_stock=2)
    manager.create_item("Leche", stock=3, min_stock=1, unit="bricks")
    manager.create_item("Arroz", stock=2, min_stock=1)
    manager.create_item("Yogures", stock=4)
    return setup_despensa


async def test_voice_sentences(hass: HomeAssistant, with_assist) -> None:
    manager = _manager(hass)
    assert await _say(hass, "He usado dos latas de atún") == "Hecho. De atún en lata te quedan 4."
    assert await _say(hass, "Hemos gastado un yogur") == "Hecho. De yogures te quedan 3."
    assert await _say(hass, "¿Cuánta leche queda?") == "Te quedan 3 bricks de leche."
    assert await _say(hass, "He consumido 2 bricks de leche") == "Hecho. Te queda 1 brick de leche. Ya estás en el mínimo."
    assert await _say(hass, "Se ha acabado el arroz") == "Apuntado: no queda nada de arroz."
    assert await _say(hass, "qué falta en la despensa") == "Hay que reponer leche y arroz."
    assert await _say(hass, "He comprado tres paquetes de arroz") == "Hecho. De arroz te quedan 3."
    assert await _say(hass, "He comprado garbanzos") == "He añadido garbanzos a la despensa. De garbanzos te queda 1."
    assert manager.find("garbanzos")["icon"] == "🫘"
    assert await _say(hass, "He usado caviar") == "«Caviar» no está en la despensa."
    assert await _say(hass, "he gastado todo el atún") == "Apuntado: no queda nada de atún en lata."
    assert await _say(hass, "Añade lo que falta a la cesta") == "No he podido hacerlo: Cesta no está instalada."

    log = manager.log
    assert log[0]["source"] == "voz" and log[0]["kind"] == "empty"

    # Lo que no es de la despensa sigue llegando a Home Assistant
    assert "despensa" not in (await _say(hass, "enciende la luz de la cocina")).lower()

    # Se pueden desactivar las frases desde los ajustes
    manager.set_settings(voice=False)
    assert not hass.data["despensa_voice"].active
    assert "Hecho" not in await _say(hass, "He usado leche")
    manager.set_settings(voice=True)
    assert hass.data["despensa_voice"].active


async def test_intents_for_alexa_and_llm(hass: HomeAssistant, with_assist) -> None:
    """Los intents se pueden llamar sin frases (skill de Alexa, agentes con IA)."""
    response = await intent.async_handle(
        hass, "alexa", "DespensaUseItem", {"item": {"value": "leche"}, "quantity": {"value": 2}}
    )
    assert response.speech["plain"]["speech"] == "Hecho. Te queda 1 brick de leche. Ya estás en el mínimo."

    response = await intent.async_handle(hass, "alexa", "DespensaGetStock", {"item": {"value": "nada"}})
    assert response.response_type is intent.IntentResponseType.ERROR

    response = await intent.async_handle(hass, "alexa", "DespensaListLow", {})
    assert response.speech["plain"]["speech"] == "Hay que reponer leche."

    api = await llm.async_get_api(
        hass,
        "assist",
        llm.LLMContext(platform="test", context=Context(), language="es", assistant="conversation", device_id=None),
    )
    tool_names = {tool.name for tool in api.tools}
    assert {"DespensaUseItem", "DespensaGetStock", "DespensaListLow"} <= tool_names


def _trigger_intents() -> Intents:
    mine = Intents.from_dict(
        {"language": "es", "intents": {k: {"data": [{"sentences": v}]} for k, v in SENTENCES.items()}}
    )
    mine.slot_lists["producto"] = WildcardSlotList("producto")
    return mine


@pytest.mark.parametrize(
    ("sentence", "intent_name", "product"),
    [
        ("He usado dos latas de atún", "DespensaUseItem", "latas de atún"),
        ("Hemos gastado un yogur", "DespensaUseItem", "yogur"),
        ("Apunta que he cogido el último huevo", "DespensaUseItem", "huevo"),
        ("He gastado todo el arroz", "DespensaUseItem", "arroz"),
        ("Se ha acabado la leche", "DespensaEmptyItem", "leche"),
        ("La leche se ha acabado", "DespensaEmptyItem", "leche"),
        ("He terminado el café", "DespensaEmptyItem", "café"),
        ("He comprado tres paquetes de pasta", "DespensaAddItem", "paquetes de pasta"),
        ("Añade garbanzos a la despensa", "DespensaAddItem", "garbanzos"),
        ("¿Cuánto arroz queda?", "DespensaGetStock", "arroz"),
        ("¿Cuántos huevos nos quedan?", "DespensaGetStock", "huevos"),
        ("¿Nos quedan huevos?", "DespensaGetStock", "huevos"),
        ("¿Hay atún en la despensa?", "DespensaGetStock", "atún"),
        ("¿Cuánta leche me queda en casa?", "DespensaGetStock", "leche"),
        ("¿Qué falta?", "DespensaListLow", None),
        ("¿Qué hay que comprar?", "DespensaListLow", None),
        ("¿Qué se está acabando?", "DespensaListLow", None),
        ("Añade lo que falta a la cesta", "DespensaAddLowToCesta", None),
        ("Pon en la lista de la compra todo lo que falta", "DespensaAddLowToCesta", None),
    ],
)
def test_sentences(sentence: str, intent_name: str, product: str | None) -> None:
    results = list(recognize_all(sentence, _trigger_intents()))
    assert {r.intent.name for r in results} == {intent_name}
    if product is not None:
        _quantity, _all, candidates = parse_spoken(results[0].entities["producto"].value)
        assert candidates[0] == product


def test_sentences_do_not_capture_home_assistant_commands() -> None:
    """Ninguna frase de Assist en español (encender luces, temporizadores...) cae en Despensa."""
    logging.getLogger("hassil").setLevel(logging.ERROR)
    mine = _trigger_intents()
    builtin = Intents.from_dict(get_intents("es"))
    lists = dict(builtin.slot_lists)
    for name, values in {"name": ["la luz del salón"], "area": ["la cocina"], "floor": ["la planta baja"]}.items():
        lists[name] = TextSlotList.from_strings(values)
    checked = 0
    for intent_name in builtin.intents:
        for _name, sentence in sample_intents(
            builtin, slot_lists=lists, max_sentences_per_intent=400, intent_names={intent_name},
            exclude_sentences_with_wildcards=False, expand_ranges=False, language="es",
        ):
            checked += 1
            assert next(iter(recognize_all(sentence, mine)), None) is None, sentence
    assert checked > 5000


# --------------------------------------------------------------------- Cesta
@needs_cesta
async def test_cesta_purchase_adds_and_undo_reverts(hass: HomeAssistant, setup_both, freezer) -> None:
    cesta, despensa = _cesta(hass), _manager(hass)
    assert despensa.snapshot()["cesta"]["available"] is True

    # Comprar algo nuevo lo crea en su balda con el icono de Cesta
    leche = cesta.add_item("leche")
    assert despensa.snapshot()["cesta"]["in_list"] == ["leche"]
    cesta.purchase_item(leche["id"])
    item = despensa.find_by_name("leche")
    assert (item["stock"], item["icon"], item["department"]) == (1, "🥛", "lacteos")
    assert despensa.log[0]["source"] == "cesta" and despensa.log[0]["kind"] == "purchased"
    assert despensa.snapshot()["cesta"]["in_list"] == []

    # Unidades por compra del producto, o las del detalle si es un número
    despensa.update_item(item["id"], pack=6)
    freezer.tick(1)
    cesta.purchase_item(cesta.add_item("leche")["id"])
    assert item["stock"] == 7
    freezer.tick(1)
    cesta.purchase_item(cesta.add_item("leche", note="2 uds")["id"])
    assert item["stock"] == 9

    # Deshacer en Cesta resta
    entry = cesta.recent[0]
    cesta.restore_recent(entry["id"], undo=True)
    assert item["stock"] == 7
    # Volver a añadirla a la lista (sin deshacer) no resta: sí se compró
    freezer.tick(1)
    cesta.purchase_item(cesta.find_by_name("leche")["id"])
    assert item["stock"] == 9  # vuelve a la lista con su detalle "2 uds"
    cesta.restore_recent(cesta.recent[0]["id"])
    assert item["stock"] == 9

    # Deshacer la compra que creó el producto lo quita de la despensa
    pan = cesta.add_item("pan")
    cesta.purchase_item(pan["id"])
    assert despensa.find_by_name("pan")["stock"] == 1
    cesta.restore_recent(pan["id"], undo=True)
    assert despensa.find_by_name("pan") is None

    # También funciona marcando en la lista de tareas todo.cesta (o por voz con Assist)
    cesta.add_item("café")
    await hass.services.async_call(
        "todo", "update_item", {"entity_id": "todo.cesta", "item": "Café", "status": "completed"}, blocking=True
    )
    assert despensa.find_by_name("café")["stock"] == 1


@needs_cesta
async def test_cesta_settings_and_departments(hass: HomeAssistant, setup_both) -> None:
    cesta, despensa = _cesta(hass), _manager(hass)

    # Sin "añadir productos nuevos": solo suma a lo que ya está en la despensa
    despensa.set_settings(add_from_cesta=False)
    cesta.purchase_item(cesta.add_item("flores")["id"])
    assert despensa.find_by_name("flores") is None
    despensa.create_item("Agua", stock=0)
    cesta.purchase_item(cesta.add_item("agua")["id"])
    assert despensa.find_by_name("agua")["stock"] == 1

    # Las baldas siguen los colores y el orden de Cesta
    departments = [dict(d) for d in cesta.data["departments"]]
    departments[0]["color"] = "#123456"
    departments.reverse()
    cesta.set_departments(departments)
    snapshot = despensa.snapshot()
    assert snapshot["departments"][0]["id"] == "otros"
    assert snapshot["departments"][-1]["color"] == "#123456"


@needs_cesta
async def test_add_to_cesta(hass: HomeAssistant, setup_both, hass_ws_client) -> None:
    cesta, despensa = _cesta(hass), _manager(hass)
    client = await hass_ws_client(hass)
    cafe, _ = despensa.create_item("Café", stock=1, min_stock=1)
    arroz, _ = despensa.create_item("Arroz", stock=0, min_stock=0)
    despensa.create_item("Sal", stock=3, min_stock=1)

    await client.send_json_auto_id({"type": "despensa/cesta/add", "item_id": cafe["id"]})
    msg = await client.receive_json()
    assert msg["result"] == {"added": True}
    assert [i["name"] for i in cesta.items] == ["Café"]
    assert cesta.items[0]["department"] == "desayuno"
    assert despensa.snapshot()["cesta"]["in_list"] == ["cafe"]

    await client.send_json_auto_id({"type": "despensa/cesta/add_low"})
    msg = await client.receive_json()
    assert msg["result"] == {"added": ["Arroz"]}  # el café ya estaba

    res = await hass.services.async_call(DOMAIN, "add_low_to_cesta", {}, blocking=True, return_response=True)
    assert res == {"count": 0, "added": []}

    # Automático al llegar al mínimo
    despensa.set_settings(auto_cesta=True)
    sal = despensa.find_by_name("sal")
    despensa.adjust(sal["id"], -2)
    await hass.async_block_till_done()
    assert cesta.find_by_name("sal") is not None


@needs_cesta
async def test_cesta_voice(hass: HomeAssistant, setup_both) -> None:
    assert await async_setup_component(hass, "homeassistant", {})
    assert await async_setup_component(hass, "conversation", {})
    await hass.async_block_till_done()
    cesta, despensa = _cesta(hass), _manager(hass)
    despensa.create_item("Café", stock=1, min_stock=0)
    despensa.create_item("Arroz", stock=0, min_stock=0)
    despensa.set_settings(auto_cesta=True)
    assert await _say(hass, "He usado el café") == "Hecho. No queda nada de café. Lo añado a la Cesta."
    await hass.async_block_till_done()
    assert await _say(hass, "Añade lo que falta a la cesta") == "He añadido 1 producto a la Cesta: arroz."
    assert sorted(i["name"] for i in cesta.items) == ["Arroz", "Café"]
    assert await _say(hass, "¿Qué falta?") == "Hay que reponer arroz y café. Ya está todo en la Cesta."


@needs_cesta
async def test_old_purchases_are_not_imported_and_reload(hass: HomeAssistant, freezer) -> None:
    """Lo comprado antes de instalar Despensa no cuenta; si Cesta se recarga, se vuelve a enganchar."""
    hass.config.language = "es"
    assert await async_setup_component(hass, "http", {})
    cesta_entry = MockConfigEntry(domain="cesta", title="Cesta", data={})
    cesta_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(cesta_entry.entry_id)
    cesta = _cesta(hass)
    cesta.purchase_item(cesta.add_item("leche")["id"])

    freezer.tick(5)
    entry = MockConfigEntry(domain=DOMAIN, title="Despensa", data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    despensa = _manager(hass)
    assert despensa.items == []

    assert await hass.config_entries.async_reload(cesta_entry.entry_id)
    await hass.async_block_till_done()
    freezer.tick(1)
    new_cesta = _cesta(hass)
    assert new_cesta is not cesta
    new_cesta.purchase_item(new_cesta.add_item("pan")["id"])
    # Aún no se ha enganchado a la nueva Cesta, pero al hacerlo recupera la compra
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=31))
    await hass.async_block_till_done()
    assert despensa.find_by_name("pan")["stock"] == 1
    assert despensa.find_by_name("leche") is None
