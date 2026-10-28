"""Проверка вёрстки хаба на ширинах телефонов: ничего не вылезает за экран, текст не обрезан.

Запуск: <python с playwright> tools/check.py [url] [скриншот.png]
По умолчанию проверяет docs/index.html и кладёт полный скриншот 390px в build/hub.png.
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = sys.argv[1] if len(sys.argv) > 1 else (ROOT / "docs" / "index.html").as_uri()
SHOT = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "build" / "hub.png"

JS = """() => {
  const vw = document.documentElement.clientWidth, out = [];
  for (const el of document.querySelectorAll('h1,h2,h3,.tag,.btn,.mp a,.order,p,b,small')) {
    if (el.closest('.swim')) continue;
    const r = el.getBoundingClientRect();
    if (r.right > vw + 0.5 || r.left < -0.5) out.push('OUT ' + el.textContent.trim().slice(0, 30));
    const cs = getComputedStyle(el);
    if (el.scrollWidth > el.clientWidth + 1 && cs.display !== 'inline' && cs.overflowX === 'visible')
      out.push('CLIP ' + el.textContent.trim().slice(0, 30) + ' ' + el.scrollWidth + '>' + el.clientWidth);
  }
  return {sw: document.documentElement.scrollWidth, out};
}"""

with sync_playwright() as p:
    browser = p.chromium.launch()
    bad = 0
    for w in (360, 390, 430):
        page = browser.new_page(viewport={"width": w, "height": 844}, device_scale_factor=2)
        page.goto(URL, wait_until="load")
        # пролистываем, чтобы наклейки и карточки отыграли появление
        for y in range(0, 6000, 400):
            page.evaluate(f"scrollTo(0,{y})")
            page.wait_for_timeout(120)
        page.evaluate("scrollTo(0,0)")
        page.wait_for_timeout(900)
        r = page.evaluate(JS)
        print(w, "scrollWidth", r["sw"], "проблем:", len(r["out"]))
        for o in r["out"][:10]:
            print("   ", o)
        bad += len(r["out"]) + (r["sw"] > w)
        if w == 390:
            SHOT.parent.mkdir(exist_ok=True)
            page.screenshot(path=str(SHOT), full_page=True)
        page.close()
    browser.close()
sys.exit(1 if bad else 0)
