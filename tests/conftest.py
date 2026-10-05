"""Fixtures comunes.

Las pruebas de integración con Cesta necesitan una copia de Cesta
(https://github.com/emero03/ha-cesta). Se busca en ../ha-cesta o en la ruta de la
variable CESTA_REPO; si no está, esas pruebas se saltan.
"""

import os
from pathlib import Path
import sys

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

ROOT = Path(__file__).resolve().parent.parent
CESTA_REPO = Path(os.environ.get("CESTA_REPO", ROOT.parent / "ha-cesta"))
HAS_CESTA = (CESTA_REPO / "custom_components" / "cesta" / "manifest.json").is_file()
if HAS_CESTA:
    # custom_components es un paquete de espacio de nombres: se juntan los dos repositorios.
    sys.path.insert(0, str(CESTA_REPO))

from custom_components.despensa.const import DOMAIN  # noqa: E402

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Permite cargar custom_components en los tests."""
    yield


@pytest.fixture
async def setup_despensa(hass: HomeAssistant) -> MockConfigEntry:
    """Configura Despensa (en español, como en casa)."""
    hass.config.language = "es"
    assert await async_setup_component(hass, "http", {})
    entry = MockConfigEntry(domain=DOMAIN, title="Despensa", data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


@pytest.fixture
async def setup_both(hass: HomeAssistant) -> tuple[MockConfigEntry, MockConfigEntry]:
    """Configura Cesta y después Despensa."""
    if not HAS_CESTA:
        pytest.skip("Cesta no está disponible (define CESTA_REPO)")
    hass.config.language = "es"
    assert await async_setup_component(hass, "http", {})
    cesta = MockConfigEntry(domain="cesta", title="Cesta", data={})
    cesta.add_to_hass(hass)
    assert await hass.config_entries.async_setup(cesta.entry_id)
    despensa = MockConfigEntry(domain=DOMAIN, title="Despensa", data={})
    despensa.add_to_hass(hass)
    assert await hass.config_entries.async_setup(despensa.entry_id)
    await hass.async_block_till_done()
    return cesta, despensa
