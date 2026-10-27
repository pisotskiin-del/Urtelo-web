"""Тесты dbf2pg: python -m pytest migration/dbf2pg

Таблицы DBF создаются на лету библиотекой dbf (requirements-dev.txt).
Тест переноса в PostgreSQL запускается, только если задана переменная DBF2PG_TEST_DSN
с адресом пустой тестовой базы, например "host=localhost dbname=dbf2pg_test user=postgres".
"""
import datetime as dt
import importlib.util
import os
from decimal import Decimal
from pathlib import Path

import pytest

dbf = pytest.importorskip("dbf")

spec = importlib.util.spec_from_file_location("dbf2pg", Path(__file__).with_name("dbf2pg.py"))
dbf2pg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dbf2pg)


@pytest.fixture
def src(tmp_path):
    """Город, потребители и начисления: связи по cod_gorod и potreb_id, удалённая запись, битая дата."""
    d = tmp_path / "dbf"
    d.mkdir()
    g = dbf.Table(str(d / "danrasch.dbf"), "cod_gorod N(1,0); name_gorod C(20)", dbf_type="vfp", codepage="cp1251")
    g.open(dbf.READ_WRITE)
    for row in ((1, "Рыбница"), (2, "Дубоссары")):
        g.append(row)
    g.close()
    p = dbf.Table(str(d / "potreb.dbf"), "potreb_id N(4,0); name_potre C(60); cod_gor N(1,0); inf M",
                  dbf_type="vfp", codepage="cp1251")
    p.open(dbf.READ_WRITE)
    for row in ((1, 'ООО "Ромашка"', 1, "примечание"), (2, "ГУП Теплосеть", 2, ""), (3, "ИП Иванов", 0, "")):
        p.append(row)
    dbf.delete(p[2])
    p.close()
    n = dbf.Table(str(d / "nachisl.dbf"), "potreb_id N(4,0); mes D; summa N(12,2)", dbf_type="vfp", codepage="cp1251")
    n.open(dbf.READ_WRITE)
    for i in range(1, 101):
        n.append((1 + i % 2, dt.date(2025, 1 + i % 12, 1), Decimal(i) / 4))
    n.close()
    # Заголовок без кодовой страницы и неверная дата во второй записи
    t = dbf.Table(str(d / "tarif.dbf"), "id_tar N(3,0); name C(20); dat D", dbf_type="db3", codepage="cp866")
    t.open(dbf.READ_WRITE)
    t.append((1, "Отопление", dt.date(2025, 1, 1)))
    t.append((2, "Горячая вода", dt.date(2025, 1, 1)))
    t.close()
    raw = bytearray((d / "tarif.dbf").read_bytes())
    raw[29] = 0
    header, reclen = int.from_bytes(raw[8:10], "little"), int.from_bytes(raw[10:12], "little")
    pos = header + reclen + 1 + 3 + 20
    raw[pos:pos + 8] = b"2025AB01"
    (d / "tarif.dbf").write_bytes(raw)
    return d


def test_encoding_from_header_and_guess(src):
    assert dbf2pg.guess_encoding(src / "potreb.dbf")[0] == "cp1251"
    enc, how = dbf2pg.guess_encoding(src / "tarif.dbf")
    assert enc == "cp866" and "по тексту" in how


def test_names_follow_dbfsync():
    taken = set()
    assert dbf2pg.column_name_for("ID", taken) == "id_dbf"
    assert dbf2pg.column_name_for("CLASS", taken) == "class_dbf"
    assert dbf2pg.column_name_for("NAME-1", taken) == "name_1"
    assert dbf2pg.snake("tarif_") == "tarif"


def test_deleted_records_skipped_and_bad_values_counted(src):
    tables = dbf2pg.dbf_tables(src)
    assert tables["potreb"]["records"] == 2 and tables["potreb"]["deleted"] == 1
    list(dbf2pg.open_dbf(tables["tarif"]["file"], tables["tarif"]["encoding"]).records)
    assert dbf2pg.TolerantParser.bad_values[("tarif.dbf", "DAT")] == 1


