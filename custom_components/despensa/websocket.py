"""API websocket de Despensa (la usan el panel y la tarjeta)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .catalog import CATALOG
from .const import DOMAIN, KIND_EMPTY, MAX_STOCK
from .manager import DespensaError, DespensaManager

DATA_BRIDGE = f"{DOMAIN}_bridge"
DATA_VOICE = f"{DOMAIN}_voice"

_STOCK = vol.All(vol.Coerce(int), vol.Range(min=0, max=MAX_STOCK))
_MIN = vol.Any(None, vol.All(vol.Coerce(int), vol.Range(min=0, max=999)))
_PACK = vol.All(vol.Coerce(int), vol.Range(min=1, max=999))
_ICON = vol.All(str, vol.Length(max=16))
_UNIT = vol.All(str, vol.Length(max=20))


def _manager(hass: HomeAssistant) -> DespensaManager | None:
    return hass.data.get(DOMAIN)


def _with_manager(
    func: Callable[[HomeAssistant, websocket_api.ActiveConnection, dict[str, Any], DespensaManager], None],
) -> Callable[[HomeAssistant, websocket_api.ActiveConnection, dict[str, Any]], None]:
    """Inyecta el gestor y convierte los errores en respuestas websocket."""

    @wraps(func)
    def wrapper(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
        manager = _manager(hass)
        if manager is None:
            connection.send_error(msg["id"], "not_loaded", "Despensa no está configurada")
            return
        try:
            func(hass, connection, msg, manager)
        except DespensaError as err:
            connection.send_error(msg["id"], err.code, str(err))

    return wrapper


def _with_manager_async(
    func: Callable[[HomeAssistant, websocket_api.ActiveConnection, dict[str, Any], DespensaManager], Awaitable[None]],
) -> Callable[[HomeAssistant, websocket_api.ActiveConnection, dict[str, Any]], Awaitable[None]]:
    @wraps(func)
    async def wrapper(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
        manager = _manager(hass)
        if manager is None:
            connection.send_error(msg["id"], "not_loaded", "Despensa no está configurada")
            return
        try:
            await func(hass, connection, msg, manager)
        except DespensaError as err:
            connection.send_error(msg["id"], err.code, str(err))

    return wrapper


@callback
def async_register_websocket_api(hass: HomeAssistant) -> None:
    for command in (
        ws_subscribe,
        ws_catalog,
        ws_create,
        ws_adjust,
        ws_update,
        ws_empty,
        ws_delete,
        ws_restore,
        ws_undo,
        ws_log_clear,
        ws_cesta_add,
        ws_cesta_add_low,
        ws_settings,
        ws_unignore,
    ):
        websocket_api.async_register_command(hass, command)


def _item_result(manager: DespensaManager, item: dict[str, Any], entry: dict[str, Any] | None) -> dict[str, Any]:
    return {"item": item, "log": entry, "low": manager.is_low(item)}


@websocket_api.websocket_command({vol.Required("type"): "despensa/subscribe"})
@callback
@_with_manager
def ws_subscribe(hass, connection, msg, manager: DespensaManager) -> None:
    """Envía el estado completo ahora y cada vez que cambie."""
    msg_id = msg["id"]

    @callback
    def forward() -> None:
        state = manager.snapshot()
        voice = hass.data.get(DATA_VOICE)
        state["voice_active"] = bool(voice and voice.active)
        connection.send_message(websocket_api.event_message(msg_id, state))

    connection.subscriptions[msg_id] = manager.async_add_listener(forward)
    connection.send_result(msg_id)
    forward()


@websocket_api.websocket_command({vol.Required("type"): "despensa/catalog"})
@callback
def ws_catalog(hass, connection, msg) -> None:
    connection.send_result(msg["id"], {"catalog": CATALOG})


@websocket_api.websocket_command(
    {
        vol.Required("type"): "despensa/item/create",
        vol.Required("name"): vol.All(str, vol.Length(min=1, max=120)),
        vol.Optional("stock"): _STOCK,
        vol.Optional("icon"): _ICON,
        vol.Optional("department"): str,
        vol.Optional("min_stock"): _MIN,
        vol.Optional("unit"): _UNIT,
        vol.Optional("pack"): _PACK,
    }
)
@callback
@_with_manager
def ws_create(hass, connection, msg, manager: DespensaManager) -> None:
    extra = {"min_stock": msg["min_stock"]} if "min_stock" in msg else {}
    item, entry = manager.create_item(
        msg["name"],
        stock=msg.get("stock"),
        icon=msg.get("icon"),
        department=msg.get("department"),
        unit=msg.get("unit"),
        pack=msg.get("pack"),
        **extra,
    )
    connection.send_result(msg["id"], _item_result(manager, item, entry))


@websocket_api.websocket_command(
    {
        vol.Required("type"): "despensa/item/adjust",
        vol.Required("item_id"): str,
        vol.Required("delta"): vol.All(vol.Coerce(int), vol.Range(min=-MAX_STOCK, max=MAX_STOCK)),
    }
)
@callback
@_with_manager
def ws_adjust(hass, connection, msg, manager: DespensaManager) -> None:
    entry = manager.adjust(msg["item_id"], msg["delta"])
    connection.send_result(msg["id"], _item_result(manager, manager.get_item(msg["item_id"]), entry))


@websocket_api.websocket_command(
    {
        vol.Required("type"): "despensa/item/update",
        vol.Required("item_id"): str,
        vol.Optional("name"): vol.All(str, vol.Length(min=1, max=120)),
        vol.Optional("icon"): _ICON,
        vol.Optional("department"): str,
        vol.Optional("min_stock"): _MIN,
        vol.Optional("unit"): _UNIT,
        vol.Optional("pack"): _PACK,
        vol.Optional("stock"): _STOCK,
    }
)
@callback
@_with_manager
def ws_update(hass, connection, msg, manager: DespensaManager) -> None:
    fields = ("name", "icon", "department", "min_stock", "unit", "pack", "stock")
    changes = {k: msg[k] for k in fields if k in msg}
    item = manager.update_item(msg["item_id"], **changes)
    connection.send_result(msg["id"], _item_result(manager, item, None))


@websocket_api.websocket_command({vol.Required("type"): "despensa/item/empty", vol.Required("item_id"): str})
@callback
@_with_manager
def ws_empty(hass, connection, msg, manager: DespensaManager) -> None:
    entry = manager.set_stock(msg["item_id"], 0, kind=KIND_EMPTY)
    connection.send_result(msg["id"], _item_result(manager, manager.get_item(msg["item_id"]), entry))


@websocket_api.websocket_command(
    {
        vol.Required("type"): "despensa/item/delete",
        vol.Required("item_id"): str,
        vol.Optional("ignore", default=False): bool,
    }
)
@callback
@_with_manager
def ws_delete(hass, connection, msg, manager: DespensaManager) -> None:
    connection.send_result(msg["id"], manager.delete_item(msg["item_id"], ignore=msg["ignore"]))


@websocket_api.websocket_command({vol.Required("type"): "despensa/item/restore", vol.Required("item_id"): str})
@callback
@_with_manager
def ws_restore(hass, connection, msg, manager: DespensaManager) -> None:
    connection.send_result(msg["id"], manager.restore_deleted(msg["item_id"]))


@websocket_api.websocket_command({vol.Required("type"): "despensa/log/undo", vol.Required("log_id"): str})
@callback
@_with_manager
def ws_undo(hass, connection, msg, manager: DespensaManager) -> None:
    connection.send_result(msg["id"], manager.undo(msg["log_id"]))


@websocket_api.websocket_command({vol.Required("type"): "despensa/log/clear"})
@callback
@_with_manager
def ws_log_clear(hass, connection, msg, manager: DespensaManager) -> None:
    manager.clear_log()
    connection.send_result(msg["id"])


def _bridge(hass: HomeAssistant):
    bridge = hass.data.get(DATA_BRIDGE)
    if bridge is None or not bridge.available:
        raise DespensaError("no_cesta", "Cesta no está instalada o no está configurada")
    return bridge


@websocket_api.websocket_command({vol.Required("type"): "despensa/cesta/add", vol.Required("item_id"): str})
@websocket_api.async_response
@_with_manager_async
async def ws_cesta_add(hass, connection, msg, manager: DespensaManager) -> None:
    added = await _bridge(hass).async_add(manager.get_item(msg["item_id"]))
    connection.send_result(msg["id"], {"added": added})


@websocket_api.websocket_command({vol.Required("type"): "despensa/cesta/add_low"})
@websocket_api.async_response
@_with_manager_async
async def ws_cesta_add_low(hass, connection, msg, manager: DespensaManager) -> None:
    added = await _bridge(hass).async_add_low()
    connection.send_result(msg["id"], {"added": added})


@websocket_api.websocket_command(
    {
        vol.Required("type"): "despensa/settings/set",
        vol.Optional("default_min"): _MIN,
        vol.Optional("add_from_cesta"): bool,
        vol.Optional("auto_cesta"): bool,
        vol.Optional("voice"): bool,
    }
)
@callback
@_with_manager
def ws_settings(hass, connection, msg, manager: DespensaManager) -> None:
    manager.set_settings(**{k: v for k, v in msg.items() if k not in ("type", "id")})
    connection.send_result(msg["id"])


@websocket_api.websocket_command({vol.Required("type"): "despensa/ignored/remove", vol.Required("name"): str})
@callback
@_with_manager
def ws_unignore(hass, connection, msg, manager: DespensaManager) -> None:
    manager.unignore(msg["name"])
    connection.send_result(msg["id"])
