"""Отчеты старой программы: форма otchet (кнопки «Отчеты») и меню «Печать»
(pasp_got.prg, potreb_koteln.prg, potreb_kategor.prg). Каждый отчет —
функция, которая по городу и параметрам строит Report: заголовок, таблицы
с группами, итогами по группам и общим итогом, подписи. Один и тот же
Report показывается на экране, печатается и выгружается в Excel."""

import datetime
from dataclasses import dataclass, field
from decimal import Decimal

from django.db.models import Q

from catalogs.models import Akcept, Danrasch, GvsKot, Kategorpot, Limit, Minist, Potreb

SIGNATURES = [
    "Исполнитель _________________________________",
    "Начальник ОУиРТЭ __________________________________ Елфимова И.Ю.",
]
FILIAL = 'ПЕРЕЧЕНЬ ПОТРЕБИТЕЛЕЙ МГУП "ТИРАСТЕПЛОЭНЕРГО" ФИЛИАЛ В Г.РЫБНИЦА'


@dataclass
class Col:
    title: str
    kind: str = "text"      # text, int, num, date
    places: int = 3
    total: bool = False     # суммировать в итогах


@dataclass
class Section:
    title: str = ""
    rows: list = field(default_factory=list)
    foot: list = None       # строка итога группы


@dataclass
class Table:
    cols: list
    sections: list
    groups: list = None     # верхняя строка шапки: [(заголовок, колонок)]
    total: list = None      # строка общего итога
    title: str = ""


@dataclass
class Report:
    title: str
    lines: list
    tables: list
    notes: list = field(default_factory=list)
    signatures: list = field(default_factory=list)
    landscape: bool = False


@dataclass
class ReportDef:
    key: str
    title: str
    group: str
    build: object
    options: list = field(default_factory=list)   # [(имя, подпись, [(значение, подпись)])]
    per_city: bool = True
    hint: str = ""


def n(value):
    return value if value is not None else Decimal(0)


def _sum_row(cols, rows, label, label_col=None):
    """Строка итога: подпись в первой текстовой колонке (или label_col),
    суммы в колонках с total=True."""
    if label_col is None:
        label_col = next((i for i, c in enumerate(cols) if c.kind == "text"), 0)
    out = [None] * len(cols)
    for i, c in enumerate(cols):
        if c.total:
            out[i] = sum((n(r[i]) for r in rows), Decimal(0))
    out[label_col] = label
    return out


def _numbered(rows):
    return [[i] + r for i, r in enumerate(rows, 1)]


def _city_lines(city, month=True):
    lines = [f"г. {(city.name_gorod or '').strip()}"]
    if month:
        lines.append(f"за {(city.name_mes or '').strip()} {city.god} г.")
    return lines


def _kategor():
    return dict(Kategorpot.objects.values_list("id_kotegor", "name_kateg"))


def _akcept():
    return dict(Akcept.objects.values_list("id_akc", "name_akc"))


def _grouped(items, key, title, build_row, cols):
    """Разбивает записи на группы по key (порядок — как в items) и
    добавляет итог каждой группы."""
    sections, current, keyval = [], None, object()
    for item in items:
        k = key(item)
        if k != keyval:
            current = Section(title(k))
            sections.append(current)
            keyval = k
        current.rows.append(build_row(item))
    for s in sections:
        for i, r in enumerate(s.rows, 1):
            r[0] = i
        s.foot = _sum_row(cols, s.rows, f"всего: {s.title}", label_col=3)
    return sections


# --- Отчеты формы «Отчеты» ---------------------------------------------------

