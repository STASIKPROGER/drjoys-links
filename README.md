# DR.JOYS — ссылки для шапки Instagram

Хаб `/` со всеми товарами и страницы-переходы `/<slug>/` с фирменными обложками для превью ссылок в Instagram.

- `links.json` — куда ведёт каждая ссылка (`base` — адрес сайта)
- `site/` — исходник хаба и картинки, `tools/og.html` — обложки 1080×1080
- `tools/crop.py` — нарезка фото из `src/`, `tools/build.py` — сборка в `docs/` (её отдаёт GitHub Pages)

Сборка: python с playwright и pillow → `python tools/crop.py && python tools/build.py`, затем push в ветку `gh-pages`.
