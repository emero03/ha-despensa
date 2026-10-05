"""Genera preview/despensa-preview.html a partir del frontend y el catálogo reales.

Uso: python3 tools/build_preview.py
"""

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPONENT = ROOT / "custom_components" / "despensa"


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, COMPONENT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


catalog = load("catalog")
const = load("const")

html = (ROOT / "preview" / "template.html").read_text(encoding="utf-8")
despensa_js = (COMPONENT / "frontend" / "despensa.js").read_text(encoding="utf-8")
mock_js = (ROOT / "preview" / "mock-backend.js").read_text(encoding="utf-8")
assert "</script" not in despensa_js + mock_js

dump = lambda value: json.dumps(value, ensure_ascii=False, separators=(",", ":"))
for marker, value in {
    "/*CATALOG*/": dump(catalog.CATALOG),
    "/*DEPARTMENTS*/": dump(const.DEFAULT_DEPARTMENTS),
    "/*MOCK_JS*/": mock_js,
    "/*DESPENSA_JS*/": despensa_js,
}.items():
    assert html.count(marker) == 1, marker
    html = html.replace(marker, value)

out = ROOT / "preview" / "despensa-preview.html"
out.write_text(html, encoding="utf-8")
print(f"{out} ({len(html) // 1024} KB)")
