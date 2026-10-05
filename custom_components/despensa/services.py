"""Acciones de Despensa para automatizaciones, scripts y botones (NFC, mandos...)."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse, callback
from homeassistant.exceptions import ServiceValidationError
import homeassistant.helpers.config_validation as cv

from .catalog import normalize
from .const import (
    ATTR_DEPARTMENT,
    ATTR_ICON,
    ATTR_LOW_ONLY,
    ATTR_MIN_STOCK,
    ATTR_NAME,
    ATTR_QUANTITY,
    ATTR_STOCK,
    ATTR_UNIT,
    DOMAIN,
    KIND_EMPTY,
    KIND_USED,
    MAX_STOCK,
    SERVICE_ADD_ITEM,
    SERVICE_ADD_LOW_TO_CESTA,
    SERVICE_GET_ITEMS,
    SERVICE_SET_STOCK,
    SERVICE_USE_ITEM,
    SOURCE_SERVICE,
)
from .manager import UNSET, DespensaError, DespensaManager
from .voice import describe_stock

_QTY = vol.All(vol.Coerce(int), vol.Range(min=1, max=MAX_STOCK))
_STOCK = vol.All(vol.Coerce(int), vol.Range(min=0, max=MAX_STOCK))
_MIN = vol.Any(None, vol.All(vol.Coerce(int), vol.Range(min=0, max=999)))

USE_ITEM_SCHEMA = vol.Schema({vol.Required(ATTR_NAME): cv.string, vol.Optional(ATTR_QUANTITY, default=1): _QTY})
ADD_ITEM_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_NAME): cv.string,
        vol.Optional(ATTR_QUANTITY): _QTY,
        vol.Optional(ATTR_MIN_STOCK): _MIN,
        vol.Optional(ATTR_UNIT): cv.string,
        vol.Optional(ATTR_ICON): cv.string,
        vol.Optional(ATTR_DEPARTMENT): cv.string,
    }
)
SET_STOCK_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_NAME): cv.string,
        vol.Required(ATTR_STOCK): _STOCK,
        vol.Optional(ATTR_MIN_STOCK): _MIN,
    }
)
GET_ITEMS_SCHEMA = vol.Schema(
    {vol.Optional(ATTR_LOW_ONLY, default=False): cv.boolean, vol.Optional(ATTR_DEPARTMENT): cv.string}
)


def _manager(hass: HomeAssistant) -> DespensaManager:
    manager: DespensaManager | None = hass.data.get(DOMAIN)
    if manager is None:
        raise ServiceValidationError(translation_domain=DOMAIN, translation_key="not_loaded")
    return manager


def _find(manager: DespensaManager, name: str) -> dict[str, Any]:
    try:
        return manager.find(name)
    except DespensaError as err:
        if err.code == "ambiguous":
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="ambiguous",
                translation_placeholders={"name": name, "options": ", ".join(err.candidates)},
            ) from err
        raise ServiceValidationError(
            translation_domain=DOMAIN, translation_key="item_not_found", translation_placeholders={"name": name}
        ) from err


def public_item(manager: DespensaManager, item: dict[str, Any]) -> dict[str, Any]:
    """Producto con el nombre legible de la balda."""
    depts = {d["id"]: d["name"] for d in manager.departments}
    return {
        "name": item["name"],
        "icon": item["icon"],
        "stock": item["stock"],
        "min_stock": item.get("min_stock"),
        "unit": item.get("unit", ""),
        "department": depts.get(item["department"], item["department"]),
        "low": manager.is_low(item),
        "in_cesta": normalize(item["name"]) in manager.cesta_in_list,
    }


def _response(manager: DespensaManager, item: dict[str, Any]) -> dict[str, Any]:
    return {**public_item(manager, item), "text": describe_stock(item)}


@callback
def async_register_services(hass: HomeAssistant) -> None:
    """Registra las acciones despensa.*"""

    @callback
    def use_item(call: ServiceCall) -> ServiceResponse:
        manager = _manager(hass)
        item = _find(manager, call.data[ATTR_NAME])
        manager.adjust(item["id"], -call.data[ATTR_QUANTITY], kind=KIND_USED, source=SOURCE_SERVICE)
        return _response(manager, item) if call.return_response else None

    @callback
    def add_item(call: ServiceCall) -> ServiceResponse:
        manager = _manager(hass)
        try:
            item, _entry = manager.create_item(
                call.data[ATTR_NAME],
                stock=call.data.get(ATTR_QUANTITY),
                icon=call.data.get(ATTR_ICON),
                department=call.data.get(ATTR_DEPARTMENT),
                min_stock=call.data.get(ATTR_MIN_STOCK, UNSET),
                unit=call.data.get(ATTR_UNIT),
                source=SOURCE_SERVICE,
            )
            if ATTR_MIN_STOCK in call.data or ATTR_UNIT in call.data:
                manager.update_item(
                    item["id"],
                    **{k: call.data[k] for k in (ATTR_MIN_STOCK, ATTR_UNIT) if k in call.data},
                )
        except DespensaError as err:
            raise ServiceValidationError(str(err)) from err
        return _response(manager, item) if call.return_response else None

    @callback
    def set_stock(call: ServiceCall) -> ServiceResponse:
        manager = _manager(hass)
        item = _find(manager, call.data[ATTR_NAME])
        if ATTR_MIN_STOCK in call.data:
            manager.update_item(item["id"], min_stock=call.data[ATTR_MIN_STOCK])
        stock = call.data[ATTR_STOCK]
        manager.set_stock(item["id"], stock, source=SOURCE_SERVICE, **({"kind": KIND_EMPTY} if stock == 0 else {}))
        return _response(manager, item) if call.return_response else None

    @callback
    def get_items(call: ServiceCall) -> ServiceResponse:
        manager = _manager(hass)
        items = manager.low_items() if call.data[ATTR_LOW_ONLY] else manager.sorted_items()
        if dept := call.data.get(ATTR_DEPARTMENT):
            dept_id = manager.resolve_department(dept)
            if dept_id is None:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="department_not_found",
                    translation_placeholders={"department": dept},
                )
            items = [i for i in items if i["department"] == dept_id]
        public = [public_item(manager, i) for i in items]
        lines = []
        for item in public:
            unit = f" {item['unit']}" if item["unit"] else ""
            lines.append(f"{item['icon']} {item['name']}: {item['stock']}{unit}" + (" ⚠️" if item["low"] else ""))
        return {"count": len(public), "items": public, "text": "\n".join(lines)}

    async def add_low_to_cesta(call: ServiceCall) -> ServiceResponse:
        _manager(hass)
        bridge = hass.data.get(f"{DOMAIN}_bridge")
        if bridge is None or not bridge.available:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="no_cesta")
        added = await bridge.async_add_low()
        return {"count": len(added), "added": added} if call.return_response else None

    hass.services.async_register(
        DOMAIN, SERVICE_USE_ITEM, use_item, schema=USE_ITEM_SCHEMA, supports_response=SupportsResponse.OPTIONAL
    )
    hass.services.async_register(
        DOMAIN, SERVICE_ADD_ITEM, add_item, schema=ADD_ITEM_SCHEMA, supports_response=SupportsResponse.OPTIONAL
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SET_STOCK, set_stock, schema=SET_STOCK_SCHEMA, supports_response=SupportsResponse.OPTIONAL
    )
    hass.services.async_register(
        DOMAIN, SERVICE_GET_ITEMS, get_items, schema=GET_ITEMS_SCHEMA, supports_response=SupportsResponse.ONLY
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_LOW_TO_CESTA,
        add_low_to_cesta,
        supports_response=SupportsResponse.OPTIONAL,
    )