def ot_kateg(city, opts):
    """Кнопка «Распределение по бюджетам» (отчет OT_KATEG): начислено за месяц
    по категориям потребителей. Ветка с предоплатой (pr_xozr) не переносится:
    предоплата не используется."""
    qs = Potreb.objects.filter(cod_gor=city.cod_gorod).exclude(id_katabon=3).exclude(nac_vsego=0).exclude(nac_vsego=None)
    kat = opts.get("kateg")
    if kat:
        qs = qs.filter(id_kategor=int(kat))
    else:
        qs = qs.filter(nom_dog__gt=0)
    names, akc = _kategor(), _akcept()
    cols = [Col("№ п/п", "int"), Col("Лиц. №", "int"), Col("Код бух.", "int"), Col("Абонент"), Col("Акцепт"),
            Col("Выстав. аванс", "num", total=True), Col("Отпуск (Гкал)", "num", total=True),
            Col("К оплате (Гкал)", "num", total=True)]
    sections = _grouped(
        qs.order_by("id_kategor", "potreb_id"), lambda p: p.id_kategor,
        lambda k: (names.get(k) or f"Категория {k}").upper(),
        lambda p: [0, p.potreb_id, p.cod_buhg, p.name_potre, akc.get(p.accept), n(p.predopl),
                   n(p.nac_vsego) + n(p.predopl), n(p.nac_vsego)],
        cols)
    rows = [r for s in sections for r in s.rows]
    return Report("ОТПУСК ТЕПЛОВОЙ ЭНЕРГИИ ДЛЯ АБОНЕНТОВ", _city_lines(city),
                  [Table(cols, sections, total=_sum_row(cols, rows, "ИТОГО:", label_col=4))],
                  signatures=SIGNATURES)


def ot_minist(city, opts):
    """Кнопка «Расшифровка по министерствам»: республиканский бюджет по
    министерствам."""
    qs = Potreb.objects.filter(cod_gor=city.cod_gorod, nom_dog__gt=0, id_kategor=3).exclude(id_katabon=3)
    names, akc = dict(Minist.objects.values_list("cod_minist", "name_minis")), _akcept()
    cols = [Col("№ п/п", "int"), Col("Код АС", "int"), Col("Код бух.", "int"), Col("Абонент"), Col("Акцепт"),
            Col("Выстав. аванс", "num", total=True), Col("Отпуск (Гкал)", "num", total=True),
            Col("К оплате (Гкал)", "num", total=True)]
    sections = _grouped(
        qs.order_by("cod_minist", "potreb_id"), lambda p: p.cod_minist_id,
        lambda k: (names.get(k) or "Министерство не указано").strip().upper(),
        lambda p: [0, p.cod_ac, p.cod_buhg, p.name_potre, akc.get(p.accept), n(p.predopl),
                   n(p.nac_vsego), n(p.nac_vsego) - n(p.predopl)],
        cols)
    rows = [r for s in sections for r in s.rows]
    return Report("РЕСПУБЛИКАНСКИЙ БЮДЖЕТ", ["Расшифровка по министерствам"] + _city_lines(city),
                  [Table(cols, sections, total=_sum_row(cols, rows, "ИТОГО:", label_col=4))],
                  signatures=SIGNATURES)


def ved_potreb(city, opts):
    """Кнопка «Ведомость по приборам»: абоненты с показаниями прибора, у
    которых есть (или нет) начисления по разнице показаний."""
    qs = Potreb.objects.filter(cod_gor=city.cod_gorod, pok_new__gt=0)
    nenach = opts.get("vid") == "nenach"
    qs = qs.filter(Q(nach_otpr__lte=0) | Q(nach_otpr=None)) if nenach else qs.filter(nach_otpr__gt=0)
    cols = [Col("№ догов.", "int"), Col("Наименование потребителя"), Col("разн. показаний", "num", 2, total=True)]
    rows = [[p.nom_dog, p.name_potre, n(p.nach_otpr)] for p in qs.order_by("nom_dog", "potreb_id")]
    return Report("Ведомость начисления по приборам", _city_lines(city) + ["не начислено" if nenach else "начислено"],
                  [Table(cols, [Section(rows=rows)], total=_sum_row(cols, rows, "Итого:"))])


def nach_nul(city, opts):
    """Кнопка «Без начисления»: абоненты, у которых нет начисления за
    отопление (или за ГВС)."""
    name = "nach_gvs" if opts.get("vid") == "gvs" else "nach_otopl"
    qs = Potreb.objects.filter(cod_gor=city.cod_gorod).filter(Q(**{f"{name}__lte": 0}) | Q(**{name: None}))
    cols = [Col("№ дог.", "int"), Col("Наименование потребителей"), Col("предоплата", "num"),
            Col("начисл. отопление", "num"), Col("Начислено ГВС", "num")]
    rows = [[p.nom_dog, p.name_potre, n(p.predopl), n(p.nach_otopl), n(p.nach_gvs)]
            for p in qs.order_by("nom_dog", "potreb_id")]
    return Report("Список потребителей без начисления",
                  _city_lines(city) + ["по ГВС" if name == "nach_gvs" else "по отоплению"],
                  [Table(cols, [Section(rows=rows)])], notes=[f"Всего: {len(rows)}"])


