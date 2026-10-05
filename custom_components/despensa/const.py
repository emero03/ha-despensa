"""Constantes de la integración Despensa."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "despensa"
NAME: Final = "Despensa"
VERSION: Final = "1.0.0"

STORAGE_KEY: Final = DOMAIN
STORAGE_VERSION: Final = 1
SAVE_DELAY: Final = 1

# Panel lateral y ficheros estáticos
PANEL_URL_PATH: Final = "despensa"
PANEL_ICON: Final = "mdi:cupboard-outline"
PANEL_COMPONENT: Final = "despensa-panel"
STATIC_URL: Final = "/despensa_static"
FRONTEND_FILE: Final = "despensa.js"

# Cesta (https://github.com/emero03/ha-cesta)
CESTA_DOMAIN: Final = "cesta"
CESTA_UNDO_WINDOW: Final = 15 * 60  # segundos en los que un "Deshacer" de Cesta se refleja aquí

# Límites
MAX_LOG: Final = 120  # movimientos recordados
MAX_STOCK: Final = 9999
MAX_DELETED: Final = 20  # productos quitados que aún se pueden recuperar con "Deshacer"
MERGE_WINDOW: Final = 90  # segundos: pulsaciones seguidas de +/- se agrupan en un movimiento

DEFAULT_ICON: Final = "🛒"
FALLBACK_DEPARTMENT: Final = "otros"

DEFAULT_SETTINGS: Final[dict[str, object]] = {
    "default_min": 0,  # mínimo para productos nuevos (None = sin aviso). 0 = avisar al acabarse
    "add_from_cesta": True,  # al comprar en Cesta algo que no está en la despensa, añadirlo
    "auto_cesta": False,  # al llegar al mínimo, añadirlo a la Cesta automáticamente
    "voice": True,  # frases de voz para Assist
}

# Las mismas secciones y colores que Cesta. Si Cesta está instalada, se usan las suyas
# (con el orden y los colores que el usuario haya elegido allí).
DEFAULT_DEPARTMENTS: Final[list[dict[str, str]]] = [
    {"id": "fruta_verdura", "name": "Frutas y verduras", "icon": "🥦", "color": "#43A047"},
    {"id": "panaderia", "name": "Panadería", "icon": "🥖", "color": "#C9922E"},
    {"id": "carne", "name": "Carnicería", "icon": "🥩", "color": "#E53935"},
    {"id": "pescado", "name": "Pescadería", "icon": "🐟", "color": "#1E88E5"},
    {"id": "charcuteria", "name": "Charcutería y quesos", "icon": "🧀", "color": "#FB8C00"},
    {"id": "lacteos", "name": "Lácteos y huevos", "icon": "🥛", "color": "#F9C02D"},
    {"id": "despensa", "name": "Despensa", "icon": "🥫", "color": "#9E9D24"},
    {"id": "desayuno", "name": "Desayuno y dulces", "icon": "🍪", "color": "#EC407A"},
    {"id": "congelados", "name": "Congelados", "icon": "🧊", "color": "#00ACC1"},
    {"id": "bebidas", "name": "Bebidas", "icon": "🥤", "color": "#8E24AA"},
    {"id": "limpieza", "name": "Limpieza y hogar", "icon": "🧽", "color": "#3949AB"},
    {"id": "higiene", "name": "Higiene y salud", "icon": "🧴", "color": "#00897B"},
    {"id": "mascotas", "name": "Mascotas", "icon": "🐾", "color": "#6D4C41"},
    {"id": "otros", "name": "Otros", "icon": "🛒", "color": "#78909C"},
]

# Origen de cada movimiento
SOURCE_PANEL: Final = "panel"
SOURCE_CESTA: Final = "cesta"
SOURCE_VOICE: Final = "voz"
SOURCE_SERVICE: Final = "accion"

# Tipo de movimiento
KIND_USED: Final = "used"  # he usado
KIND_EMPTY: Final = "empty"  # se ha acabado
KIND_PURCHASED: Final = "purchased"  # comprado en Cesta
KIND_ADDED: Final = "added"  # añadido a mano
KIND_SET: Final = "set"  # stock corregido

EVENT_LOW_STOCK: Final = f"{DOMAIN}_low_stock"

# Servicios
SERVICE_USE_ITEM: Final = "use_item"
SERVICE_ADD_ITEM: Final = "add_item"
SERVICE_SET_STOCK: Final = "set_stock"
SERVICE_GET_ITEMS: Final = "get_items"
SERVICE_ADD_LOW_TO_CESTA: Final = "add_low_to_cesta"

ATTR_NAME: Final = "name"
ATTR_QUANTITY: Final = "quantity"
ATTR_STOCK: Final = "stock"
ATTR_MIN_STOCK: Final = "min_stock"
ATTR_UNIT: Final = "unit"
ATTR_ICON: Final = "icon"
ATTR_DEPARTMENT: Final = "department"
ATTR_LOW_ONLY: Final = "low_only"
