"""Собирает сайт ссылок DR.JOYS в docs/ (его отдаёт GitHub Pages).

  site/            исходники страницы-хаба и картинки
  links.json       ссылки для шапки Instagram: slug -> куда ведёт
  docs/            результат: хаб, /<slug>/ страницы-переходы, /og/*.jpg обложки

Запуск: <python с playwright и PIL> tools/build.py [--no-og]
Страница-переход отдаёт краулеру Instagram og:image с фирменной обложкой
(он не выполняет JS), а человека сразу уводит на target через location.replace.
"""
import html
import json
import shutil
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE, DOCS = ROOT / "site", ROOT / "docs"
CFG = json.loads((ROOT / "links.json").read_text())
BASE = CFG["base"].rstrip("/")

REDIRECT = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{og_title}</title>
<meta name="robots" content="noindex">
<meta property="og:type" content="website">
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="{og_desc}">
<meta property="og:image" content="{base}/og/{slug}.jpg">
<meta property="og:image:width" content="1080">
<meta property="og:image:height" content="1080">
<meta property="og:url" content="{base}/{slug}/">
<meta name="theme-color" content="#0d0d0d">
<link rel="icon" href="../assets/shield.svg" type="image/svg+xml">
<script>location.replace({target_js})</script>
<style>
@font-face{{font-family:Benzin;src:url(../assets/benzin.woff2) format("woff2");font-weight:700;font-display:swap}}
html,body{{height:100%;margin:0}}
body{{background:#0d0d0d;color:#fff;display:grid;place-items:center;text-align:center;
  font:400 15px/1.4 -apple-system,BlinkMacSystemFont,"SF Pro Display",system-ui,sans-serif}}
img{{width:78px;animation:beat 1s ease-in-out infinite}}
b{{display:block;font:700 18px/1.1 Benzin,"Arial Black",sans-serif;text-transform:uppercase;margin:22px 0 14px}}
a{{color:rgba(255,255,255,.6)}}
@keyframes beat{{50%{{transform:scale(1.12)}}}}
</style>
</head>
<body>
<div>
  <img src="../assets/shield.svg" alt="">
  <b>Открываем {store}</b>
  <a href="{target}">Не открылось? Нажмите сюда</a>
</div>
</body>
</html>
"""


def encode_target(url):
    # кириллица в query (текст для WhatsApp) должна уйти закодированной
    p = urllib.parse.urlsplit(url)
    q = urllib.parse.urlencode(urllib.parse.parse_qsl(p.query, keep_blank_values=True))
    return urllib.parse.urlunsplit((p.scheme, p.netloc, p.path, q, p.fragment))


def build_pages():
    if DOCS.exists():
        shutil.rmtree(DOCS)
    shutil.copytree(SITE, DOCS)
    index = DOCS / "index.html"
    index.write_text(index.read_text().replace("{{BASE}}", BASE))
    for link in CFG["links"]:
        target = encode_target(link["target"])
        page = REDIRECT.format(
            base=BASE,
            slug=link["slug"],
            store=html.escape(link["store"]),
            og_title=html.escape(link["og_title"]),
            og_desc=html.escape(link["og_desc"]),
            target=html.escape(target),
            target_js=json.dumps(target),
        )
        (DOCS / link["slug"]).mkdir()
        (DOCS / link["slug"] / "index.html").write_text(page)
    (DOCS / ".nojekyll").write_text("")
    domain = urllib.parse.urlsplit(BASE)
    if not domain.netloc.endswith("github.io"):
        (DOCS / "CNAME").write_text(domain.netloc + "\n")


def build_og():
    from playwright.sync_api import sync_playwright
    from PIL import Image

    out = DOCS / "og"
    out.mkdir(exist_ok=True)
    slugs = ["hub"] + [l["slug"] for l in CFG["links"]]
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1080})
        for slug in slugs:
            page.goto((ROOT / "tools" / "og.html").as_uri() + f"?v={slug}")
            page.wait_for_load_state("load")
            page.evaluate("document.fonts.ready")
            png = out / f"{slug}.png"
            page.screenshot(path=str(png))
            Image.open(png).convert("RGB").save(out / f"{slug}.jpg", quality=88, optimize=True, progressive=True)
            png.unlink()
            print("og", slug)
        browser.close()


if __name__ == "__main__":
    build_pages()
    if "--no-og" not in sys.argv:
        build_og()
    print("ok ->", DOCS)