def _koteln():
    return {k.id_kot: k.name_kot for k in GvsKot.objects.exclude(id_kot=None)}


KOT_KATEG = [(4, "население ведомственное"), (6, "население абонентское"), (2, "местный бюджет"),
             (3, "республиканский бюджет"), (7, "ОСКиИОД"), (1, "хозрасчет")]


def p_kot1(city, opts):
    """Кнопка «Потребление по котельным» (p_kot1): начислено за ГВС и
    отопление по котельным и категориям. Категория «Население хозрасчётное»
    отдельной колонки не имеет и входит только во «Всего», как в старом
    отчете."""
    names = _koteln()
    data = {}
    for p in Potreb.objects.filter(cod_gor=city.cod_gorod, id_koteln__gt=0).order_by("id_koteln"):
        if p.id_koteln not in names:
            continue
        row = data.setdefault(p.id_koteln, {})
        for k in (p.id_kategor, "all"):
            g, o = row.get(k, (Decimal(0), Decimal(0)))
            row[k] = (g + n(p.nach_gvs), o + n(p.nach_otopl))
    cols = [Col("Наименование котельной")]
    groups = [("", 1)]
    for _, title in KOT_KATEG + [(None, "Всего")]:
        cols += [Col("ГВС", "num", 2, total=True), Col("Отопл.", "num", 2, total=True)]
        groups.append((title, 2))
    rows = []
    for kot, row in data.items():
        r = [(names[kot] or "")[3:].strip()]
        for k, _ in KOT_KATEG + [("all", "")]:
            r += list(row.get(k, (Decimal(0), Decimal(0))))
        rows.append(r)
    total = _sum_row(cols, rows, "Итого")
    vsego = (total[-2] or 0) + (total[-1] or 0)
    return Report("ФАКТИЧЕСКОЕ ПОТРЕБЛЕНИЕ ПО КОТЕЛЬНЫМ", [" ".join(_city_lines(city))],
                  [Table(cols, [Section(rows=rows)], groups=groups, total=total)],
                  notes=[f"ВСЕГО ПОТРЕБЛЕНИЕ ПО КОТЕЛЬНЫМ: {vsego:.2f} ГКал"],
                  signatures=SIGNATURES, landscape=True)


def p_kot2(city, opts):
    """Кнопка «Нагрузка по котельным» (p_kot2): часовая нагрузка по
    котельным, население (абонентское) отдельно от прочих."""
    names = _koteln()
    data = {}
    for p in Potreb.objects.filter(cod_gor=city.cod_gorod).order_by("id_koteln"):
        if p.id_koteln not in names:
            continue
        r = data.setdefault(p.id_koteln, [Decimal(0)] * 4)
        i = 0 if p.id_kategor == 6 else 2
        r[i] += n(p.q_otoppr)
        r[i + 1] += n(p.q_gvs)
    cols = [Col("Наименование котельной")] + [Col(t, "num", 4, total=True) for t in
                                               ("Отопл.", "ГВС", "Отопл.", "ГВС", "Отопл.", "ГВС", "ВСЕГО")]
    groups = [("", 1), ("Население", 2), ("Прочие", 2), ("", 3)]
    rows = [[names[k], a, b, c, d, a + c, b + d, a + b + c + d] for k, (a, b, c, d) in data.items()]
    total = _sum_row(cols, rows, "Итого")
    return Report("РАСПРЕДЕЛЕННАЯ НАГРУЗКА ПО КОТЕЛЬНЫМ", _city_lines(city),
                  [Table(cols, [Section(rows=rows)], groups=groups, total=total)],
                  notes=[f"ВСЕГО НАГРУЗКА ПО КОТЕЛЬНЫМ: {total[-1]:.4f} Гкал/час"],
                  signatures=SIGNATURES)


