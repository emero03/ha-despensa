"""Catálogo de productos predefinidos: nombre, icono y departamento.

Es el mismo catálogo que usa Cesta (mismos nombres, iconos y departamentos),
para que un producto se vea igual en la lista de la compra y en la despensa.
Se incluye una copia para que Despensa funcione aunque Cesta no esté instalada.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Final, TypedDict


class CatalogEntry(TypedDict):
    """Producto del catálogo."""

    name: str
    icon: str
    department: str


_RAW: Final[dict[str, list[tuple[str, str]]]] = {
    "fruta_verdura": [
        ("Manzanas", "🍎"), ("Peras", "🍐"), ("Naranjas", "🍊"), ("Mandarinas", "🍊"),
        ("Limones", "🍋"), ("Lima", "🍋"), ("Pomelo", "🍊"), ("Plátanos", "🍌"),
        ("Sandía", "🍉"), ("Melón", "🍈"), ("Uvas", "🍇"), ("Fresas", "🍓"),
        ("Frambuesas", "🍓"), ("Arándanos", "🫐"), ("Cerezas", "🍒"), ("Melocotones", "🍑"),
        ("Nectarinas", "🍑"), ("Mango", "🥭"), ("Piña", "🍍"), ("Coco", "🥥"),
        ("Kiwis", "🥝"), ("Aguacates", "🥑"), ("Tomates", "🍅"), ("Tomates cherry", "🍅"),
        ("Berenjenas", "🍆"), ("Patatas", "🥔"), ("Boniatos", "🍠"), ("Zanahorias", "🥕"),
        ("Mazorcas de maíz", "🌽"), ("Pimientos", "🫑"), ("Guindillas", "🌶️"),
        ("Pepinos", "🥒"), ("Calabacines", "🥒"), ("Lechuga", "🥬"), ("Espinacas", "🥬"),
        ("Rúcula", "🥬"), ("Canónigos", "🥬"), ("Col", "🥬"), ("Apio", "🥬"),
        ("Ensalada en bolsa", "🥗"), ("Brócoli", "🥦"), ("Coliflor", "🥦"),
        ("Cebollas", "🧅"), ("Cebolletas", "🧅"), ("Puerros", "🧅"), ("Ajos", "🧄"),
        ("Jengibre", "🫚"), ("Champiñones", "🍄"), ("Setas", "🍄"), ("Judías verdes", "🫛"),
        ("Guisantes", "🫛"), ("Calabaza", "🎃"), ("Perejil", "🌿"), ("Cilantro", "🌿"),
        ("Albahaca", "🌿"), ("Hierbabuena", "🌿"), ("Castañas", "🌰"),
    ],
    "panaderia": [
        ("Pan", "🍞"), ("Barra de pan", "🥖"), ("Pan de molde", "🍞"), ("Pan integral", "🍞"),
        ("Picos", "🥖"), ("Croissants", "🥐"), ("Napolitanas", "🥐"), ("Magdalenas", "🧁"),
        ("Donuts", "🍩"), ("Bagels", "🥯"), ("Pan de pita", "🫓"), ("Tortillas de trigo", "🫓"),
        ("Pretzels", "🥨"), ("Bizcocho", "🍰"), ("Tarta", "🎂"), ("Empanada", "🥟"),
    ],
    "carne": [
        ("Pollo", "🍗"), ("Pechugas de pollo", "🍗"), ("Muslos de pollo", "🍗"),
        ("Alitas de pollo", "🍗"), ("Carne picada", "🥩"), ("Ternera", "🥩"),
        ("Filetes de ternera", "🥩"), ("Lomo de cerdo", "🥩"), ("Solomillo", "🥩"),
        ("Costillas", "🍖"), ("Chuletas", "🍖"), ("Cordero", "🍖"), ("Pavo", "🦃"),
        ("Hamburguesas", "🍔"), ("Salchichas", "🌭"), ("Conejo", "🐇"),
    ],
    "pescado": [
        ("Salmón", "🐟"), ("Merluza", "🐟"), ("Bacalao", "🐟"), ("Atún fresco", "🐟"),
        ("Dorada", "🐟"), ("Lubina", "🐟"), ("Sardinas", "🐟"), ("Boquerones", "🐟"),
        ("Gambas", "🦐"), ("Langostinos", "🦐"), ("Calamares", "🦑"), ("Sepia", "🦑"),
        ("Pulpo", "🐙"), ("Mejillones", "🦪"), ("Almejas", "🦪"), ("Surimi", "🦀"),
        ("Sushi", "🍣"),
    ],
    "charcuteria": [
        ("Jamón serrano", "🍖"), ("Jamón cocido", "🥓"), ("Pavo en lonchas", "🦃"),
        ("Chorizo", "🌭"), ("Salchichón", "🌭"), ("Fuet", "🌭"), ("Lomo embuchado", "🥓"),
        ("Mortadela", "🥓"), ("Bacon", "🥓"), ("Queso", "🧀"), ("Queso curado", "🧀"),
        ("Queso fresco", "🧀"), ("Queso rallado", "🧀"), ("Queso en lonchas", "🧀"),
        ("Mozzarella", "🧀"), ("Hummus", "🫘"), ("Gazpacho", "🍅"), ("Tortilla de patatas", "🍳"),
        ("Masa de hojaldre", "🥐"), ("Pizza fresca", "🍕"),
    ],
    "lacteos": [
        ("Leche", "🥛"), ("Leche sin lactosa", "🥛"), ("Bebida de avena", "🥛"),
        ("Bebida de soja", "🥛"), ("Yogures", "🥣"), ("Yogur griego", "🥣"), ("Kéfir", "🥛"),
        ("Mantequilla", "🧈"), ("Margarina", "🧈"), ("Nata para cocinar", "🥛"),
        ("Nata para montar", "🍦"), ("Huevos", "🥚"), ("Natillas", "🍮"), ("Flan", "🍮"),
        ("Cuajada", "🍮"), ("Requesón", "🧀"),
    ],
    "despensa": [
        ("Arroz", "🍚"), ("Pasta", "🍝"), ("Espaguetis", "🍝"), ("Macarrones", "🍝"),
        ("Fideos", "🍜"), ("Noodles", "🍜"), ("Lentejas", "🫘"), ("Garbanzos", "🫘"),
        ("Alubias", "🫘"), ("Quinoa", "🌾"), ("Cuscús", "🌾"), ("Harina", "🌾"),
        ("Levadura", "🍞"), ("Pan rallado", "🍞"), ("Azúcar", "🧂"), ("Sal", "🧂"),
        ("Pimienta", "🧂"), ("Especias", "🌿"), ("Aceite de oliva", "🫒"),
        ("Aceite de girasol", "🌻"), ("Vinagre", "🍶"), ("Tomate frito", "🥫"),
        ("Tomate triturado", "🥫"), ("Atún en lata", "🥫"), ("Sardinas en lata", "🥫"),
        ("Maíz dulce", "🌽"), ("Aceitunas", "🫒"), ("Pepinillos", "🥒"), ("Caldo", "🍲"),
        ("Sopa", "🍜"), ("Mayonesa", "🫙"), ("Ketchup", "🍅"), ("Mostaza", "🫙"),
        ("Salsa de soja", "🍶"), ("Tortillas mexicanas", "🌮"), ("Frutos secos", "🥜"),
        ("Almendras", "🥜"), ("Cacahuetes", "🥜"), ("Nueces", "🌰"), ("Pipas", "🌻"),
        ("Patatas fritas", "🍟"), ("Palomitas", "🍿"), ("Crema de cacahuete", "🥜"),
    ],
    "desayuno": [
        ("Café", "☕"), ("Café molido", "☕"), ("Cápsulas de café", "☕"), ("Té", "🫖"),
        ("Infusiones", "🍵"), ("Cacao soluble", "🍫"), ("Cereales", "🥣"), ("Avena", "🌾"),
        ("Galletas", "🍪"), ("Chocolate", "🍫"), ("Bombones", "🍫"), ("Caramelos", "🍬"),
        ("Chicles", "🍬"), ("Gominolas", "🍬"), ("Turrón", "🍫"), ("Tortitas de arroz", "🍘"),
        ("Barritas de cereales", "🍫"), ("Miel", "🍯"), ("Mermelada", "🍓"),
    ],
    "congelados": [
        ("Helado", "🍦"), ("Polos", "🍧"), ("Hielo", "🧊"), ("Pizza congelada", "🍕"),
        ("Verduras congeladas", "🥦"), ("Guisantes congelados", "🫛"),
        ("Patatas congeladas", "🍟"), ("Croquetas", "🧆"), ("Varitas de merluza", "🐟"),
        ("Gambas congeladas", "🦐"), ("Lasaña", "🍝"), ("Empanadillas", "🥟"),
        ("Gyozas", "🥟"), ("Nuggets", "🍗"),
    ],
    "bebidas": [
        ("Agua", "💧"), ("Agua con gas", "🫧"), ("Zumo de naranja", "🧃"), ("Zumo", "🧃"),
        ("Refresco de cola", "🥤"), ("Refrescos", "🥤"), ("Tónica", "🥤"),
        ("Bebida isotónica", "🥤"), ("Batidos", "🥛"), ("Horchata", "🥛"), ("Cerveza", "🍺"),
        ("Cerveza sin alcohol", "🍺"), ("Vino tinto", "🍷"), ("Vino blanco", "🥂"),
        ("Tinto de verano", "🍷"), ("Cava", "🍾"), ("Sidra", "🍾"), ("Vermut", "🍸"),
        ("Ginebra", "🍸"), ("Ron", "🥃"), ("Whisky", "🥃"),
    ],
    "limpieza": [
        ("Detergente", "🧺"), ("Suavizante", "🧺"), ("Lejía", "🧴"), ("Lavavajillas", "🍽️"),
        ("Pastillas lavavajillas", "🍽️"), ("Friegasuelos", "🪣"), ("Limpiacristales", "🪟"),
        ("Limpiador multiusos", "🧴"), ("Estropajos", "🧽"), ("Bayetas", "🧽"),
        ("Bolsas de basura", "🗑️"), ("Papel de cocina", "🧻"), ("Servilletas", "🧻"),
        ("Papel de aluminio", "📦"), ("Film transparente", "📦"), ("Pilas", "🔋"),
        ("Bombillas", "💡"), ("Velas", "🕯️"), ("Ambientador", "🌸"), ("Insecticida", "🪰"),
        ("Guantes", "🧤"), ("Fregona", "🧹"), ("Escoba", "🧹"),
    ],
    "higiene": [
        ("Papel higiénico", "🧻"), ("Gel de ducha", "🧴"), ("Champú", "🧴"),
        ("Acondicionador", "🧴"), ("Jabón de manos", "🧼"), ("Pasta de dientes", "🪥"),
        ("Cepillo de dientes", "🪥"), ("Enjuague bucal", "🦷"), ("Desodorante", "🧴"),
        ("Crema hidratante", "🧴"), ("Protector solar", "🌞"), ("Cuchillas de afeitar", "🪒"),
        ("Espuma de afeitar", "🪒"), ("Compresas", "🌸"), ("Tampones", "🌸"),
        ("Pañuelos", "🤧"), ("Bastoncillos", "👂"), ("Algodón", "☁️"), ("Tiritas", "🩹"),
        ("Paracetamol", "💊"), ("Ibuprofeno", "💊"), ("Medicinas", "💊"), ("Pañales", "👶"),
        ("Toallitas", "👶"), ("Leche infantil", "🍼"), ("Potitos", "🍼"), ("Maquillaje", "💄"),
    ],
    "mascotas": [
        ("Pienso para perro", "🐶"), ("Comida para gato", "🐱"), ("Arena para gato", "🐱"),
        ("Snacks para perro", "🦴"), ("Comida húmeda", "🐾"), ("Comida para peces", "🐠"),
        ("Bolsas para excrementos", "🐾"),
    ],
    "otros": [
        ("Flores", "💐"), ("Plantas", "🪴"), ("Periódico", "📰"), ("Regalo", "🎁"),
        ("Carbón", "🔥"),
    ],
}

CATALOG: Final[list[CatalogEntry]] = [
    {"name": name, "icon": icon, "department": dept}
    for dept, entries in _RAW.items()
    for name, icon in entries
]

# Productos básicos para sugerir cuando aún no hay historial.
STAPLES: Final[list[str]] = [
    "Leche", "Pan", "Huevos", "Plátanos", "Tomates", "Aceite de oliva",
    "Papel higiénico", "Café", "Yogures", "Agua",
]


def normalize(text: str) -> str:
    """Normaliza un nombre: minúsculas, sin tildes y sin espacios extra."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text.strip().lower())


