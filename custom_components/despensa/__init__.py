"""Despensa: inventario de casa con stock mínimo, enlazado con Cesta y con la voz."""

from __future__ import annotations

import hashlib
from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.storage import Store
from homeassistant.helpers.typing import ConfigType

from .cesta_bridge import CestaBridge
from .const import (
    DOMAIN,
    FRONTEND_FILE,
    NAME,
    PANEL_COMPONENT,
    PANEL_ICON,
    PANEL_URL_PATH,
    STATIC_URL,
    STORAGE_KEY,
    STORAGE_VERSION,
)
from .manager import DespensaManager
from .services import async_register_services
from .voice import VoiceSentences, async_register_intents, async_remove_intents
from .websocket import DATA_BRIDGE, DATA_VOICE, async_register_websocket_api

PLATFORMS: list[Platform] = [Platform.SENSOR]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

FRONTEND_DIR = Path(__file__).parent / "frontend"
DATA_STATIC_REGISTERED = f"{DOMAIN}_static_registered"
DATA_JS_URL = f"{DOMAIN}_js_url"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Comandos websocket y acciones: se registran una sola vez."""
    async_register_websocket_api(hass)
    async_register_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Carga los datos, el puente con Cesta, la voz, el panel, la tarjeta y el sensor."""
    manager = DespensaManager(hass)
    await manager.async_load()
    hass.data[DOMAIN] = manager

    bridge = CestaBridge(hass, manager)
    bridge.async_start()
    hass.data[DATA_BRIDGE] = bridge

    async_register_intents(hass)
    voice = VoiceSentences(hass, manager)
    voice.async_start()
    hass.data[DATA_VOICE] = voice

    await _async_register_frontend(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Descarga la integración (el panel desaparece de la barra lateral)."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        frontend.async_remove_panel(hass, PANEL_URL_PATH, warn_if_unknown=False)
        if url := hass.data.pop(DATA_JS_URL, None):
            frontend.remove_extra_js_url(hass, url)
        if voice := hass.data.pop(DATA_VOICE, None):
            voice.async_stop()
        if bridge := hass.data.pop(DATA_BRIDGE, None):
            bridge.async_stop()
        async_remove_intents(hass)
        hass.data.pop(DOMAIN, None)
    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Al eliminar la integración se borran también sus datos."""
    await Store(hass, STORAGE_VERSION, STORAGE_KEY).async_remove()


def _file_version(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:10]


async def _async_register_frontend(hass: HomeAssistant) -> None:
    if not hass.data.get(DATA_STATIC_REGISTERED):
        await hass.http.async_register_static_paths(
            [StaticPathConfig(STATIC_URL, str(FRONTEND_DIR), True)]
        )
        hass.data[DATA_STATIC_REGISTERED] = True

    # El hash en la URL obliga al navegador a recargar el JS tras cada actualización.
    version = await hass.async_add_executor_job(_file_version, FRONTEND_DIR / FRONTEND_FILE)
    url = f"{STATIC_URL}/{FRONTEND_FILE}?v={version}"

    # Carga la tarjeta "custom:despensa-card" en los paneles de control.
    frontend.add_extra_js_url(hass, url)
    hass.data[DATA_JS_URL] = url

    if PANEL_URL_PATH not in hass.data.get(frontend.DATA_PANELS, {}):
        await panel_custom.async_register_panel(
            hass,
            frontend_url_path=PANEL_URL_PATH,
            webcomponent_name=PANEL_COMPONENT,
            sidebar_title=NAME,
            sidebar_icon=PANEL_ICON,
            module_url=url,
            require_admin=False,
            config={},
        )