def nag_kateg(city, opts):
    """Кнопка «Нагрузка по категориям» (nag_kateg): часовая нагрузка на
    отопление абонентов по категориям."""
    names = _kategor()
    cols = [Col("№ п/п", "int"), Col("Л/Н", "int"), Col("Абонент"), Col("Нагрузка, Гкал/час", "num", 5, total=True)]
    qs = Potreb.objects.filter(cod_gor=city.cod_gorod, q_otoppr__gt=0).order_by("id_kategor", "potreb_id")
    sections = []
    for s in _grouped(qs, lambda p: p.id_kategor, lambda k: (names.get(k) or f"Категория {k}").upper(),
                      lambda p: [0, p.potreb_id, p.name_potre, n(p.q_otoppr)], cols):
        s.foot = _sum_row(cols, s.rows, f"всего: {s.title}", label_col=2)
        sections.append(s)
    rows = [r for s in sections for r in s.rows]
    return Report("ТЕПЛОВАЯ НАГРУЗКА ПО КАТЕГОРИЯМ ПОТРЕБИТЕЛЕЙ", _city_lines(city),
                  [Table(cols, sections, total=_sum_row(cols, rows, "ИТОГО:", label_col=2))],
                  signatures=SIGNATURES)


def limit(city, opts):
    """Кнопка «Превышение лимита»: таблица limit, её заполняет расчет."""
    cols = [Col("№ лиц.сч.", "int"), Col("Потребитель"), Col("Текущее начисление", "num"),
            Col("Установлен лимит", "num"), Col("Начислено с начала фин. года", "num"), Col("Коментарий")]
    rows = [[x.potreb_id, x.name_dog, n(x.nac_vsego), n(x.vd_limit), n(x.nach_finan), x.koment]
            for x in Limit.objects.order_by("potreb_id")]
    return Report("Список потребителей с заканчивающимся лимитом", [_today()],
                  [Table(cols, [Section(rows=rows)])])


# --- Меню «Печать» ------------------------------------------------------------

def _today():
    return datetime.date.today().strftime("%d.%m.%Y")


def _name_glav(p):
    name, glav = (p.name_potre or "").strip(), (p.glav_potre or "").strip()
    return f"{name}  ({glav})" if glav else name


def pasp_got(city, opts):
    """«Печать → Паспорта готовности» (pasp_got.prg): объекты хозрасчета и
    бюджета с отопительной нагрузкой и даты паспортов готовности. Колонки
    «Дата запуска» и «Количество дней отпуска» в старом отчете пустые — их
    заполняют от руки."""
    qs = Potreb.objects.filter(cod_gor=city.cod_gorod, id_kategor__lt=4, q_otoppr__gt=0).order_by("potreb_id")
    cols = [Col("Лиц.№", "int"), Col("Наименование потребителя"), Col("Паспорт готовности", "date"),
            Col("Дата запуска"), Col("Количество дней отпуска"), Col("Адрес расположения объекта")]
    recs = list(qs)
    rows = [[p.potreb_id, _name_glav(p), p.pasp_got, "", "",
             f"ул. {(p.adres_sd or '').strip()}. дом {(p.oba_dom or '').strip()}. {(p.oba_kv or '').strip()}"]
            for p in recs]
    scols = [Col(""), Col("Количество объектов", "int", total=True), Col("С паспортами готовности", "int", total=True)]
    srows = [[title, sum(1 for p in recs if p.id_kategor == k), sum(1 for p in recs if p.id_kategor == k and p.pasp_got)]
             for k, title in ((1, "Хозрасчет"), (2, "Местный бюджет"), (3, "Республиканский бюджет"))]
    return Report(FILIAL, [f"участок г.{(city.name_gorod or '').strip()}", _today()],
                  [Table(cols, [Section(rows=rows)], title=""),
                   Table(scols, [Section(rows=srows)], total=_sum_row(scols, srows, "Итого по городу"))],
                  landscape=True)