def test_keys_and_links(src):
    tables = dbf2pg.analyze(dbf2pg.dbf_tables(src), manual_links=["*.cod_gor=danrasch.cod_gorod"])
    assert tables["potreb"]["key"] == "potreb_id"
    assert {"column": "cod_gor", "ref_table": "danrasch", "ref_column": "cod_gorod", "manual": True} \
        in tables["potreb"]["links"]
    assert any(l["ref_table"] == "potreb" for l in tables["nachisl"]["links"])


def test_relations_json_in_dbfsync_format(src, tmp_path):
    import json
    tables = dbf2pg.analyze(dbf2pg.dbf_tables(src), manual_links=["*.cod_gor=danrasch.cod_gorod"])
    dbf2pg.write_report(tables, tmp_path / "out")
    rel = json.loads((tmp_path / "out" / "relations.json").read_text(encoding="utf-8"))
    assert rel["unique"]["DANRASCH"] == ["COD_GOROD"]
    assert {"table": "POTREB", "field": "COD_GOR", "to_table": "DANRASCH", "to_field": "COD_GOROD"} \
        in rel["foreign_keys"]


def test_read_models(tmp_path):
    models = tmp_path / "models.py"
    models.write_text('''
from django.db import models

class Potreb(models.Model):
    dbf_source = "potreb.dbf"
    dbf_columns = {"id_dbf": "ID"}
    id_dbf = models.IntegerField(null=True)
    cod_gor = models.ForeignKey("Danrasch", to_field="cod_gorod", db_column="cod_gor", on_delete=models.PROTECT)
    org = models.ForeignKey("Org", on_delete=models.PROTECT)

    class Meta:
        db_table = "potreb"
''', encoding="utf-8")
    m = dbf2pg.read_models(models)["potreb.dbf"]
    assert m["table"] == "potreb"
    assert m["columns"] == {"ID": "id_dbf", "COD_GOR": "cod_gor", "ORG": "org_id"}


@pytest.mark.skipif(not os.environ.get("DBF2PG_TEST_DSN"), reason="нужна тестовая база: DBF2PG_TEST_DSN")
def test_load_and_verify(src, tmp_path):
    import psycopg
    dsn = os.environ["DBF2PG_TEST_DSN"]
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute("DROP TABLE IF EXISTS nachisl, potreb, danrasch, tarif")
        conn.execute("CREATE TABLE danrasch (id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,"
                     " cod_gorod integer UNIQUE, name_gorod varchar(20))")
        conn.execute("CREATE TABLE potreb (id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,"
                     " potreb_id integer UNIQUE, name_potre varchar(60),"
                     " cod_gor integer REFERENCES danrasch (cod_gorod), inf text)")
        conn.execute("CREATE TABLE nachisl (id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,"
                     " potreb_id integer REFERENCES potreb (potreb_id), mes date, summa numeric(12,2))")
        conn.execute("CREATE TABLE tarif (id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,"
                     " id_tar integer, name varchar(20), dat date)")
    report = tmp_path / "report"
    assert dbf2pg.main(["all", "--src", str(src), "--dsn", dsn, "--report-dir", str(report),
                        "--fix", "potreb.cod_gor:1=2"]) == 0
    with psycopg.connect(dsn) as conn:
        assert conn.execute("SELECT count(*) FROM potreb").fetchone()[0] == 2
        assert conn.execute("SELECT name FROM tarif WHERE id_tar = 2").fetchone()[0] == "Горячая вода"
        assert conn.execute("SELECT dat FROM tarif WHERE id_tar = 2").fetchone()[0] is None
        # --fix: 1 в cod_gor заменён на 2, сверка сравнивает уже исправленные значения
        assert conn.execute("SELECT cod_gor FROM potreb WHERE potreb_id = 1").fetchone()[0] == 2
