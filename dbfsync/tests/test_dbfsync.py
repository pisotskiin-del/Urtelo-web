"""Тесты чтения DBF, генерации моделей и загрузки на тестовых таблицах."""

import io
import shutil
import struct
import tempfile
from pathlib import Path

import dbf as dbf_writer

from django.core.management import CommandError, call_command
from django.test import TestCase

from dbfsync.testapp.models import Objekt, Org
from dbfsync.importer import import_table
from dbfsync.reader import detect_encoding, open_dbf
from dbfsync.schema import apply_relations, inspect_directory, load_labels, render_models

DEMO = Path(__file__).resolve().parent / "fixtures"


class DbfTests(TestCase):
    def test_inspect_builds_valid_code(self):
        tables = inspect_directory(DEMO, labels=load_labels(DEMO / "labels.json"))
        code = render_models(tables)
        compile(code, "models.py", "exec")
        org = next(t for t in tables if t.class_name == "Org")
        self.assertFalse(org.in_dbc)
        self.assertEqual(org.label, "Организации")
        self.assertEqual(org.encoding, "cp866")

    def test_relations_render_foreign_key_and_unique(self):
        tables = inspect_directory(DEMO)
        skipped = apply_relations(tables, {
            "foreign_keys": [
                {"table": "OBJEKT", "field": "KOD_ORG", "to_table": "ORG", "to_field": "KOD"},
                {"table": "OBJEKT", "field": "NET", "to_table": "ORG", "to_field": "KOD"},
            ],
        })
        self.assertEqual(skipped, ["OBJEKT.NET -> ORG.KOD"])
        code = render_models(tables)
        compile(code, "models.py", "exec")
        self.assertIn('kod_org = models.ForeignKey("Org", models.PROTECT, verbose_name="KOD_ORG", '
                      'to_field="kod", db_column="kod_org", null=True, blank=True)', code)
        self.assertIn('kod = models.IntegerField("KOD", unique=True', code)

    def test_import_matches_record_count(self):
        call_command("dbf_import", "--app", "dbfsync_testapp", "--dir", str(DEMO), stdout=open("/dev/null", "w"))
        self.assertEqual(Org.objects.count(), 3)
        org = Org.objects.get(kod=1)
        self.assertEqual(org.naim, 'ООО "Пример"')
        self.assertTrue(org.aktiv)

    def test_foreign_keys_load_in_order_and_zero_becomes_null(self):
        call_command("dbf_import", "--app", "dbfsync_testapp", "--dir", str(DEMO), stdout=open("/dev/null", "w"))
        self.assertEqual(Objekt.objects.get(kod=20).kod_org.naim, 'АО "Образец"')
        self.assertIsNone(Objekt.objects.get(kod=30).kod_org)
        # Перезагрузка одной родительской таблицы не ломает ссылки на неё.
        call_command("dbf_import", "--app", "dbfsync_testapp", "--dir", str(DEMO), "--only", "org", stdout=open("/dev/null", "w"))
        self.assertEqual(Objekt.objects.get(kod=10).kod_org.kod, 1)


def _zero_language_driver(path):
    with open(path, "r+b") as f:
        f.seek(29)
        f.write(b"\x00")


def _corrupt_field(path, record_no, field_name, raw):
    table = open_dbf(path)
    with open(path, "rb") as f:
        header = f.read(12)
    header_len, record_len = struct.unpack("<HH", header[8:12])
    offset = 1
    for fld in table.fields:
        if fld.name == field_name:
            break
        offset += fld.length
    with open(path, "r+b") as f:
        f.seek(header_len + record_no * record_len + offset)
        f.write(raw)


class DbfEdgeCaseTests(TestCase):
    def test_duplicate_unique_key_is_reported_and_nothing_changes(self):
        Org.objects.create(kod=99, naim="было до загрузки")
        t = dbf_writer.Table(str(self.tmp / "org.dbf"), "kod N(5,0); naim C(60)", dbf_type="vfp", codepage="cp1251")
        t.open(dbf_writer.READ_WRITE)
        for row in [(1, "Первая"), (2, "Вторая"), (1, "Повтор первой")]:
            t.append(row)
        t.close()
        err = io.StringIO()
        with self.assertRaises(CommandError):
            call_command("dbf_import", "--app", "dbfsync_testapp", "--dir", str(self.tmp),
                         "--only", "org", stdout=io.StringIO(), stderr=err)
        self.assertIn("KOD = 1: записи №1 и №3 (Повтор первой)", err.getvalue())
        self.assertEqual(list(Org.objects.values_list("kod", flat=True)), [99])

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)

    def test_guess_encoding_when_header_has_none(self):
        shutil.copy(DEMO / "tarif.dbf", self.tmp / "tarif.dbf")
        _zero_language_driver(self.tmp / "tarif.dbf")
        self.assertEqual(detect_encoding(self.tmp / "tarif.dbf"), "cp866")

        t = dbf_writer.Table(str(self.tmp / "win.dbf"), "naim C(40)", dbf_type="vfp", codepage="cp1251")
        t.open(dbf_writer.READ_WRITE)
        t.append(("Горячая вода",))
        t.close()
        _zero_language_driver(self.tmp / "win.dbf")
        self.assertEqual(detect_encoding(self.tmp / "win.dbf"), "cp1251")
        self.assertEqual(next(iter(open_dbf(self.tmp / "win.dbf")))["NAIM"], "Горячая вода")

    def test_bad_values_are_counted_and_subdirs_found(self):
        (self.tmp / "DATA").mkdir()
        for name in ("org.dbf", "org.fpt"):
            shutil.copy(DEMO / name, self.tmp / "DATA" / name)
        _corrupt_field(self.tmp / "DATA" / "org.dbf", 0, "DATA_DOG", b"2019AB15")
        tables = inspect_directory(self.tmp)
        self.assertEqual(tables[0].file_name, "DATA/org.dbf")

        Org.dbf_source = "DATA/org.dbf"
        self.addCleanup(setattr, Org, "dbf_source", "org.dbf")
        source, loaded, bad, fixed = import_table(Org, self.tmp)
        self.assertEqual((source, loaded), (3, 3))
        self.assertEqual(bad, {"DATA_DOG": 1})
        self.assertIsNone(Org.objects.get(kod=1).data_dog)

    def test_fixes_replace_values_on_import(self):
        fixes = {"objekt.dbf": {"KOD_ORG": {"from": [None], "to": 2}, "KOD": {"from": [20], "to": 21}}}
        import_table(Org, DEMO)
        source, loaded, bad, fixed = import_table(Objekt, DEMO, fixes=fixes)
        self.assertEqual(fixed, {"KOD_ORG": 1, "KOD": 1})
        self.assertEqual(Objekt.objects.get(naim__startswith="Котельная").kod_org_id, 2)
        self.assertTrue(Objekt.objects.filter(kod=21).exists())
        self.assertFalse(Objekt.objects.filter(kod=20).exists())