# Объекты, которые старая программа не включала в список по котельным
# (potreb_koteln.prg): Рыбница — л/№ 173, 276, 277; Дубоссары — 263–275;
# Каменка — 338–341.
KOTELN_EXCLUDE = {1: {173, 276, 277}, 2: set(range(263, 276)), 3: set(range(338, 342))}


def potreb_koteln(city, opts):
    """«Печать → Потребители по котельным» (potreb_koteln.prg)."""
    names = _koteln()
    skip = KOTELN_EXCLUDE.get(city.cod_gorod, set())
    cols = [Col("Лиц.№", "int"), Col("Наименование потребителя"), Col("Адрес"),
            Col("Тепловая нагр. Гкал/час", "num", 4, total=True), Col("Примечание")]
    sections = []
    for p in Potreb.objects.filter(cod_gor=city.cod_gorod).order_by("id_koteln", "potreb_id"):
        if p.id_koteln not in names or p.potreb_id in skip:
            continue
        if not sections or sections[-1].kot != p.id_koteln:
            s = Section(f"Участок — {names[p.id_koteln]}")
            s.kot = p.id_koteln
            sections.append(s)
        sections[-1].rows.append([p.potreb_id, _name_glav(p), p.adres_sd, n(p.q_otoppr), ""])
    for s in sections:
        s.foot = _sum_row(cols, s.rows, f"всего: {names[s.kot]}")
    scols = [Col("Список котельных"), Col("Тепловая нагр. Гкал/час", "num", 4, total=True)]
    srows = [[names[s.kot], s.foot[3]] for s in sections]
    return Report(FILIAL, [f"участок г.{(city.name_gorod or '').strip()}", _today()],
                  [Table(cols, sections), Table(scols, [Section(rows=srows)], total=_sum_row(scols, srows, "ИТОГО:"))],
                  landscape=True)


KATEGOR_COLS = [(1, "Хозрасчет"), (2, "Местный бюджет"), (3, "Респуб-ий бюджет"),
                (4, "Население бюджет"), (6, "Население абонентское")]


def potreb_kategor(city, opts):
    """«Печать → Нагрузки по категориям» (potreb_kategor.prg): часовая
    нагрузка на отопление по участкам и категориям. Категории 5 и 7 в
    старом отчете не показаны и во «Всего» не входят."""
    sums = {}
    for p in Potreb.objects.exclude(q_otoppr=None).only("cod_gor", "id_kategor", "q_otoppr"):
        key = (p.cod_gor_id, p.id_kategor)
        sums[key] = sums.get(key, Decimal(0)) + p.q_otoppr
    cols = [Col("Участок")] + [Col(t, "num", 5, total=True) for _, t in KATEGOR_COLS] + [Col("Всего по участку", "num", 5, total=True)]
    rows = []
    for c in Danrasch.objects.exclude(cod_gorod=None).order_by("cod_gorod"):
        vals = [sums.get((c.cod_gorod, k), Decimal(0)) for k, _ in KATEGOR_COLS]
        rows.append([f"г.{(c.name_gorod or '').strip()}"] + vals + [sum(vals, Decimal(0))])
    return Report("Часовые нагрузки по категориям потребителей", [_today()],
                  [Table(cols, [Section(rows=rows)], total=_sum_row(cols, rows, "Всего по категориям потреб."))])


VID_PRIBOR = [("nach", "Начислено"), ("nenach", "Не начислено")]
VID_NUL = [("otopl", "Отопление"), ("gvs", "ГВС")]

