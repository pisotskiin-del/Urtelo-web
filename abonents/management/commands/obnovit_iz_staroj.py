"""Обновить данные из старой программы на время параллельной работы.

Из папки DBF старой программы (по умолчанию DBF_SOURCE_DIR, D:\\Teplo_dog\\dbf)
переносятся только исходные данные для расчёта:

- potreb.dbf — показания счётчиков (pok_new, pok_old, date_pok — отопление,
  pok_newg, pok_oldg — ГВС) и дни подачи отопления и ГВС из карточек
  (dnotop, dngvs) у лицевых, которые есть в обеих программах;
- danrasch.dbf — исходные данные для расчёта по городам (t воздуха, расчётная t,
  t коэффициент, дни отопления и ГВС, Q факт, полезный отпуск населению).

Остальное, что правили в новой программе (карточки, коды КРЭДО, начисления),
не трогается; новые лицевые не создаются. Если у участка в программах разный
расчётный месяц, его данные не переносятся. С --proverka только показывает,
что изменится.
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalogs.models import Danrasch, Potreb
from dbfsync.importer import _find_file, column_map, convert
from dbfsync.reader import open_dbf

POLYA_KARTY = ["pok_new", "pok_old", "date_pok", "pok_newg", "pok_oldg", "dnotop", "dngvs"]
POLYA_GORODA = ["t_vozd", "t_proekt", "tkoef", "dnotop", "dngvs", "qpfakt", "gkl_pod", "gkl_bezpod"]


def prochitat(model, papka, klyuch, polya):
    """{ключ: {поле: значение}} из DBF таблицы модели."""
    try:
        path = _find_file(Path(papka), model.dbf_source)
    except FileNotFoundError:
        raise CommandError(f"Нет файла {Path(papka) / model.dbf_source}") from None
    cols = {f.attname: (f, col) for f, col in column_map(model).items()}
    table = open_dbf(path, settings.DBF_ENCODING or None)
    names = {f.name.upper() for f in table.fields}
    polya = [p for p in polya if cols[p][1] in names]
    out = {}
    for rec in table:   # удалённые записи dbfread пропускает
        rec = {k.upper(): v for k, v in rec.items()}
        k = convert(cols[klyuch][0], rec.get(cols[klyuch][1]), table.encoding)
        if k is not None:
            out[k] = {p: convert(cols[p][0], rec.get(cols[p][1]), table.encoding) for p in polya}
    return out


def raznica(obj, novoe):
    return {k: v for k, v in novoe.items() if v != getattr(obj, k)}


class Command(BaseCommand):
    help = ("Обновить из старой программы показания счётчиков, дни отопления в карточках и исходные "
            "данные для расчёта (с --proverka — только показать).")

    def add_arguments(self, parser):
        parser.add_argument("--dir", default=settings.DBF_SOURCE_DIR, help="Папка dbf старой программы")
        parser.add_argument("--proverka", action="store_true", help="Только показать, ничего не записывать")

    def handle(self, *args, **opts):
        papka = opts["dir"] or ""
        if not Path(papka).is_dir():
            raise CommandError(f"Нет папки {papka}")
        self.stdout.write(f"Папка старой программы: {papka}")
        goroda_st = prochitat(Danrasch, papka, "cod_gorod", POLYA_GORODA + ["nom_mes", "god"])
        karty_st = prochitat(Potreb, papka, "potreb_id", POLYA_KARTY)

        goroda, propusk = [], set()
        for d in Danrasch.objects.exclude(cod_gorod=None).order_by("cod_gorod"):
            s = goroda_st.get(d.cod_gorod)
            if s is None:
                continue
            if (s.get("nom_mes"), s.get("god")) != (d.nom_mes, d.god):
                propusk.add(d.cod_gorod)
                self.stdout.write(self.style.WARNING(
                    f"{d.name_gorod}: расчётный месяц в старой программе {s.get('nom_mes')}.{s.get('god')}, "
                    f"в новой {d.nom_mes}.{d.god} — данные участка не переносятся"))
                continue
            raz = raznica(d, {k: s[k] for k in POLYA_GORODA if k in s})
            if raz:
                goroda.append((d, raz))
                self.stdout.write(f"{d.name_gorod}: " + ", ".join(f"{k} {getattr(d, k)} -> {v}" for k, v in raz.items()))

        karty, net = [], 0
        for p in Potreb.objects.only("potreb_id", "name_potre", "cod_gor", *POLYA_KARTY).order_by("potreb_id"):
            s = karty_st.get(p.potreb_id)
            if s is None:
                net += 1
                continue
            if p.cod_gor_id in propusk:
                continue
            raz = raznica(p, {k: s[k] for k in POLYA_KARTY if k in s})
            if raz:
                karty.append((p, raz))
        for p, raz in karty[:50]:
            self.stdout.write(f"Л/№ {p.potreb_id} {(p.name_potre or '').strip()[:40]}: " + ", ".join(
                f"{k} {getattr(p, k)} -> {v}" for k, v in raz.items()))
        if len(karty) > 50:
            self.stdout.write(f"... и ещё {len(karty) - 50}")
        novye = len(set(karty_st) - set(Potreb.objects.values_list("potreb_id", flat=True)))
        self.stdout.write(f"Городов с другими исходными данными: {len(goroda)}; карточек с изменениями: {len(karty)}")
        if net or novye:
            self.stdout.write(f"Лицевых нет в старой программе: {net}; есть только в старой (не переносятся): {novye}")
        if opts["proverka"]:
            self.stdout.write("Проверка: ничего не записано.")
            return
        with transaction.atomic():
            for d, raz in goroda:
                Danrasch.objects.filter(pk=d.pk).update(**raz)
            for p, raz in karty:
                Potreb.objects.filter(pk=p.pk).update(**raz)
        self.stdout.write(self.style.SUCCESS(f"Записано: городов {len(goroda)}, карточек {len(karty)}. "
                                             f"Расчёт в новой программе нужно выполнить заново."))
