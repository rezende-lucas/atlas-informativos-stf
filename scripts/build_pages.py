"""Gera docs/index.html (página completa para o GitHub Pages) a partir de src/atlas.html."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src", "atlas.html")
OUT = os.path.join(ROOT, "docs", "index.html")

ICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
        "%3Crect width='32' height='32' rx='7' fill='%231E5B48'/%3E"
        "%3Cpath d='M16 7v17M9 24h14M8 11h16M8 11l-3 7h6zM24 11l-3 7h6z' fill='none' stroke='%23fff' "
        "stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E")

HEAD = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="Busca, filtros, leitor, flashcards, índice de legislação e temas de repercussão geral dos Informativos do STF (1995–2026).">
<link rel="icon" href="{ICON}">
<style>
:root{{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}
body{{margin:0;font:14px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif;background:#fafafa}}
img{{max-width:100%}}
[hidden]{{display:none!important}}
</style>
</head>
<body>
"""

with open(SRC, encoding="utf-8") as f:
    page = f.read()
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(HEAD + page + "\n</body>\n</html>\n")
open(os.path.join(ROOT, "docs", ".nojekyll"), "w").close()
print("gerado", OUT)