REPORTS = [
    ReportDef("ot_kateg", "Распределение по бюджетам", "Начисление", ot_kateg,
              options=[("kateg", "Категория", None)], hint="Отпуск тепловой энергии по категориям потребителей"),
    ReportDef("ot_minist", "Расшифровка по министерствам", "Начисление", ot_minist,
              hint="Республиканский бюджет по министерствам"),
    ReportDef("ved_potreb", "Ведомость по приборам", "Начисление", ved_potreb,
              options=[("vid", "Показать", VID_PRIBOR)], hint="Начисление по разнице показаний приборов"),
    ReportDef("nach_nul", "Без начисления", "Начисление", nach_nul,
              options=[("vid", "Услуга", VID_NUL)], hint="Список потребителей без начисления"),
    ReportDef("limit", "Превышение лимита", "Начисление", limit, per_city=False,
              hint="Заканчивающийся лимит (по последнему расчету)"),
    ReportDef("p_kot1", "Потребление по котельным", "Котельные", p_kot1,
              hint="Фактическое потребление ГВС и отопления по котельным"),
    ReportDef("p_kot2", "Нагрузка по котельным", "Котельные", p_kot2,
              hint="Распределенная часовая нагрузка по котельным"),
    ReportDef("nag_kateg", "Нагрузка по категориям", "Котельные", nag_kateg,
              hint="Тепловая нагрузка абонентов по категориям"),
    ReportDef("pasp_got", "Паспорта готовности", "Печать", pasp_got,
              hint="Перечень потребителей с паспортами готовности"),
    ReportDef("potreb_koteln", "Потребители по котельным", "Печать", potreb_koteln,
              hint="Перечень потребителей и нагрузка по котельным"),
    ReportDef("potreb_kategor", "Часовые нагрузки по категориям", "Печать", potreb_kategor, per_city=False,
              hint="Нагрузка по участкам и категориям потребителей"),
]
BY_KEY = {r.key: r for r in REPORTS}


def options_for(rdef):
    """Варианты выбора для параметров отчета (категории берутся из справочника)."""
    out = []
    for name, label, choices in rdef.options:
        if choices is None:
            choices = [("", "Все категории")] + [(str(k), v) for k, v in sorted(_kategor().items())]
        out.append((name, label, choices))
    return out


def build(rdef, city, params):
    opts = {}
    for name, _, choices in options_for(rdef):
        value = params.get(name, choices[0][0])
        opts[name] = value if value in {c for c, _ in choices} else choices[0][0]
    return rdef.build(city, opts), opts


def to_xlsx(report, out):
    """Выгрузка отчета в Excel."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, Side
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = "Отчет"
    thin = Side(style="thin", color="999999")
    box = Border(left=thin, right=thin, top=thin, bottom=thin)
    bold = Font(bold=True)
    width = max(len(t.cols) for t in report.tables)
    r = 1
    ws.cell(r, 1, report.title).font = Font(bold=True, size=13)
    for line in report.lines:
        r += 1
        ws.cell(r, 1, line)
    widths = {}

    def put(row, values, cols, font=None):
        for i, (v, c) in enumerate(zip(values, cols), 1):
            cell = ws.cell(row, i, v)
            cell.border = box
            if font:
                cell.font = font
            if c.kind == "num" and v is not None and v != "":
                cell.number_format = "0." + "0" * c.places if c.places else "0"
            elif c.kind == "date" and v:
                cell.number_format = "DD.MM.YYYY"
            if c.kind == "text":
                widths[i] = max(widths.get(i, 8), min(60, len(str(v or "")) + 2))
            else:
                widths[i] = max(widths.get(i, 8), 14)

    for t in report.tables:
        r += 2
        if t.title:
            ws.cell(r, 1, t.title).font = bold
            r += 1
        if t.groups and any(g for g, _ in t.groups):
            col = 1
            for g, span in t.groups:
                if span > 1:
                    ws.merge_cells(start_row=r, start_column=col, end_row=r, end_column=col + span - 1)
                cell = ws.cell(r, col, g)
                cell.font, cell.alignment, cell.border = bold, Alignment(horizontal="center"), box
                col += span
            r += 1
        for i, c in enumerate(t.cols, 1):
            cell = ws.cell(r, i, c.title)
            cell.font, cell.border = bold, box
            cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        for s in t.sections:
            if s.title:
                r += 1
                ws.cell(r, 1, s.title).font = bold
            for row in s.rows:
                r += 1
                put(r, row, t.cols)
            if s.foot:
                r += 1
                put(r, s.foot, t.cols, bold)
        if t.total:
            r += 1
            put(r, t.total, t.cols, bold)
    for note in report.notes:
        r += 2
        ws.cell(r, 1, note).font = bold
    for sig in report.signatures:
        r += 2
        ws.cell(r, 2, sig)
    for i in range(1, width + 1):
        ws.column_dimensions[get_column_letter(i)].width = widths.get(i, 12)
    if report.landscape:
        ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    wb.save(out)
