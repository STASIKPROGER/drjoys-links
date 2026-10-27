"""Режет исходные фото (src/) в картинки карточек (site/assets/) и квадраты для обложек (build/og-src/)."""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC, OUT, OG = ROOT / "src", ROOT / "site" / "assets", ROOT / "build" / "og-src"

# доли от размера исходника: (left, top, right, bottom); исходники разного разрешения
CARDS = {
    "neon": ("neon-jungle.jpg", (0.173, 0.322, 0.92, 0.905)),
    "game": ("game-light.jpg", (0.173, 0.29, 0.84, 0.80)),
    "aqua": ("aqua.jpg", (0.16, 0.328, 0.96, 0.905)),
    "berry": ("berry.jpg", (0.16, 0.328, 0.96, 0.905)),
    "condoms": ("condoms-17.jpg", None),
}
# квадраты под обложки 1080×1080: вырезаем без надписей, которые зашиты в фото
SQUARES = {
    "neon": ("neon-jungle.jpg", (0.104, 0.33, 0.895, 0.905)),
    "kaspi": ("game-light.jpg", (0.153, 0.28, 0.847, 0.80)),
    "berry": ("berry.jpg", (0.133, 0.33, 0.9, 0.905)),
    "aqua": ("aqua.jpg", (0.133, 0.33, 0.9, 0.905)),
}


def cut(src, box):
    im = Image.open(SRC / src).convert("RGB")
    if box:
        w, h = im.size
        im = im.crop((round(box[0] * w), round(box[1] * h), round(box[2] * w), round(box[3] * h)))
    return im


OG.mkdir(parents=True, exist_ok=True)
for name, (src, box) in CARDS.items():
    im = cut(src, box)
    im.thumbnail((720, 720), Image.LANCZOS)
    im.save(OUT / f"{name}.jpg", quality=82, optimize=True, progressive=True)
    print("card", name, im.size, (OUT / f"{name}.jpg").stat().st_size // 1024, "KB")
for name, (src, box) in SQUARES.items():
    im = cut(src, box)
    side = min(im.size)
    x = (im.width - side) // 2
    im = im.crop((x, 0, x + side, side)).resize((1080, 1080), Image.LANCZOS)
    im.save(OG / f"{name}.jpg", quality=92)
    print("square", name, side, "->1080")
