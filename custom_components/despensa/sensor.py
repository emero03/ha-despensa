"""Sensor "Por reponer": cuántos productos han llegado a su mínimo.

Sirve para badges en los paneles y para automatizaciones (avisar al móvil,
mandar la lista al llegar al súper...). Los atributos llevan el detalle.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, NAME, VERSION
from .manager import DespensaManager
from .services import public_item


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([DespensaLowSensor(hass.data[DOMAIN], entry)])


class DespensaLowSensor(SensorEntity):
    """Número de productos por reponer."""

    _attr_has_entity_name = True
    _attr_name = "Por reponer"
    _attr_icon = "mdi:basket-unfill"
    _attr_native_unit_of_measurement = "productos"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_should_poll = False

    def __init__(self, manager: DespensaManager, entry: ConfigEntry) -> None:
        self._manager = manager
        self._attr_unique_id = f"{entry.entry_id}_low"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=NAME,
            manufacturer=NAME,
            model="Inventario de la despensa",
            sw_version=VERSION,
            entry_type=DeviceEntryType.SERVICE,
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._manager.async_add_listener(self._handle_change))

    @callback
    def _handle_change(self) -> None:
        self.async_write_ha_state()

    @property
    def native_value(self) -> int:
        return len(self._manager.low_items())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        low = [public_item(self._manager, i) for i in self._manager.low_items()]
        return {
            "productos": [i["name"] for i in low],
            "detalle": low,
            "texto": "\n".join(
                f"{i['icon']} {i['name']} ({i['stock']}{' ' + i['unit'] if i['unit'] else ''})" for i in low
            ),
            "total": len(self._manager.items),
            "agotados": sum(1 for i in self._manager.items if i["stock"] <= 0),
        }
