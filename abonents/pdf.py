"""PDF документов абоненту на сервере (вместо виртуального принтера Bullzip
старой программы) — для рассылки и хранения по месяцам.

PDF строится библиотекой xhtml2pdf из тех же шаблонов, что страница
документа. Для кириллицы нужен шрифт TrueType: TEPLO_PDF_FONT (и
TEPLO_PDF_FONT_BOLD), иначе Arial из Windows или DejaVu Sans в Linux.
"""

import io
from pathlib import Path

from django.conf import settings
from django.template.loader import render_to_string

FONTS = [
    (r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\arialbd.ttf"),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
]

GORODA = {1: "ryb", 2: "dub", 3: "kam"}   # папки, как в старой программе (Akt_potreb\ryb\…)
VIDY = {"schet": "Информация-счёт", "akt": "Акт о фактическом потреблении"}


def _font():
    regular = getattr(settings, "TEPLO_PDF_FONT", "")
    bold = getattr(settings, "TEPLO_PDF_FONT_BOLD", "") or regular
    if regular and Path(regular).exists():
        return regular, bold if Path(bold).exists() else regular
    for r, b in FONTS:
        if Path(r).exists():
            return r, b if Path(b).exists() else r
    return None, None


def html(doks, vid, context):
    regular, bold = _font()
    return render_to_string("abonents/dokument_pdf.html", {
        **context, "doks": doks, "vid": vid, "title": VIDY[vid],
        "font": Path(regular).as_posix() if regular else "", "font_bold": Path(bold).as_posix() if bold else "",
    })


def render(doks, vid, context):
    """PDF (bytes) документов vid по списку документов doks."""
    from xhtml2pdf import pisa
    out = io.BytesIO()
    regular, _ = _font()
    # Базовый каталог документа — каталог шрифта: новые версии xhtml2pdf читают
    # файлы только из него.
    base = str(Path(regular).parent / "dokument.html") if regular else ""
    result = pisa.CreatePDF(html(doks, vid, context), dest=out, encoding="utf-8", path=base)
    if result.err:
        raise RuntimeError("Не удалось построить PDF")
    return out.getvalue()


def filename(dok, vid):
    """<вид>_<№ договора>_<л/№>.pdf (в старой программе <№ договора>_<л/№>.PDF)."""
    return f"{'akt' if vid == 'akt' else 'schet'}_{dok.filename}.pdf"


def folder(dok):
    """Папка документов месяца: TEPLO_DOC_DIR\\<участок>\\<год>\\<месяц>, как
    D:\\Teplo_dog\\Akt_potreb\\<город>\\<год>\\<месяц> в старой программе."""
    base = Path(getattr(settings, "TEPLO_DOC_DIR", "") or Path(settings.BASE_DIR) / "dokumenty")
    return base / GORODA.get(dok.gorod.cod_gorod, str(dok.gorod.cod_gorod)) / str(dok.god) / str(dok.mes)


def save(dok, vid, context):
    """Построить PDF одного документа и сохранить в папку месяца. Возвращает путь."""
    path = folder(dok) / filename(dok, vid)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(render([dok], vid, context))
    return path
