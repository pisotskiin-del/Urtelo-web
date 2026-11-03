"""Сверка итогов расчёта новой программы со старой (potreb.dbf).

Сравнивает по каждому лицевому поля итогов расчёта (как на странице «Итоги
расчета») и пишет Excel: лист «Итоги» — суммы по городам в обеих программах и
разница, лист «Расхождения» — лицевые, у которых хоть одно поле отличается
больше чем на 0,01, рядом с исходными данными карточки из обеих программ.
Расчёт в обеих программах должен быть выполнен за один и тот же месяц.
"""

import datetime
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from catalogs.models import Danrasch, Potreb

from .obnovit_iz_staroj import prochitat

ITOGI = [
    ("nach_otpr", "Начислено по прибору"), ("nach_otnag", "Начислено по расчету"),
    ("nac_pogaz", "Начислено по факту"), ("poter_pr", "Потери по прибору"), ("poter_nag", "Потери по нагрузке"),
    ("gkl_perer", "Перерасчет"), ("nach_otopl", "Отопление, факт. потребление"), ("nach_gvs", "ГВС"),
    ("poter_gvs", "Тепловые потери ГВС"), ("nac_vsego", "Предъявлено к оплате"),
]
# Исходные данные карточки: помогают понять, откуда расхождение.
ISHODNYE = [
    ("d_stat", "Статус дог."), ("tip_rasot", "Способ расчета"), ("tip_rasgvs", "Расчет ГВС"),
    ("pok_new", "Показ. наст."), ("pok_old", "Показ. пред."), ("koef_pok", "Коэф. прибора"),
    ("pok_newg", "ГВС наст."), ("pok_oldg", "ГВС пред."), ("dnotop", "Дни отоп."), ("q_otoppr", "Нагрузка"),
    ("dn_pereras", "Дни перерасч."),
]
POROG = Decimal("0.01")


def n(v):
    return Decimal(v) if v is not None else Decimal(0)


class Command(BaseCommand):
    help = "Сверить итоги расчёта со старой программой и записать Excel."

    def add_arguments(self, parser):
        parser.add_argument("--dir", default=settings.DBF_SOURCE_DIR, help="Папка dbf старой программы")
        parser.add_argument("--out", default="", help="Файл Excel (по умолчанию dokumenty\\sverka\\...)")
        parser.add_argument("--otkryt", action="store_true", help="Открыть файл после записи (Windows)")

    def handle(self, *args, **opts):
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill
        papka = opts["dir"] or ""
        if not Path(papka).is_dir():
            raise CommandError(f"Нет папки {papka}")
        polya = [k for k, _ in ITOGI] + [k for k, _ in ISHODNYE]
        staroe = prochitat(Potreb, papka, "potreb_id", polya + ["cod_gor_id"])
        goroda_st = prochitat(Danrasch, papka, "cod_gorod", ["nom_mes", "god"])
        goroda = {d.cod_gorod: d for d in Danrasch.objects.exclude(cod_gorod=None)}
        for kod, d in goroda.items():
            s = goroda_st.get(kod) or {}
            if (s.get("nom_mes"), s.get("god")) != (d.nom_mes, d.god):
                self.stdout.write(self.style.WARNING(
                    f"{d.name_gorod}: месяц в старой программе {s.get('nom_mes')}.{s.get('god')}, "
                    f"в новой {d.nom_mes}.{d.god} — сверка участка будет неточной"))

        novoe = {p.potreb_id: p for p in Potreb.objects.all()}
        summy = {}   # (город, поле) -> [старая, новая]
        rasx = []
        for pid in sorted(set(novoe) | set(staroe)):
            p, s = novoe.get(pid), staroe.get(pid)
            gor = p.cod_gor_id if p is not None else (s or {}).get("cod_gor_id")
            raz = False
            for k, _ in ITOGI:
                # В итоги входят только рассчитанные договоры: в старой программе
                # статус 60, в новой 60 и 62 (страница «Итоги расчета»).
                a = n(s.get(k)) if s is not None and s.get("d_stat") == 60 else Decimal(0)
                b = n(getattr(p, k)) if p is not None and p.d_stat in (60, 62) else Decimal(0)
                ss = summy.setdefault((gor, k), [Decimal(0), Decimal(0)])
                ss[0] += a
                ss[1] += b
                raz |= abs(a - b) > POROG
            if raz:
                rasx.append((pid, p, s))

        wb = Workbook()
        ws = wb.active
        ws.title = "Итоги"
        bold = Font(bold=True)
        ws.append(["Показатель"] + [x for kod in sorted(goroda) for x in
                                    (f"{goroda[kod].name_gorod}: старая", "новая", "разница")])
        for c in ws[1]:
            c.font = bold
        for k, t in ITOGI:
            row = [t]
            for kod in sorted(goroda):
                a, b = summy.get((kod, k), [Decimal(0), Decimal(0)])
                row += [float(a), float(b), float(b - a)]
            ws.append(row)
        ws.column_dimensions["A"].width = 32

        ws2 = wb.create_sheet("Расхождения")
        zag = ["Л/№", "Город", "Наименование", "Объект"]
        for _, t in ITOGI:
            zag += [f"{t}: старая", "новая"]
        for _, t in ISHODNYE:
            zag += [f"{t}: старая", "новая"]
        ws2.append(zag)
        for c in ws2[1]:
            c.font = bold
        krasn = PatternFill("solid", fgColor="FFD7D7")
        for pid, p, s in rasx:
            s = s or {}
            gor = goroda.get(p.cod_gor_id if p else s.get("cod_gor_id"))
            row = [pid, gor.name_gorod if gor else "",
                   (p.name_potre or "").strip() if p else "нет в новой программе",
                   (p.nameobakt or "").strip() if p else ""]
            otmetit = []
            itogi = {k for k, _ in ITOGI}
            for k, _ in ITOGI + ISHODNYE:
                a, b = s.get(k), getattr(p, k) if p is not None else None
                if abs(n(a) - n(b)) > (POROG if k in itogi else 0):
                    otmetit.append(len(row) + 2)
                row += [float(a) if isinstance(a, Decimal) else a, float(b) if isinstance(b, Decimal) else b]
            ws2.append(row)
            for col in otmetit:
                ws2.cell(row=ws2.max_row, column=col).fill = krasn
        ws2.freeze_panes = "E2"

        if opts["out"]:
            out = Path(opts["out"])
        else:
            from abonents.pdf import base_dir
            out = base_dir() / "sverka" / f"sverka_rascheta_{datetime.datetime.now():%Y-%m-%d_%H%M%S}.xlsx"
        out.parent.mkdir(parents=True, exist_ok=True)
        wb.save(out)
        self.stdout.write(f"Лицевых с расхождениями: {len(rasx)}")
        for kod in sorted(goroda):
            a, b = summy.get((kod, "nac_vsego"), [0, 0])
            self.stdout.write(f"{goroda[kod].name_gorod}: предъявлено к оплате — старая {a}, новая {b}, разница {b - a}")
        self.stdout.write(self.style.SUCCESS(f"Файл сверки: {out}"))
        if opts["otkryt"]:
            import os
            try:
                os.startfile(str(out))
            except (AttributeError, OSError) as e:
                self.stdout.write(f"Не удалось открыть файл: {e}")
