"""Логотип DR.JOYS «в две строки» из PNG со страницы игры (src/logo-stack.png, 640×482).

Буквы берём из PNG, щит и сердце рисуем вектором из site/assets/logo.svg поверх —
так сердце можно анимировать отдельно. На выходе самодостаточные SVG (PNG внутри base64):
  site/assets/logo-stack.svg        белые буквы, красный щит, бьющееся белое сердце (для тёмного фона)
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


def compose(letters, shield_fill, heart_fill, beat):
    style = ""
    heart_attr = ""
    if beat:
        heart_attr = ' class="beat"'
        style = (
            "<style>.beat{transform-box:fill-box;transform-origin:50% 55%;animation:beat 1.4s ease-in-out infinite}"
            "@keyframes beat{0%,50%,100%{transform:scale(1)}12%{transform:scale(1.16)}24%{transform:scale(1)}36%{transform:scale(1.09)}}"
            "@media (prefers-reduced-motion:reduce){.beat{animation:none}}</style>"
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">{style}'
        f'<image href="data:image/png;base64,{b64(letters)}" width="{W}" height="{H}"/>'
        f'<g transform="{PLACE}"><path d="{shield_d}" fill="{shield_fill}"/>'
        f'<path{heart_attr} d="{heart_d}" fill="{heart_fill}"/></g></svg>'
    )


if __name__ == "__main__":
    OG.mkdir(parents=True, exist_ok=True)
    white = letters_png()
    (ASSETS / "logo-stack.svg").write_text(compose(white, "#E42521", "#FFFFFF", beat=True))
    (OG / "logo-stack-onred.svg").write_text(compose(white, "#FFFFFF", "#E42521", beat=False))
    (OG / "logo-stack-dark.svg").write_text(compose(tint(white, (0x1D, 0x1D, 0x1B)), "#E42521", "#FFFFFF", beat=False))
    print("ok", (ASSETS / "logo-stack.svg").stat().st_size // 1024, "KB")
