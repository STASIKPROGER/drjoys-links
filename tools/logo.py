"""Логотип DR.JOYS «в две строки» из PNG со страницы игры (src/logo-stack.png, 640×482).

Буквы берём из PNG, щит и сердце рисуем вектором из site/assets/logo.svg поверх —
так сердце можно анимировать отдельно (SMIL: работает и в <img>, и во встроенном SVG на iPhone).
На выходе:
  site/assets/logo-letters.png      белые буквы без щита
  site/assets/logo-inline.svg       разметка для вставки в страницу (build.py подставляет вместо <!--LOGO-->)
  site/assets/logo-stack.svg        то же самостоятельным файлом (PNG внутри base64) для <img>
  build/og-src/logo-stack-onred.svg белые буквы, белый щит, красное сердце (обложки на красном)
  build/og-src/logo-stack-dark.svg  тёмные буквы, красный щит, белое сердце (обложки на белом)
"""
import base64
import io
import re
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
ASSETS, OG = ROOT / "site" / "assets", ROOT / "build" / "og-src"
W, H = 640, 482

svg = (ASSETS / "logo.svg").read_text()
d = re.search(r'<path d="(M1002\.27[^"]*)"[^>]*fill="#E42521"/>', svg).group(1)
_, shield_d, heart_d = d.split("M")
shield_d, heart_d = "M" + shield_d, "M" + heart_d

# щит в logo.svg: bbox x 666.3, y 0, ширина 336.2; в PNG тот же щит: x 382..636, y 4..244
S = (636 - 382) / 336.2
PLACE = f"translate({382 - 666.3 * S:.2f} {4:.2f}) scale({S:.5f})"


def letters_png():
    """PNG без щита: всё под векторным щитом (с запасом 2px) делаем прозрачным."""
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H})
        pg.set_content(
            f'<body style="margin:0;background:#000"><svg width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f'<g transform="{PLACE}"><path d="{shield_d}" fill="#fff" stroke="#fff" stroke-width="{4 / S:.1f}"/></g></svg></body>'
        )
        mask = Image.open(io.BytesIO(pg.screenshot())).convert("L")
        b.close()
    im = Image.open(ROOT / "src" / "logo-stack.png").convert("RGBA")
    px, m = im.load(), mask.load()
    for y in range(H):
        for x in range(W):
            if m[x, y] > 40:
                px[x, y] = (0, 0, 0, 0)
    return im


def tint(im, rgb):
    out = Image.new("RGBA", im.size, rgb + (0,))
    out.putalpha(im.getchannel("A"))
    return out


def b64(im):
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


# центр сердца в координатах logo.svg (bbox 728.3, 56.8, 211.8×186.3), чуть ниже середины
HX, HY = 834.2, 159.3
# «тук-тук»: два удара и пауза
BEAT = ('<animateTransform attributeName="transform" type="scale" dur="1.4s" repeatCount="indefinite" '
        'values="1;1.16;1;1.09;1;1" keyTimes="0;.12;.24;.36;.5;1"/>')


def heart(fill, beat):
    path = f'<path d="{heart_d}" fill="{fill}"/>'
    if not beat:
        return path
    return f'<g transform="translate({HX} {HY})"><g>{BEAT}<g transform="translate({-HX} {-HY})">{path}</g></g></g>'


def compose(letters_href, shield_fill, heart_fill, beat, attrs=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}"{attrs}>'
        f'<image href="{letters_href}" width="{W}" height="{H}"/>'
        f'<g transform="{PLACE}"><path d="{shield_d}" fill="{shield_fill}"/>{heart(heart_fill, beat)}</g></svg>'
    )


if __name__ == "__main__":
    OG.mkdir(parents=True, exist_ok=True)
    white = letters_png()
    white.save(ASSETS / "logo-letters.png", optimize=True)
    data = "data:image/png;base64," + b64(white)
    (ASSETS / "logo-inline.svg").write_text(compose(
        "assets/logo-letters.png", "#E42521", "#FFFFFF", beat=True,
        attrs=' class="logo" role="img" aria-label="DR.JOYS" width="150" height="113"'))
    (ASSETS / "logo-stack.svg").write_text(compose(data, "#E42521", "#FFFFFF", beat=True))
    (OG / "logo-stack-onred.svg").write_text(compose(data, "#FFFFFF", "#E42521", beat=False))
    dark = "data:image/png;base64," + b64(tint(white, (0x1D, 0x1D, 0x1B)))
    (OG / "logo-stack-dark.svg").write_text(compose(dark, "#E42521", "#FFFFFF", beat=False))
    print("ok", (ASSETS / "logo-stack.svg").stat().st_size // 1024, "KB")