def _stem(word: str) -> str:
    """Raíz muy simple para tolerar singular/plural en español."""
    if len(word) > 3 and word.endswith("s"):
        word = word[:-1]
    if len(word) > 3 and word.endswith("e"):
        word = word[:-1]
    return word


def _stems(text: str) -> list[str]:
    return [_stem(w) for w in re.split(r"[^a-z0-9]+", normalize(text)) if w]


CATALOG_INDEX: Final[dict[str, CatalogEntry]] = {
    normalize(entry["name"]): entry for entry in CATALOG
}
_CATALOG_STEMS: Final[list[tuple[list[str], CatalogEntry]]] = [
    (_stems(entry["name"]), entry) for entry in CATALOG
]


_CATALOG_BY_STEMS: Final[dict[str, CatalogEntry]] = {
    " ".join(words): entry for words, entry in _CATALOG_STEMS
}


def canonical_product(name: str) -> CatalogEntry | None:
    """Producto del catálogo que es el mismo (sin tildes, singular o plural)."""
    key = normalize(name)
    if key in CATALOG_INDEX:
        return CATALOG_INDEX[key]
    return _CATALOG_BY_STEMS.get(" ".join(_stems(name)))


def guess_product(name: str) -> CatalogEntry | None:
    """Busca el producto del catálogo que mejor encaja con un nombre libre.

    "leche" -> Leche, "tomate" -> Tomates, "queso manchego" -> Queso,
    "pechuga de pavo" -> Pavo. Devuelve None si nada encaja.
    """
    key = normalize(name)
    if key in CATALOG_INDEX:
        return CATALOG_INDEX[key]
    words = _stems(name)
    if not words:
        return None
    best: CatalogEntry | None = None
    best_score = 0
    for cand_words, entry in _CATALOG_STEMS:
        size = len(cand_words)
        if size == 0 or size > len(words):
            continue
        for start in range(len(words) - size + 1):
            if words[start : start + size] == cand_words:
                score = sum(len(w) for w in cand_words) * 10 + (5 if start == 0 else 0)
                if size == len(words):
                    score += 1000  # mismo producto en singular/plural
                if score > best_score:
                    best, best_score = entry, score
                break
    return best
