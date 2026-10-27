"""Модели справочников и таблиц старой программы.

Файл сгенерирован командой `python manage.py dbf_inspect`
по таблицам из dbf.
Не правьте его вручную: названия таблиц и полей задаются в
dbfsync/labels/ur_teplo.json, ключи и связи — в ur_teplo_relations.json.
"""

from django.db import models


class DbfModel(models.Model):
    """Общий предок: хранит имя исходного файла DBF и соответствие полей."""

    dbf_source = ""
    dbf_columns = {}

    class Meta:
        abstract = True

    def __str__(self):
        for f in self._meta.concrete_fields:
            if f.get_internal_type() == "CharField":
                value = getattr(self, f.attname)
                if value:
                    return str(value)
        return f"{self._meta.verbose_name} #{self.pk}"


class Abav(DbfModel):
    """abav.dbf (таблица базы): записей 0, кодировка cp1251."""

    dbf_source = "abav.dbf"

    kod = models.BigIntegerField("KOD", null=True, blank=True)
    kodabon = models.BigIntegerField("KODABON", null=True, blank=True)
    name = models.CharField("NAME", max_length=150, null=True, blank=True)
    akcept = models.IntegerField("AKCEPT", null=True, blank=True)
    tarif = models.DecimalField("TARIF", max_digits=20, decimal_places=2, null=True, blank=True)
    ras_kol = models.DecimalField("RAS_KOL", max_digits=20, decimal_places=2, null=True, blank=True)
    zav_kol = models.DecimalField("ZAV_KOL", max_digits=20, decimal_places=2, null=True, blank=True)
    ras_sum = models.DecimalField("RAS_SUM", max_digits=18, decimal_places=2, null=True, blank=True)
    zav_sum = models.DecimalField("ZAV_SUM", max_digits=18, decimal_places=2, null=True, blank=True)
    op_kol = models.DecimalField("OP_KOL", max_digits=20, decimal_places=2, null=True, blank=True)
    op_sum = models.DecimalField("OP_SUM", max_digits=20, decimal_places=2, null=True, blank=True)
    koduslug = models.IntegerField("KODUSLUG", null=True, blank=True)
    nameuslug = models.CharField("NAMEUSLUG", max_length=100, null=True, blank=True)
    tarifue = models.DecimalField("TARIFUE", max_digits=20, decimal_places=2, null=True, blank=True)
    city = models.IntegerField("CITY", null=True, blank=True)
    fisk_cod = models.CharField("FISK_COD", max_length=11, null=True, blank=True)
    ras_shet = models.BigIntegerField("RAS_SHET", null=True, blank=True)
    perc_peni = models.IntegerField("PERC_PENI", null=True, blank=True)

    class Meta:
        db_table = "abav"
        verbose_name = "ABAV"
        verbose_name_plural = "ABAV"
        ordering = ["pk"]


class Abav0812(DbfModel):
    """abav0812.dbf (таблица базы): записей 0, кодировка cp1251."""

    dbf_source = "abav0812.dbf"

    kod = models.BigIntegerField("KOD", null=True, blank=True)
    kodabon = models.BigIntegerField("KODABON", null=True, blank=True)
    name = models.CharField("NAME", max_length=150, null=True, blank=True)
    akcept = models.IntegerField("AKCEPT", null=True, blank=True)
    tarif = models.DecimalField("TARIF", max_digits=20, decimal_places=2, null=True, blank=True)
    ras_kol = models.DecimalField("RAS_KOL", max_digits=20, decimal_places=2, null=True, blank=True)
    zav_kol = models.DecimalField("ZAV_KOL", max_digits=20, decimal_places=2, null=True, blank=True)
    ras_sum = models.DecimalField("RAS_SUM", max_digits=18, decimal_places=2, null=True, blank=True)
    zav_sum = models.DecimalField("ZAV_SUM", max_digits=18, decimal_places=2, null=True, blank=True)
    op_kol = models.DecimalField("OP_KOL", max_digits=20, decimal_places=2, null=True, blank=True)
    op_sum = models.DecimalField("OP_SUM", max_digits=20, decimal_places=2, null=True, blank=True)
    koduslug = models.IntegerField("KODUSLUG", null=True, blank=True)
    nameuslug = models.CharField("NAMEUSLUG", max_length=100, null=True, blank=True)
    tariffue = models.DecimalField("TARIFFUE", max_digits=20, decimal_places=2, null=True, blank=True)
    cod_gor = models.ForeignKey("Danrasch", models.PROTECT, verbose_name="COD_GOR", to_field="cod_gorod", db_column="cod_gor", null=True, blank=True)

    class Meta:
        db_table = "abav0812"
        verbose_name = "ABAV0812"
        verbose_name_plural = "ABAV0812"
        ordering = ["pk"]


class Abonent(DbfModel):
    """abonent.DBF (таблица базы): записей 38, кодировка cp1251."""

    dbf_source = "abonent.DBF"

    tip_rasgvs = models.IntegerField("TIP_RASGVS", null=True, blank=True)
    tip_rasot = models.IntegerField("TIP_RASOT", null=True, blank=True)
    data_aktao = models.DateField("DATA_AKTAO", null=True, blank=True)
    nom_aktao = models.IntegerField("NOM_AKTAO", null=True, blank=True)
    data_otkot = models.DateField("DATA_OTKOT", null=True, blank=True)
    data_pdotp = models.DateField("DATA_PDOTP", null=True, blank=True)
    data_aktag = models.DateField("DATA_AKTAG", null=True, blank=True)
    nom_aktag = models.CharField("NOM_AKTAG", max_length=3, null=True, blank=True)
    data_otgvs = models.DateField("DATA_OTGVS", null=True, blank=True)
    data_pdgvs = models.DateField("DATA_PDGVS", null=True, blank=True)
    nach_otgla = models.DecimalField("NACH_OTGLA", max_digits=8, decimal_places=2, null=True, blank=True)
    nach_otopl = models.DecimalField("NACH_OTOPL", max_digits=8, decimal_places=2, null=True, blank=True)
    glav_potre = models.CharField("GLAV_POTRE", max_length=90, null=True, blank=True)
    pok_new = models.DecimalField("POK_NEW", max_digits=8, decimal_places=2, null=True, blank=True)
    pok_old = models.DecimalField("POK_OLD", max_digits=8, decimal_places=2, null=True, blank=True)
    koef_pok = models.DecimalField("KOEF_POK", max_digits=5, decimal_places=3, null=True, blank=True)
    cod_gor = models.ForeignKey("Danrasch", models.PROTECT, verbose_name="COD_GOR", to_field="cod_gorod", db_column="cod_gor", null=True, blank=True)
    potreb_id = models.ForeignKey("Potreb", models.PROTECT, verbose_name="POTREB_ID", to_field="potreb_id", db_column="potreb_id", null=True, blank=True)
    nom_dog = models.IntegerField("NOM_DOG", null=True, blank=True)
    data_dog = models.DateField("DATA_DOG", null=True, blank=True)
    name_potre = models.CharField("NAME_POTRE", max_length=90, null=True, blank=True)
    cod_minist = models.ForeignKey("Minist", models.PROTECT, verbose_name="COD_MINIST", to_field="cod_minist", db_column="cod_minist", null=True, blank=True)
    v_zdan = models.DecimalField("V_ZDAN", max_digits=7, decimal_places=1, null=True, blank=True)
    v_zdanpr = models.DecimalField("V_ZDANPR", max_digits=7, decimal_places=1, null=True, blank=True)
    s_potreb = models.DecimalField("S_POTREB", max_digits=7, decimal_places=1, null=True, blank=True)
    s_obshaya = models.DecimalField("S_OBSHAYA", max_digits=7, decimal_places=1, null=True, blank=True)
    q_otop = models.DecimalField("Q_OTOP", max_digits=7, decimal_places=5, null=True, blank=True)
    q_otoppr = models.DecimalField("Q_OTOPPR", max_digits=7, decimal_places=5, null=True, blank=True)
    q_gvs = models.DecimalField("Q_GVS", max_digits=5, decimal_places=2, null=True, blank=True)
    id_kategor = models.IntegerField("ID_KATEGOR", null=True, blank=True)
    adres_sd = models.CharField("ADRES_SD", max_length=60, null=True, blank=True)
    adres_regi = models.CharField("ADRES_REGI", max_length=30, null=True, blank=True)
    telefon = models.CharField("TELEFON", max_length=20, null=True, blank=True)
    fax = models.CharField("FAX", max_length=8, null=True, blank=True)
    id_katabon = models.IntegerField("ID_KATABON", null=True, blank=True)
    cod_banka = models.IntegerField("COD_BANKA", null=True, blank=True)
    ras_chet = models.BigIntegerField("RAS_CHET", null=True, blank=True)
    fisk_cod = models.CharField("FISK_COD", max_length=11, null=True, blank=True)
    kor_chet = models.CharField("KOR_CHET", max_length=10, null=True, blank=True)
    direktor = models.CharField("DIREKTOR", max_length=20, null=True, blank=True)
    byhalter = models.CharField("BYHALTER", max_length=20, null=True, blank=True)
    id_koteln = models.IntegerField("ID_KOTELN", null=True, blank=True)
    id_poteri = models.IntegerField("ID_POTERI", null=True, blank=True)

    class Meta:
        db_table = "abonent"
        verbose_name = "ABONENT"
        verbose_name_plural = "ABONENT"
        ordering = ["pk"]


class Abot(DbfModel):
    """abot.dbf (таблица базы): записей 31, кодировка cp1251."""

    dbf_source = "abot.dbf"

    kod = models.BigIntegerField("KOD", null=True, blank=True)
    kodabon = models.BigIntegerField("KODABON", null=True, blank=True)
    name = models.CharField("NAME", max_length=150, null=True, blank=True)
    akcept = models.IntegerField("AKCEPT", null=True, blank=True)
    tarif = models.DecimalField("TARIF", max_digits=20, decimal_places=2, null=True, blank=True)
    ras_kol = models.DecimalField("RAS_KOL", max_digits=20, decimal_places=2, null=True, blank=True)
    zav_kol = models.DecimalField("ZAV_KOL", max_digits=20, decimal_places=2, null=True, blank=True)
    ras_sum = models.DecimalField("RAS_SUM", max_digits=18, decimal_places=2, null=True, blank=True)
    zav_sum = models.DecimalField("ZAV_SUM", max_digits=18, decimal_places=2, null=True, blank=True)
    op_kol = models.DecimalField("OP_KOL", max_digits=20, decimal_places=2, null=True, blank=True)
    op_sum = models.DecimalField("OP_SUM", max_digits=20, decimal_places=2, null=True, blank=True)
    koduslug = models.IntegerField("KODUSLUG", null=True, blank=True)
    nameuslug = models.CharField("NAMEUSLUG", max_length=100, null=True, blank=True)
    tarifue = models.DecimalField("TARIFUE", max_digits=20, decimal_places=2, null=True, blank=True)
    city = models.IntegerField("CITY", null=True, blank=True)
    ras_chet = models.BigIntegerField("RAS_CHET", null=True, blank=True)
    fisk_cod = models.CharField("FISK_COD", max_length=11, null=True, blank=True)
    perc_peni = models.IntegerField("PERC_PENI", null=True, blank=True)
    koduslug1 = models.IntegerField("KODUSLUG1", null=True, blank=True)
    name_city = models.CharField("NAME_CITY", max_length=15, null=True, blank=True)
    name_kateg = models.CharField("NAME_KATEG", max_length=50, null=True, blank=True)
    n_dog = models.CharField("N_DOG", max_length=10, null=True, blank=True)
    dat_dog = models.DateField("DAT_DOG", null=True, blank=True)

    class Meta:
        db_table = "abot"
        verbose_name = "ABOT"
        verbose_name_plural = "ABOT"
        ordering = ["pk"]


class Abot0812(DbfModel):
    """abot0812.dbf (таблица базы): записей 0, кодировка cp1251."""

    dbf_source = "abot0812.dbf"

    kod = models.BigIntegerField("KOD", null=True, blank=True)
    kodabon = models.BigIntegerField("KODABON", null=True, blank=True)
    name = models.CharField("NAME", max_length=100, null=True, blank=True)
    tarifue = models.DecimalField("TARIFUE", max_digits=10, decimal_places=2, null=True, blank=True)
    tarif = models.DecimalField("TARIF", max_digits=20, decimal_places=2, null=True, blank=True)
    ras_kol = models.DecimalField("RAS_KOL", max_digits=10, decimal_places=2, null=True, blank=True)
    koduslug = models.BigIntegerField("KODUSLUG", null=True, blank=True)
    nameuslug = models.CharField("NAMEUSLUG", max_length=100, null=True, blank=True)
    akcept = models.IntegerField("AKCEPT", null=True, blank=True)
    cod_gor = models.ForeignKey("Danrasch", models.PROTECT, verbose_name="COD_GOR", to_field="cod_gorod", db_column="cod_gor", null=True, blank=True)

    class Meta:
        db_table = "abot0812"
        verbose_name = "ABOT0812"
        verbose_name_plural = "ABOT0812"
        ordering = ["pk"]


class Abrs(DbfModel):
    """abrs.dbf (таблица базы): записей 0, кодировка cp1251."""

    dbf_source = "abrs.dbf"

    kod = models.BigIntegerField("KOD", null=True, blank=True)
    kodabon = models.BigIntegerField("KODABON", null=True, blank=True)
    name = models.CharField("NAME", max_length=150, null=True, blank=True)
    akcept = models.IntegerField("AKCEPT", null=True, blank=True)
    tarif = models.DecimalField("TARIF", max_digits=20, decimal_places=2, null=True, blank=True)
    ras_kol = models.DecimalField("RAS_KOL", max_digits=20, decimal_places=2, null=True, blank=True)
    zav_kol = models.DecimalField("ZAV_KOL", max_digits=20, decimal_places=2, null=True, blank=True)
    ras_sum = models.DecimalField("RAS_SUM", max_digits=18, decimal_places=2, null=True, blank=True)
    zav_sum = models.DecimalField("ZAV_SUM", max_digits=18, decimal_places=2, null=True, blank=True)
    op_kol = models.DecimalField("OP_KOL", max_digits=20, decimal_places=2, null=True, blank=True)
    op_sum = models.DecimalField("OP_SUM", max_digits=20, decimal_places=2, null=True, blank=True)
    koduslug = models.IntegerField("KODUSLUG", null=True, blank=True)
    nameuslug = models.CharField("NAMEUSLUG", max_length=100, null=True, blank=True)
    tarifue = models.DecimalField("TARIFUE", max_digits=20, decimal_places=2, null=True, blank=True)
    id_city = models.IntegerField("ID_CITY", null=True, blank=True)
    ras_chet = models.CharField("RAS_CHET", max_length=50, null=True, blank=True)
    fisk_cod = models.CharField("FISK_COD", max_length=30, null=True, blank=True)
    perc_peni = models.DecimalField("PERC_PENI", max_digits=10, decimal_places=2, null=True, blank=True)
    kor_chet = models.CharField("KOR_CHET", max_length=30, null=True, blank=True)
    nom_dog = models.BigIntegerField("NOM_DOG", null=True, blank=True)
    data_dog = models.DateField("DATA_DOG", null=True, blank=True)
    id_kategor = models.BigIntegerField("ID_KATEGOR", null=True, blank=True)
    ao_code = models.CharField("AO_CODE", max_length=31, null=True, blank=True)
    telefon = models.CharField("TELEFON", max_length=30, null=True, blank=True)
    mail = models.CharField("MAIL", max_length=20, null=True, blank=True)
    city = models.CharField("CITY", max_length=10, null=True, blank=True)
    bank = models.CharField("BANK", max_length=100, null=True, blank=True)
    kyb42 = models.CharField("KYB42", max_length=10, null=True, blank=True)
    kategor = models.CharField("KATEGOR", max_length=20, null=True, blank=True)

    class Meta:
        db_table = "abrs"
        verbose_name = "ABRS"
        verbose_name_plural = "ABRS"
        ordering = ["pk"]


class Akcept(DbfModel):
    """akcept.dbf (таблица базы): записей 3, кодировка cp1251."""

    dbf_source = "akcept.dbf"

    id_akc = models.IntegerField("№", null=True, blank=True)
    name_akc = models.CharField("Наименование", max_length=10, null=True, blank=True)

    class Meta:
        db_table = "akcept"
        verbose_name = "Акцепт"
        verbose_name_plural = "Акцепт"
        ordering = ["pk"]


class AktFaktpotr(DbfModel):
    """Akt_faktpotr.dbf (таблица базы): записей 1, кодировка cp1251."""

    dbf_source = "Akt_faktpotr.dbf"

    shapka = models.TextField("SHAPKA", null=True, blank=True)

    class Meta:
        db_table = "akt_faktpotr"
        verbose_name = "AKT_FAKTPOTR"
        verbose_name_plural = "AKT_FAKTPOTR"
        ordering = ["pk"]


class AktPotr(DbfModel):
    """Akt_potr.DBF (свободная таблица): записей 1, кодировка cp1251."""

    dbf_source = "Akt_potr.DBF"

    cod_gor = models.ForeignKey("Danrasch", models.PROTECT, verbose_name="COD_GOR", to_field="cod_gorod", db_column="cod_gor", null=True, blank=True)
    glav_potre = models.CharField("GLAV_POTRE", max_length=180, null=True, blank=True)
    nom_dogab = models.IntegerField("NOM_DOGAB", null=True, blank=True)
    name_potre = models.CharField("NAME_POTRE", max_length=180, null=True, blank=True)
    nom_dog = models.IntegerField("NOM_DOG", null=True, blank=True)
    potreb_id = models.ForeignKey("Potreb", models.PROTECT, verbose_name="POTREB_ID", to_field="potreb_id", db_column="potreb_id", null=True, blank=True)
    id_kategor = models.IntegerField("ID_KATEGOR", null=True, blank=True)
    id_katabon = models.IntegerField("ID_KATABON", null=True, blank=True)
    adres_sd = models.CharField("ADRES_SD", max_length=60, null=True, blank=True)
    oba_dom = models.CharField("OBA_DOM", max_length=6, null=True, blank=True)
    oba_kv = models.CharField("OBA_KV", max_length=5, null=True, blank=True)
    adres_regi = models.CharField("ADRES_REGI", max_length=30, null=True, blank=True)
    nach_gvs = models.DecimalField("NACH_GVS", max_digits=10, decimal_places=3, null=True, blank=True)
    poter_gvs = models.DecimalField("POTER_GVS", max_digits=10, decimal_places=3, null=True, blank=True)
    otnos_dog = models.IntegerField("OTNOS_DOG", null=True, blank=True)
    nach_otopl = models.DecimalField("NACH_OTOPL", max_digits=9, decimal_places=3, null=True, blank=True)
    nach_otsub = models.DecimalField("NACH_OTSUB", max_digits=9, decimal_places=3, null=True, blank=True)
    nac_vsego = models.DecimalField("NAC_VSEGO", max_digits=10, decimal_places=3, null=True, blank=True)
    poternagob = models.DecimalField("POTERNAGOB", max_digits=10, decimal_places=3, null=True, blank=True)
    poterschob = models.DecimalField("POTERSCHOB", max_digits=10, decimal_places=3, null=True, blank=True)
    kodt = models.IntegerField("KODT", null=True, blank=True)
    vid_topl = models.BooleanField("VID_TOPL", null=True)
    nameobakt = models.CharField("NAMEOBAKT", max_length=180, null=True, blank=True)

    class Meta:
        db_table = "akt_potr"
        verbose_name = "AKT_POTR"
        verbose_name_plural = "AKT_POTR"
        ordering = ["pk"]


class Arhiv(DbfModel):
    """arhiv.dbf (таблица базы): записей 218, кодировка cp1251."""

    dbf_source = "arhiv.dbf"

    id_arh = models.BigIntegerField("ID_ARH", null=True, blank=True)
    data_arh = models.DateField("DATA_ARH", null=True, blank=True)
    nom_mes = models.IntegerField("NOM_MES", null=True, blank=True)
    god = models.IntegerField("GOD", null=True, blank=True)

    class Meta:
        db_table = "arhiv"
        verbose_name = "ARHIV"
        verbose_name_plural = "ARHIV"
        ordering = ["pk"]


class ArifPogr(DbfModel):
    """arif_pogr.dbf (таблица базы): записей 2, кодировка cp1251."""

    dbf_source = "arif_pogr.dbf"

    id_kategor = models.BigIntegerField("ID_KATEGOR", null=True, blank=True)
    sum_pogr = models.DecimalField("SUM_POGR", max_digits=10, decimal_places=4, null=True, blank=True)

    class Meta:
        db_table = "arif_pogr"
        verbose_name = "ARIF_POGR"
        verbose_name_plural = "ARIF_POGR"
        ordering = ["pk"]


class Avot0812(DbfModel):
    """avot0812.DBF (таблица базы): записей 0, кодировка cp1251."""

    dbf_source = "avot0812.DBF"

    kod = models.BigIntegerField("KOD", null=True, blank=True)
    kodabon = models.BigIntegerField("KODABON", null=True, blank=True)
    name = models.CharField("NAME", max_length=100, null=True, blank=True)
    tariffue = models.DecimalField("TARIFFUE", max_digits=10, decimal_places=2, null=True, blank=True)
    tarif = models.DecimalField("TARIF", max_digits=10, decimal_places=2, null=True, blank=True)
    ras_kol = models.DecimalField("RAS_KOL", max_digits=10, decimal_places=2, null=True, blank=True)
    koduslug = models.BigIntegerField("KODUSLUG", null=True, blank=True)
    nameuslug = models.CharField("NAMEUSLUG", max_length=100, null=True, blank=True)
    akcept = models.IntegerField("AKCEPT", null=True, blank=True)

    class Meta:
        db_table = "avot0812"
        verbose_name = "AVOT0812"
        verbose_name_plural = "AVOT0812"
        ordering = ["pk"]


class Bank(DbfModel):
    """bank.DBF (таблица базы): записей 8, кодировка cp1251."""

    dbf_source = "bank.DBF"

    cod_banka = models.IntegerField("COD_BANKA", null=True, blank=True)
    name_banka = models.CharField("NAME_BANKA", max_length=80, null=True, blank=True)
    ras_shet = models.BigIntegerField("RAS_SHET", null=True, blank=True)

    class Meta:
        db_table = "bank"
        verbose_name = "BANK"
        verbose_name_plural = "BANK"
        ordering = ["pk"]


class Buh1c(DbfModel):
    """buh_1c.dbf (таблица базы): записей 178, кодировка cp1251."""

    dbf_source = "buh_1c.dbf"

    cod_buhg = models.IntegerField("COD_BUHG", null=True, blank=True)
    cod_ac = models.IntegerField("COD_AC", null=True, blank=True)
    nac_vsego = models.DecimalField("NAC_VSEGO", max_digits=10, decimal_places=2, null=True, blank=True)
    accept = models.CharField("ACCEPT", max_length=2, null=True, blank=True)

    class Meta:
        db_table = "buh_1c"
        verbose_name = "BUH_1C"
        verbose_name_plural = "BUH_1C"
        ordering = ["pk"]


class Danrasch(DbfModel):
    """danrasch.dbf (таблица базы): записей 3, кодировка cp1251."""

    dbf_source = "danrasch.dbf"

    nom_mes = models.IntegerField("NOM_MES", null=True, blank=True)
    god = models.IntegerField("GOD", null=True, blank=True)
    tkoef = models.DecimalField("TKOEF", max_digits=5, decimal_places=3, null=True, blank=True)
    dnotop = models.DecimalField("DNOTOP", max_digits=4, decimal_places=1, null=True, blank=True)
    dngvs = models.DecimalField("DNGVS", max_digits=4, decimal_places=1, null=True, blank=True)
    qpfakt = models.DecimalField("QPFAKT", max_digits=10, decimal_places=2, null=True, blank=True)
    qpras = models.DecimalField("QPRAS", max_digits=10, decimal_places=2, null=True, blank=True)
    t_vozd = models.DecimalField("T_VOZD", max_digits=5, decimal_places=1, null=True, blank=True)
    tip_ras = models.IntegerField("TIP_RAS", null=True, blank=True)
    nac_prgvs = models.DecimalField("NAC_PRGVS", max_digits=10, decimal_places=2, null=True, blank=True)
    name_gorod = models.CharField("Наименование города", max_length=20, null=True, blank=True)
    cod_gorod = models.IntegerField("Код", unique=True, null=True, blank=True)
    t_proekt = models.IntegerField("T_PROEKT", null=True, blank=True)
    name_mes = models.CharField("NAME_MES", max_length=10, null=True, blank=True)
    gkl_bezpod = models.DecimalField("GKL_BEZPOD", max_digits=10, decimal_places=2, null=True, blank=True)
    gkl_pod = models.DecimalField("GKL_POD", max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "danrasch"
        verbose_name = "Города"
        verbose_name_plural = "Города"
        ordering = ["pk"]


class DanraschK(DbfModel):
    """danrasch_k.DBF (таблица базы): записей 3, кодировка cp1251."""

    dbf_source = "danrasch_k.DBF"

    nom_mes = models.IntegerField("NOM_MES", null=True, blank=True)
    god = models.IntegerField("GOD", null=True, blank=True)
    tkoef = models.DecimalField("TKOEF", max_digits=5, decimal_places=3, null=True, blank=True)
    dnotop = models.DecimalField("DNOTOP", max_digits=4, decimal_places=1, null=True, blank=True)
    dngvs = models.DecimalField("DNGVS", max_digits=4, decimal_places=1, null=True, blank=True)
    qpfakt = models.DecimalField("QPFAKT", max_digits=10, decimal_places=2, null=True, blank=True)
    qpras = models.DecimalField("QPRAS", max_digits=10, decimal_places=2, null=True, blank=True)
    t_vozd = models.DecimalField("T_VOZD", max_digits=5, decimal_places=1, null=True, blank=True)
    tip_ras = models.IntegerField("TIP_RAS", null=True, blank=True)
    nac_prgvs = models.DecimalField("NAC_PRGVS", max_digits=10, decimal_places=2, null=True, blank=True)
    name_gorod = models.CharField("NAME_GOROD", max_length=20, null=True, blank=True)
    cod_gorod = models.ForeignKey("Danrasch", models.PROTECT, verbose_name="COD_GOROD", to_field="cod_gorod", db_column="cod_gorod", null=True, blank=True)
    t_proekt = models.IntegerField("T_PROEKT", null=True, blank=True)
    name_mes = models.CharField("NAME_MES", max_length=10, null=True, blank=True)

    class Meta:
        db_table = "danrasch_k"
        verbose_name = "DANRASCH_K"
        verbose_name_plural = "DANRASCH_K"
        ordering = ["pk"]


class DevicePov(DbfModel):
    """device_pov.DBF (свободная таблица): записей 27, кодировка cp1251."""

    dbf_source = "device_pov.DBF"

    cod_gor = models.ForeignKey("Danrasch", models.PROTECT, verbose_name="COD_GOR", to_field="cod_gorod", db_column="cod_gor", null=True, blank=True)
    name_potre = models.CharField("NAME_POTRE", max_length=180, null=True, blank=True)
    p_kod = models.CharField("P_KOD", max_length=10, null=True, blank=True)
    d_pov = models.DateField("D_POV", null=True, blank=True)
    d_next_pov = models.DateField("D_NEXT_POV", null=True, blank=True)

    class Meta:
        db_table = "device_pov"
        verbose_name = "DEVICE_POV"
        verbose_name_plural = "DEVICE_POV"
        ordering = ["pk"]


class Faktpotreb(DbfModel):
    """faktpotreb.dbf (таблица базы): записей 39, кодировка cp1251."""

    dbf_source = "faktpotreb.dbf"

    name_potre = models.CharField("NAME_POTRE", max_length=90, null=True, blank=True)
    nom_dog = models.BigIntegerField("NOM_DOG", null=True, blank=True)
    data_dog = models.DateField("DATA_DOG", null=True, blank=True)
    id_kategor = models.BigIntegerField("ID_KATEGOR", null=True, blank=True)
    id_katabon = models.BigIntegerField("ID_KATABON", null=True, blank=True)
    cod_minist = models.ForeignKey("Minist", models.PROTECT, verbose_name="COD_MINIST", to_field="cod_minist", db_column="cod_minist", null=True, blank=True)
    potreb_id = models.BigIntegerField("POTREB_ID", null=True, blank=True)
    cod_gor = models.ForeignKey("Danrasch", models.PROTECT, verbose_name="COD_GOR", to_field="cod_gorod", db_column="cod_gor", null=True, blank=True)

    class Meta:
        db_table = "faktpotreb"
        verbose_name = "FAKTPOTREB"
        verbose_name_plural = "FAKTPOTREB"
        ordering = ["pk"]


class GetKladrFromdate(DbfModel):
    """get_kladr_fromdate.dbf (таблица базы): записей 10648, кодировка cp1251."""

    dbf_source = "get_kladr_fromdate.dbf"
    dbf_columns = {"region_type_name": "REGION_TYP", "region_code": "REGION_COD", "city_type_name": "CITY_TYPE_", "dist_type_name": "DIST_TYPE_", "street_type_name": "STREET_TYP", "operstatus_name": "OPERSTATUS"}

    aoid = models.CharField("AOID", max_length=36, null=True, blank=True)
    ao_guid = models.CharField("AO_GUID", max_length=36, null=True, blank=True)
    ao_code = models.CharField("AO_CODE", max_length=31, null=True, blank=True)
    area_code = models.IntegerField("AREA_CODE", null=True, blank=True)
    region_type_name = models.IntegerField("REGION_TYP", null=True, blank=True)
    region_ty2 = models.CharField("REGION_TY2", max_length=3, null=True, blank=True)
    region_code = models.IntegerField("REGION_COD", null=True, blank=True)
    city_type = models.IntegerField("CITY_TYPE", null=True, blank=True)
    city_type_name = models.CharField("CITY_TYPE_", max_length=7, null=True, blank=True)
    city_code = models.IntegerField("CITY_CODE", null=True, blank=True)
    dist_type = models.IntegerField("DIST_TYPE", null=True, blank=True)
    dist_type_name = models.CharField("DIST_TYPE_", max_length=4, null=True, blank=True)
    dist_code = models.IntegerField("DIST_CODE", null=True, blank=True)
    street_type_name = models.IntegerField("STREET_TYP", null=True, blank=True)
    street_ty2 = models.CharField("STREET_TY2", max_length=8, null=True, blank=True)
    street_cod = models.IntegerField("STREET_COD", null=True, blank=True)
    formalname = models.CharField("FORMALNAME", max_length=25, null=True, blank=True)
    offname = models.CharField("OFFNAME", max_length=37, null=True, blank=True)
    parent_gui = models.CharField("PARENT_GUI", max_length=36, null=True, blank=True)
    operstatus_name = models.IntegerField("OPERSTATUS", null=True, blank=True)
    operstatu2 = models.CharField("OPERSTATU2", max_length=46, null=True, blank=True)
    next_id = models.CharField("NEXT_ID", max_length=36, null=True, blank=True)
    prev_id = models.CharField("PREV_ID", max_length=36, null=True, blank=True)
    updatedate = models.DateField("UPDATEDATE", null=True, blank=True)
    normdoc = models.CharField("NORMDOC", max_length=36, null=True, blank=True)
    actstatus = models.BooleanField("ACTSTATUS", null=True)
    prov_date = models.DateTimeField("PROV_DATE", null=True, blank=True)

    class Meta:
        db_table = "get_kladr_fromdate"
        verbose_name = "GET_KLADR_FROMDATE"
        verbose_name_plural = "GET_KLADR_FROMDATE"
        ordering = ["pk"]


class God(DbfModel):
    """god.dbf (таблица базы): записей 12, кодировка cp1251."""

    dbf_source = "god.dbf"

    god = models.IntegerField("GOD", null=True, blank=True)

    class Meta:
        db_table = "god"
        verbose_name = "GOD"
        verbose_name_plural = "GOD"
        ordering = ["pk"]


class Gorod(DbfModel):
    """gorod.dbf (таблица базы): записей 3, кодировка cp1251."""

    dbf_source = "gorod.dbf"

    cod_gor = models.ForeignKey("Danrasch", models.PROTECT, verbose_name="COD_GOR", to_field="cod_gorod", db_column="cod_gor", null=True, blank=True)
    name_gorod = models.CharField("NAME_GOROD", max_length=9, null=True, blank=True)

    class Meta:
        db_table = "gorod"
        verbose_name = "GOROD"
        verbose_name_plural = "GOROD"
        ordering = ["pk"]


class GvsKot(DbfModel):
    """gvs_kot.dbf (таблица базы): записей 100, кодировка cp1251."""

    dbf_source = "gvs_kot.dbf"

    id_kot = models.IntegerField("№", null=True, blank=True)
    name_kot = models.CharField("Название котельной", max_length=30, null=True, blank=True)
    kod_gor = models.ForeignKey("Danrasch", models.PROTECT, verbose_name="Код города", to_field="cod_gorod", db_column="kod_gor", null=True, blank=True)
    adress_kot = models.CharField("Адрес", max_length=40, null=True, blank=True)
    nagr_kot = models.DecimalField("NAGR_KOT", max_digits=10, decimal_places=3, null=True, blank=True)
    nom_obekt = models.IntegerField("NOM_OBEKT", null=True, blank=True)
    nom_tel = models.BigIntegerField("№ телефона", null=True, blank=True)
    fio_mast = models.CharField("ФИО мастера", max_length=30, null=True, blank=True)

    class Meta:
        db_table = "gvs_kot"
        verbose_name = "Котельные"
        verbose_name_plural = "Котельные"
        ordering = ["pk"]


class KatTar(DbfModel):
    """kat_tar.dbf (таблица базы): записей 8, кодировка cp1251."""

    dbf_source = "kat_tar.dbf"

    id_kat = models.BigIntegerField("ID_KAT", null=True, blank=True)
    tarif = models.DecimalField("TARIF", max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "kat_tar"
        verbose_name = "KAT_TAR"
        verbose_name_plural = "KAT_TAR"
        ordering = ["pk"]


class Kategabon(DbfModel):
    """Kategabon.dbf (таблица базы): записей 0, кодировка cp1251."""

    dbf_source = "Kategabon.dbf"

    id_katabon = models.IntegerField("ID_KATABON", null=True, blank=True)
    name_katab = models.CharField("NAME_KATAB", max_length=11, null=True, blank=True)

    class Meta:
        db_table = "kategabon"
        verbose_name = "KATEGABON"
        verbose_name_plural = "KATEGABON"
        ordering = ["pk"]


class Kategorpot(DbfModel):
    """kategorpot.DBF (таблица базы): записей 7, кодировка cp1251."""

    dbf_source = "kategorpot.DBF"

    id_kotegor = models.IntegerField("№", null=True, blank=True)
    name_kateg = models.CharField("Наименование категории", max_length=25, null=True, blank=True)

    class Meta:
        db_table = "kategorpot"
        verbose_name = "Категории потребителя"
        verbose_name_plural = "Категории потребителя"
        ordering = ["pk"]


class Kodsity(DbfModel):
    """kodsity.dbf (таблица базы): записей 4, кодировка cp1251."""

    dbf_source = "kodsity.dbf"

    name = models.CharField("NAME", max_length=254, null=True, blank=True)
    kod = models.CharField("KOD", max_length=3, null=True, blank=True)

    class Meta:
        db_table = "kodsity"
        verbose_name = "KODSITY"
        verbose_name_plural = "KODSITY"
        ordering = ["pk"]


class KredoAccounts(DbfModel):
    """Kredo_Accounts.DBF (свободная таблица): записей 15, кодировка cp1251."""

    dbf_source = "Kredo_Accounts.DBF"

    org_id = models.CharField("ORG_ID", max_length=36, null=True, blank=True)
    acntpid = models.BigIntegerField("ACNTPID", null=True, blank=True)
    acntpnm = models.CharField("ACNTPNM", max_length=30, null=True, blank=True)
    acn_num = models.CharField("ACN_NUM", max_length=20, null=True, blank=True)
    kub = models.CharField("KUB", max_length=10, null=True, blank=True)
    bank_nm = models.CharField("BANK_NM", max_length=250, null=True, blank=True)

    class Meta:
        db_table = "kredo_accounts"
        verbose_name = "KREDO_ACCOUNTS"
        verbose_name_plural = "KREDO_ACCOUNTS"
        ordering = ["pk"]


class KredoBranches(DbfModel):
    """Kredo_Branches.DBF (свободная таблица): записей 8, кодировка cp1251."""

    dbf_source = "Kredo_Branches.DBF"

    prn_id = models.CharField("PRN_ID", max_length=36, null=True, blank=True)
    org_id = models.CharField("ORG_ID", max_length=36, null=True, blank=True)
    s_name = models.CharField("S_NAME", max_length=250, null=True, blank=True)
    f_name = models.TextField("F_NAME", null=True, blank=True)
    rric_acn = models.CharField("RRIC_ACN", max_length=10, null=True, blank=True)
    reg_num = models.CharField("REG_NUM", max_length=30, null=True, blank=True)
    fiscode = models.CharField("FISCODE", max_length=20, null=True, blank=True)
    ao_code = models.CharField("AO_CODE", max_length=32, null=True, blank=True)
    bld_type = models.BigIntegerField("BLD_TYPE", null=True, blank=True)
    bld_num = models.CharField("BLD_NUM", max_length=50, null=True, blank=True)
    apt_type = models.BigIntegerField("APT_TYPE", null=True, blank=True)
    apt_num = models.CharField("APT_NUM", max_length=50, null=True, blank=True)
    adr_full = models.CharField("ADR_FULL", max_length=250, null=True, blank=True)
    email = models.CharField("EMAIL", max_length=250, null=True, blank=True)
    phone = models.CharField("PHONE", max_length=250, null=True, blank=True)
    branches = models.BigIntegerField("BRANCHES", null=True, blank=True)
    reg_date = models.DateField("REG_DATE", null=True, blank=True)
    actual = models.BooleanField("ACTUAL", null=True)

    class Meta:
        db_table = "kredo_branches"
        verbose_name = "KREDO_BRANCHES"
        verbose_name_plural = "KREDO_BRANCHES"
        ordering = ["pk"]


class KredoBranchesget(DbfModel):
    """Kredo_BranchesGet.dbf (свободная таблица): записей 0, кодировка cp1251."""

    dbf_source = "Kredo_BranchesGet.dbf"

    org_id = models.CharField("ORG_ID", max_length=36, null=True, blank=True)
    short_name = models.CharField("SHORT_NAME", max_length=250, null=True, blank=True)
    full_name = models.CharField("FULL_NAME", max_length=250, null=True, blank=True)
    bos_fio = models.CharField("BOS_FIO", max_length=150, null=True, blank=True)
    rric_accou = models.CharField("RRIC_ACCOU", max_length=10, null=True, blank=True)
    reg_num = models.CharField("REG_NUM", max_length=30, null=True, blank=True)
    ao_code = models.CharField("AO_CODE", max_length=32, null=True, blank=True)
    bld_type = models.BigIntegerField("BLD_TYPE", null=True, blank=True)
    bld_num = models.CharField("BLD_NUM", max_length=50, null=True, blank=True)
    apt_type = models.BigIntegerField("APT_TYPE", null=True, blank=True)
    apt_num = models.CharField("APT_NUM", max_length=50, null=True, blank=True)
    adr_string = models.CharField("ADR_STRING", max_length=250, null=True, blank=True)
    email = models.CharField("EMAIL", max_length=250, null=True, blank=True)
    phone = models.CharField("PHONE", max_length=250, null=True, blank=True)
    reg_date = models.DateField("REG_DATE", null=True, blank=True)
    actual = models.BooleanField("ACTUAL", null=True)

    class Meta:
        db_table = "kredo_branchesget"
        verbose_name = "KREDO_BRANCHESGET"
        verbose_name_plural = "KREDO_BRANCHESGET"
        ordering = ["pk"]


class KredoDocumentsout(DbfModel):
    """Kredo_DocumentsOut.DBF (свободная таблица): записей 2, кодировка cp1251."""

    dbf_source = "Kredo_DocumentsOut.DBF"

    org_out = models.CharField("ORG_OUT", max_length=36, null=True, blank=True)
    pid_out = models.CharField("PID_OUT", max_length=36, null=True, blank=True)
    fam_out = models.CharField("FAM_OUT", max_length=100, null=True, blank=True)
    im_out = models.CharField("IM_OUT", max_length=100, null=True, blank=True)
    ot_out = models.CharField("OT_OUT", max_length=100, null=True, blank=True)
    pos_out = models.BigIntegerField("POS_OUT", null=True, blank=True)
    posn_out = models.CharField("POSN_OUT", max_length=250, null=True, blank=True)
    doc_id = models.CharField("DOC_ID", max_length=36, null=True, blank=True)
    prev_id = models.CharField("PREV_ID", max_length=36, null=True, blank=True)
    dtype = models.BigIntegerField("DTYPE", null=True, blank=True)
    dtype_n = models.CharField("DTYPE_N", max_length=100, null=True, blank=True)
    dtitle = models.CharField("DTITLE", max_length=250, null=True, blank=True)
    dstat = models.BigIntegerField("DSTAT", null=True, blank=True)
    dstat_n = models.CharField("DSTAT_N", max_length=100, null=True, blank=True)
    reg_date = models.DateField("REG_DATE", null=True, blank=True)
    actual = models.BooleanField("ACTUAL", null=True)
    dst_out = models.BigIntegerField("DST_OUT", null=True, blank=True)
    dstn_out = models.CharField("DSTN_OUT", max_length=100, null=True, blank=True)
    dst_in = models.BigIntegerField("DST_IN", null=True, blank=True)
    dstn_in = models.CharField("DSTN_IN", max_length=100, null=True, blank=True)
    org_in = models.CharField("ORG_IN", max_length=36, null=True, blank=True)
    pid_in = models.CharField("PID_IN", max_length=36, null=True, blank=True)
    fam_in = models.CharField("FAM_IN", max_length=100, null=True, blank=True)
    im_in = models.CharField("IM_IN", max_length=100, null=True, blank=True)
    ot_in = models.CharField("OT_IN", max_length=100, null=True, blank=True)
    pos_in = models.BigIntegerField("POS_IN", null=True, blank=True)
    posn_in = models.CharField("POSN_IN", max_length=250, null=True, blank=True)

    class Meta:
        db_table = "kredo_documentsout"
        verbose_name = "KREDO_DOCUMENTSOUT"
        verbose_name_plural = "KREDO_DOCUMENTSOUT"
        ordering = ["pk"]


class KredoMainorgs(DbfModel):
    """kredo_mainorgs.dbf (свободная таблица): записей 10, кодировка cp1251."""

    dbf_source = "kredo_mainorgs.dbf"

    org_id = models.CharField("ORG_ID", max_length=36, null=True, blank=True)
    s_name = models.CharField("S_NAME", max_length=250, null=True, blank=True)
    f_name = models.TextField("F_NAME", null=True, blank=True)
    rric_acn = models.CharField("RRIC_ACN", max_length=10, null=True, blank=True)
    reg_num = models.CharField("REG_NUM", max_length=30, null=True, blank=True)
    fiscode = models.CharField("FISCODE", max_length=20, null=True, blank=True)
    ao_code = models.CharField("AO_CODE", max_length=32, null=True, blank=True)
    bld_type = models.BigIntegerField("BLD_TYPE", null=True, blank=True)
    bld_num = models.CharField("BLD_NUM", max_length=50, null=True, blank=True)
    apt_type = models.BigIntegerField("APT_TYPE", null=True, blank=True)
    apt_num = models.CharField("APT_NUM", max_length=50, null=True, blank=True)
    adr_full = models.CharField("ADR_FULL", max_length=250, null=True, blank=True)
    email = models.CharField("EMAIL", max_length=250, null=True, blank=True)
    phone = models.CharField("PHONE", max_length=250, null=True, blank=True)
    branches = models.BigIntegerField("BRANCHES", null=True, blank=True)
    reg_date = models.DateField("REG_DATE", null=True, blank=True)
    actual = models.BooleanField("ACTUAL", null=True)

    class Meta:
        db_table = "kredo_mainorgs"
        verbose_name = "KREDO_MAINORGS"
        verbose_name_plural = "KREDO_MAINORGS"
        ordering = ["pk"]


class KredoOrgsget(DbfModel):
    """Kredo_OrgsGet.dbf (свободная таблица): записей 0, кодировка cp1251."""

    dbf_source = "Kredo_OrgsGet.dbf"

    org_id = models.CharField("ORG_ID", max_length=36, null=True, blank=True)
    org_type_i = models.BigIntegerField("ORG_TYPE_I", null=True, blank=True)
    org_type_n = models.CharField("ORG_TYPE_N", max_length=30, null=True, blank=True)
    short_name = models.CharField("SHORT_NAME", max_length=250, null=True, blank=True)
    full_name = models.CharField("FULL_NAME", max_length=250, null=True, blank=True)
    boss_fio = models.CharField("BOSS_FIO", max_length=150, null=True, blank=True)
    rric_accou = models.CharField("RRIC_ACCOU", max_length=10, null=True, blank=True)
    reg_num = models.CharField("REG_NUM", max_length=30, null=True, blank=True)
    fiscal_cod = models.CharField("FISCAL_COD", max_length=20, null=True, blank=True)
    rs = models.CharField("RS", max_length=50, null=True, blank=True)
    ao_code = models.CharField("AO_CODE", max_length=32, null=True, blank=True)
    bld_type = models.BigIntegerField("BLD_TYPE", null=True, blank=True)
    bld_num = models.CharField("BLD_NUM", max_length=50, null=True, blank=True)
    apt_num = models.CharField("APT_NUM", max_length=50, null=True, blank=True)
    apt_type = models.BigIntegerField("APT_TYPE", null=True, blank=True)
    adr_string = models.CharField("ADR_STRING", max_length=250, null=True, blank=True)
    email = models.CharField("EMAIL", max_length=250, null=True, blank=True)
    phone = models.CharField("PHONE", max_length=250, null=True, blank=True)
    reg_date = models.DateField("REG_DATE", null=True, blank=True)
    actual = models.BooleanField("ACTUAL", null=True)

    class Meta:
        db_table = "kredo_orgsget"
        verbose_name = "KREDO_ORGSGET"
        verbose_name_plural = "KREDO_ORGSGET"
        ordering = ["pk"]


class Limit(DbfModel):
    """limit.dbf (таблица базы): записей 0, кодировка cp1251."""

    dbf_source = "limit.dbf"

    potreb_id = models.BigIntegerField("POTREB_ID", null=True, blank=True)
    name_dog = models.CharField("NAME_DOG", max_length=150, null=True, blank=True)
    nac_vsego = models.DecimalField("NAC_VSEGO", max_digits=10, decimal_places=3, null=True, blank=True)
    vd_limit = models.DecimalField("VD_LIMIT", max_digits=10, decimal_places=3, null=True, blank=True)
    nach_finan = models.DecimalField("NACH_FINAN", max_digits=10, decimal_places=3, null=True, blank=True)
    koment = models.CharField("KOMENT", max_length=30, null=True, blank=True)

    class Meta:
        db_table = "limit"
        verbose_name = "LIMIT"
        verbose_name_plural = "LIMIT"
        ordering = ["pk"]


class Minist(DbfModel):
    """minist.dbf (таблица базы): записей 23, кодировка cp1251."""

    dbf_source = "minist.dbf"

    cod_minist = models.IntegerField("№", unique=True, null=True, blank=True)
    name_minis = models.CharField("Наименование", max_length=61, null=True, blank=True)

    class Meta:
        db_table = "minist"
        verbose_name = "Министерства"
        verbose_name_plural = "Министерства"
        ordering = ["pk"]


class Minist1(DbfModel):
    """minist1.dbf (таблица базы): записей 19, кодировка cp1251."""

    dbf_source = "minist1.dbf"

    cod_minist = models.ForeignKey("Minist", models.PROTECT, verbose_name="COD_MINIST", to_field="cod_minist", db_column="cod_minist", null=True, blank=True)
    name_minis = models.CharField("NAME_MINIS", max_length=61, null=True, blank=True)

    class Meta:
        db_table = "minist1"
        verbose_name = "MINIST1"
        verbose_name_plural = "MINIST1"
        ordering = ["pk"]


class NachMinist(DbfModel):
    """nach_minist.dbf (таблица базы): записей 0, кодировка cp1251."""

    dbf_source = "nach_minist.dbf"

    nom_dogab = models.IntegerField("NOM_DOGAB", null=True, blank=True)
    nom_dog = models.IntegerField("NOM_DOG", null=True, blank=True)
    tip_rasgvs = models.IntegerField("TIP_RASGVS", null=True, blank=True)
    tip_rasot = models.IntegerField("TIP_RASOT", null=True, blank=True)
    nach_otsub = models.DecimalField("NACH_OTSUB", max_digits=8, decimal_places=2, null=True, blank=True)
    nach_otopl = models.DecimalField("NACH_OTOPL", max_digits=8, decimal_places=2, null=True, blank=True)
    glav_potre = models.CharField("GLAV_POTRE", max_length=180, null=True, blank=True)
    cod_gor = models.ForeignKey("Danrasch", models.PROTECT, verbose_name="COD_GOR", to_field="cod_gorod", db_column="cod_gor", null=True, blank=True)
    potreb_id = models.IntegerField("POTREB_ID", null=True, blank=True)
    name_potre = models.CharField("NAME_POTRE", max_length=180, null=True, blank=True)
    cod_minist = models.IntegerField("COD_MINIST", null=True, blank=True)
    id_kategor = models.IntegerField("ID_KATEGOR", null=True, blank=True)
    adres_sd = models.CharField("ADRES_SD", max_length=60, null=True, blank=True)
    adres_regi = models.CharField("ADRES_REGI", max_length=30, null=True, blank=True)
    id_katabon = models.IntegerField("ID_KATABON", null=True, blank=True)
    id_poteri = models.IntegerField("ID_POTERI", null=True, blank=True)
    poter_nag = models.DecimalField("POTER_NAG", max_digits=5, decimal_places=2, null=True, blank=True)
    poter_pr = models.DecimalField("POTER_PR", max_digits=5, decimal_places=2, null=True, blank=True)
    cod_pot = models.IntegerField("COD_POT", null=True, blank=True)
    nach_otpr = models.DecimalField("NACH_OTPR", max_digits=10, decimal_places=2, null=True, blank=True)
    nach_otnag = models.DecimalField("NACH_OTNAG", max_digits=10, decimal_places=2, null=True, blank=True)
    nacs_priso = models.DecimalField("NACS_PRISO", max_digits=10, decimal_places=2, null=True, blank=True)
    nach_gvs = models.DecimalField("NACH_GVS", max_digits=10, decimal_places=2, null=True, blank=True)
    nac_vsego = models.DecimalField("NAC_VSEGO", max_digits=10, decimal_places=2, null=True, blank=True)
    cod_buhg = models.IntegerField("COD_BUHG", null=True, blank=True)
    cod_ac = models.IntegerField("COD_AC", null=True, blank=True)
    nac_pogaz = models.DecimalField("NAC_POGAZ", max_digits=10, decimal_places=2, null=True, blank=True)
    otnos_dog = models.IntegerField("OTNOS_DOG", null=True, blank=True)
    vd_limit = models.DecimalField("VD_LIMIT", max_digits=10, decimal_places=3, null=True, blank=True)
    ost_limit = models.DecimalField("OST_LIMIT", max_digits=10, decimal_places=3, null=True, blank=True)
    poterschob = models.DecimalField("POTERSCHOB", max_digits=10, decimal_places=3, null=True, blank=True)
    poternagob = models.DecimalField("POTERNAGOB", max_digits=10, decimal_places=3, null=True, blank=True)
    nalich_pot = models.IntegerField("NALICH_POT", null=True, blank=True)
    nameobakt = models.CharField("NAMEOBAKT", max_length=180, null=True, blank=True)
    ura_dom = models.CharField("URA_DOM", max_length=6, null=True, blank=True)
    ura_kv = models.CharField("URA_KV", max_length=5, null=True, blank=True)
    oba_dom = models.CharField("OBA_DOM", max_length=6, null=True, blank=True)
    oba_kv = models.CharField("OBA_KV", max_length=5, null=True, blank=True)
    period = models.DateField("PERIOD", null=True, blank=True)
    nachs1 = models.DecimalField("NACHS1", max_digits=10, decimal_places=3, null=True, blank=True)
    nachs2 = models.DecimalField("NACHS2", max_digits=10, decimal_places=3, null=True, blank=True)
    nachs3 = models.DecimalField("NACHS3", max_digits=10, decimal_places=3, null=True, blank=True)
    nachs4 = models.DecimalField("NACHS4", max_digits=10, decimal_places=3, null=True, blank=True)
    nachs5 = models.DecimalField("NACHS5", max_digits=10, decimal_places=3, null=True, blank=True)
    nachs6 = models.DecimalField("NACHS6", max_digits=10, decimal_places=3, null=True, blank=True)
    nachs7 = models.DecimalField("NACHS7", max_digits=10, decimal_places=3, null=True, blank=True)
    nachs8 = models.DecimalField("NACHS8", max_digits=10, decimal_places=3, null=True, blank=True)
    nachs9 = models.DecimalField("NACHS9", max_digits=10, decimal_places=3, null=True, blank=True)
    nachs10 = models.DecimalField("NACHS10", max_digits=10, decimal_places=3, null=True, blank=True)
    nachs11 = models.DecimalField("NACHS11", max_digits=10, decimal_places=3, null=True, blank=True)
    nachs12 = models.DecimalField("NACHS12", max_digits=10, decimal_places=3, null=True, blank=True)

    class Meta:
        db_table = "nach_minist"
        verbose_name = "NACH_MINIST"
        verbose_name_plural = "NACH_MINIST"
        ordering = ["pk"]


class NachNul(DbfModel):
    """nach_nul.dbf (свободная таблица): записей 0, кодировка cp1251."""

    dbf_source = "nach_nul.dbf"

    nom_dog = models.IntegerField("NOM_DOG", null=True, blank=True)
    name_potre = models.CharField("NAME_POTRE", max_length=180, null=True, blank=True)
    predopl = models.DecimalField("PREDOPL", max_digits=10, decimal_places=3, null=True, blank=True)
    cod_gor = models.ForeignKey("Danrasch", models.PROTECT, verbose_name="COD_GOR", to_field="cod_gorod", db_column="cod_gor", null=True, blank=True)
    nach_otopl = models.DecimalField("NACH_OTOPL", max_digits=9, decimal_places=3, null=True, blank=True)
    nach_gvs = models.DecimalField("NACH_GVS", max_digits=10, decimal_places=3, null=True, blank=True)

    class Meta:
        db_table = "nach_nul"
        verbose_name = "NACH_NUL"
        verbose_name_plural = "NACH_NUL"
        ordering = ["pk"]


class NachsObekt(DbfModel):
    """nachs_obekt.dbf (таблица базы): записей 0, кодировка cp1251."""

    dbf_source = "nachs_obekt.dbf"

    id_n = models.IntegerField("ID_N", null=True, blank=True)
    potreb_id = models.BigIntegerField("POTREB_ID", null=True, blank=True)
    nom_dog = models.BigIntegerField("NOM_DOG", null=True, blank=True)
    glav_potre = models.CharField("GLAV_POTRE", max_length=180, null=True, blank=True)
    id_katabon = models.IntegerField("ID_KATABON", null=True, blank=True)
    id_kotegor = models.IntegerField("ID_KOTEGOR", null=True, blank=True)
    otnos_dog = models.BigIntegerField("OTNOS_DOG", null=True, blank=True)
    name_potre = models.CharField("NAME_POTRE", max_length=180, null=True, blank=True)
    cod_minist = models.IntegerField("COD_MINIST", null=True, blank=True)
    nach_otopl = models.IntegerField("NACH_OTOPL", null=True, blank=True)
    nach_gvs = models.DecimalField("NACH_GVS", max_digits=10, decimal_places=2, null=True, blank=True)
    nac_vsego = models.DecimalField("NAC_VSEGO", max_digits=10, decimal_places=2, null=True, blank=True)
    nameobakt = models.CharField("NAMEOBAKT", max_length=180, null=True, blank=True)
    nachs_1 = models.DecimalField("NACHS_1", max_digits=10, decimal_places=2, null=True, blank=True)
    nachs_2 = models.DecimalField("NACHS_2", max_digits=10, decimal_places=2, null=True, blank=True)
    nachs_3 = models.DecimalField("NACHS_3", max_digits=10, decimal_places=2, null=True, blank=True)
    nachs_4 = models.DecimalField("NACHS_4", max_digits=10, decimal_places=2, null=True, blank=True)
    nachs_5 = models.DecimalField("NACHS_5", max_digits=10, decimal_places=2, null=True, blank=True)
    nachs_6 = models.DecimalField("NACHS_6", max_digits=10, decimal_places=2, null=True, blank=True)
    nachs_7 = models.DecimalField("NACHS_7", max_digits=10, decimal_places=2, null=True, blank=True)
    nachs_8 = models.DecimalField("NACHS_8", max_digits=10, decimal_places=2, null=True, blank=True)
    nachs_9 = models.DecimalField("NACHS_9", max_digits=10, decimal_places=2, null=True, blank=True)
    nachs_10 = models.DecimalField("NACHS_10", max_digits=10, decimal_places=2, null=True, blank=True)
    nachs_11 = models.DecimalField("NACHS_11", max_digits=10, decimal_places=2, null=True, blank=True)
    nachs_12 = models.DecimalField("NACHS_12", max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "nachs_obekt"
        verbose_name = "NACHS_OBEKT"
        verbose_name_plural = "NACHS_OBEKT"
        ordering = ["pk"]


class NachsPeriod(DbfModel):
    """nachs_period.dbf (таблица базы): записей 2, кодировка cp1251."""

    dbf_source = "nachs_period.dbf"

    nom_dogab = models.IntegerField("NOM_DOGAB", null=True, blank=True)
    nom_dog = models.IntegerField("NOM_DOG", null=True, blank=True)
    nach_otsub = models.DecimalField("NACH_OTSUB", max_digits=8, decimal_places=2, null=True, blank=True)
    nach_otopl = models.DecimalField("NACH_OTOPL", max_digits=8, decimal_places=2, null=True, blank=True)
    glav_potre = models.CharField("GLAV_POTRE", max_length=180, null=True, blank=True)
    cod_gor = models.ForeignKey("Danrasch", models.PROTECT, verbose_name="COD_GOR", to_field="cod_gorod", db_column="cod_gor", null=True, blank=True)
    potreb_id = models.ForeignKey("Potreb", models.PROTECT, verbose_name="POTREB_ID", to_field="potreb_id", db_column="potreb_id", null=True, blank=True)
    name_potre = models.CharField("NAME_POTRE", max_length=180, null=True, blank=True)
    cod_minist = models.ForeignKey("Minist", models.PROTECT, verbose_name="COD_MINIST", to_field="cod_minist", db_column="cod_minist", null=True, blank=True)
    id_kategor = models.IntegerField("ID_KATEGOR", null=True, blank=True)
    adres_sd = models.CharField("ADRES_SD", max_length=60, null=True, blank=True)
    adres_regi = models.CharField("ADRES_REGI", max_length=30, null=True, blank=True)
    id_katabon = models.IntegerField("ID_KATABON", null=True, blank=True)
    nach_otpr = models.DecimalField("NACH_OTPR", max_digits=10, decimal_places=2, null=True, blank=True)
    nach_otnag = models.DecimalField("NACH_OTNAG", max_digits=10, decimal_places=2, null=True, blank=True)
    nacs_priso = models.DecimalField("NACS_PRISO", max_digits=10, decimal_places=2, null=True, blank=True)
    nach_gvs = models.DecimalField("NACH_GVS", max_digits=10, decimal_places=2, null=True, blank=True)
    nac_vsego = models.DecimalField("NAC_VSEGO", max_digits=10, decimal_places=2, null=True, blank=True)
    otnos_dog = models.IntegerField("OTNOS_DOG", null=True, blank=True)
    nameobakt = models.CharField("NAMEOBAKT", max_length=180, null=True, blank=True)
    ura_dom = models.CharField("URA_DOM", max_length=6, null=True, blank=True)
    ura_kv = models.CharField("URA_KV", max_length=5, null=True, blank=True)
    oba_dom = models.CharField("OBA_DOM", max_length=6, null=True, blank=True)
    oba_kv = models.CharField("OBA_KV", max_length=5, null=True, blank=True)
    nachs1 = models.DecimalField("NACHS1", max_digits=10, decimal_places=3, null=True, blank=True)
    nachs2 = models.DecimalField("NACHS2", max_digits=10, decimal_places=3, null=True, blank=True)
    nachs3 = models.DecimalField("NACHS3", max_digits=10, decimal_places=3, null=True, blank=True)
    nachs4 = models.DecimalField("NACHS4", max_digits=10, decimal_places=3, null=True, blank=True)
    nachs5 = models.DecimalField("NACHS5", max_digits=10, decimal_places=3, null=True, blank=True)
    nachs6 = models.DecimalField("NACHS6", max_digits=10, decimal_places=3, null=True, blank=True)
    nachs7 = models.DecimalField("NACHS7", max_digits=10, decimal_places=3, null=True, blank=True)
    nachs8 = models.DecimalField("NACHS8", max_digits=10, decimal_places=3, null=True, blank=True)
    nachs9 = models.DecimalField("NACHS9", max_digits=10, decimal_places=3, null=True, blank=True)
    nachs10 = models.DecimalField("NACHS10", max_digits=10, decimal_places=3, null=True, blank=True)
    nachs11 = models.DecimalField("NACHS11", max_digits=10, decimal_places=3, null=True, blank=True)
    nachs12 = models.DecimalField("NACHS12", max_digits=10, decimal_places=3, null=True, blank=True)
    q_otop = models.DecimalField("Q_OTOP", max_digits=12, decimal_places=5, null=True, blank=True)
    q_otoppr = models.DecimalField("Q_OTOPPR", max_digits=12, decimal_places=5, null=True, blank=True)

    class Meta:
        db_table = "nachs_period"
        verbose_name = "NACHS_PERIOD"
        verbose_name_plural = "NACHS_PERIOD"
        ordering = ["pk"]


class Nag1Koteln(DbfModel):
    """nag1_koteln.dbf (свободная таблица): записей 166, кодировка cp1251."""

    dbf_source = "nag1_koteln.dbf"

    potreb_id = models.ForeignKey("Potreb", models.PROTECT, verbose_name="POTREB_ID", to_field="potreb_id", db_column="potreb_id", null=True, blank=True)
    glav_potre = models.CharField("GLAV_POTRE", max_length=180, null=True, blank=True)
    name_potre = models.CharField("NAME_POTRE", max_length=180, null=True, blank=True)
    q_gvs = models.DecimalField("Q_GVS", max_digits=8, decimal_places=5, null=True, blank=True)
    q_otoppr = models.DecimalField("Q_OTOPPR", max_digits=8, decimal_places=5, null=True, blank=True)
    id_koteln = models.IntegerField("ID_KOTELN", null=True, blank=True)
    name_kot = models.CharField("NAME_KOT", max_length=30, null=True, blank=True)
    cod_gor = models.ForeignKey("Danrasch", models.PROTECT, verbose_name="COD_GOR", to_field="cod_gorod", db_column="cod_gor", null=True, blank=True)
    nom_dog = models.IntegerField("NOM_DOG", null=True, blank=True)
    id_kategor = models.IntegerField("ID_KATEGOR", null=True, blank=True)
    q_gvsn = models.DecimalField("Q_GVSN", max_digits=10, decimal_places=5, null=True, blank=True)
    q_otopn = models.DecimalField("Q_OTOPN", max_digits=10, decimal_places=5, null=True, blank=True)

    class Meta:
        db_table = "nag1_koteln"
        verbose_name = "NAG1_KOTELN"
        verbose_name_plural = "NAG1_KOTELN"
        ordering = ["pk"]


class Nag2Koteln(DbfModel):
    """nag2_koteln.dbf (таблица базы): записей 329, кодировка cp1251."""

    dbf_source = "nag2_koteln.dbf"

    q_gvs = models.DecimalField("Q_GVS", max_digits=5, decimal_places=2, null=True, blank=True)
    q_otoppr = models.DecimalField("Q_OTOPPR", max_digits=10, decimal_places=5, null=True, blank=True)
    id_koteln = models.IntegerField("ID_KOTELN", null=True, blank=True)
    name_kot = models.CharField("NAME_KOT", max_length=30, null=True, blank=True)
    cod_gor = models.ForeignKey("Danrasch", models.PROTECT, verbose_name="COD_GOR", to_field="cod_gorod", db_column="cod_gor", null=True, blank=True)
    q_gvs_n = models.DecimalField("Q_GVS_N", max_digits=10, decimal_places=5, null=True, blank=True)
    q_otoppr_n = models.DecimalField("Q_OTOPPR_N", max_digits=10, decimal_places=5, null=True, blank=True)
    nom_dog = models.BigIntegerField("NOM_DOG", null=True, blank=True)
    gvs_n = models.DecimalField("GVS_N", max_digits=10, decimal_places=5, null=True, blank=True)
    q_gvsn = models.DecimalField("Q_GVSN", max_digits=10, decimal_places=5, null=True, blank=True)

    class Meta:
        db_table = "nag2_koteln"
        verbose_name = "NAG2_KOTELN"
        verbose_name_plural = "NAG2_KOTELN"
        ordering = ["pk"]


class NagKoteln(DbfModel):
    """nag_koteln.dbf (таблица базы): записей 510, кодировка cp1251."""

    dbf_source = "nag_koteln.dbf"

    nach_gvs = models.DecimalField("NACH_GVS", max_digits=10, decimal_places=2, null=True, blank=True)
    nach_otopl = models.DecimalField("NACH_OTOPL", max_digits=8, decimal_places=2, null=True, blank=True)
    id_koteln = models.IntegerField("ID_KOTELN", null=True, blank=True)
    name_kot = models.CharField("NAME_KOT", max_length=30, null=True, blank=True)
    cod_gor = models.ForeignKey("Danrasch", models.PROTECT, verbose_name="COD_GOR", to_field="cod_gorod", db_column="cod_gor", null=True, blank=True)

    class Meta:
        db_table = "nag_koteln"
        verbose_name = "NAG_KOTELN"
        verbose_name_plural = "NAG_KOTELN"
        ordering = ["pk"]


class NagMinist(DbfModel):
    """nag_minist.dbf (таблица базы): записей 38, кодировка cp1251."""

    dbf_source = "nag_minist.dbf"

    nom_dog = models.IntegerField("NOM_DOG", null=True, blank=True)
    name_potre = models.CharField("NAME_POTRE", max_length=180, null=True, blank=True)
    accept = models.IntegerField("ACCEPT", null=True, blank=True)
    q_gvs = models.DecimalField("Q_GVS", max_digits=8, decimal_places=5, null=True, blank=True)
    q_otoppr = models.DecimalField("Q_OTOPPR", max_digits=8, decimal_places=5, null=True, blank=True)
    id_kategor = models.IntegerField("ID_KATEGOR", null=True, blank=True)
    cod_minist = models.ForeignKey("Minist", models.PROTECT, verbose_name="COD_MINIST", to_field="cod_minist", db_column="cod_minist", null=True, blank=True)
    cod_buhg = models.IntegerField("COD_BUHG", null=True, blank=True)
    cod_ac = models.IntegerField("COD_AC", null=True, blank=True)
    cod_gor = models.ForeignKey("Danrasch", models.PROTECT, verbose_name="COD_GOR", to_field="cod_gorod", db_column="cod_gor", null=True, blank=True)

    class Meta:
        db_table = "nag_minist"
        verbose_name = "NAG_MINIST"
        verbose_name_plural = "NAG_MINIST"
        ordering = ["pk"]


class Nam1(DbfModel):
    """nam1.DBF (таблица базы): записей 357, кодировка cp1251."""

    dbf_source = "nam1.DBF"

    s_potreb = models.DecimalField("S_POTREB", max_digits=7, decimal_places=1, null=True, blank=True)
    nom_dogab = models.IntegerField("NOM_DOGAB", null=True, blank=True)
    s_obshaya = models.DecimalField("S_OBSHAYA", max_digits=7, decimal_places=1, null=True, blank=True)
    nom_dog = models.IntegerField("NOM_DOG", null=True, blank=True)
    tip_rasgvs = models.IntegerField("TIP_RASGVS", null=True, blank=True)
    tip_rasot = models.IntegerField("TIP_RASOT", null=True, blank=True)
    data_aktao = models.DateField("DATA_AKTAO", null=True, blank=True)
    nom_aktao = models.IntegerField("NOM_AKTAO", null=True, blank=True)
    data_otkot = models.DateField("DATA_OTKOT", null=True, blank=True)
    data_pdotp = models.DateField("DATA_PDOTP", null=True, blank=True)
    data_aktag = models.DateField("DATA_AKTAG", null=True, blank=True)
    nom_aktag = models.CharField("NOM_AKTAG", max_length=3, null=True, blank=True)
    data_otgvs = models.DateField("DATA_OTGVS", null=True, blank=True)
    data_pdgvs = models.DateField("DATA_PDGVS", null=True, blank=True)
    nach_otsub = models.DecimalField("NACH_OTSUB", max_digits=8, decimal_places=2, null=True, blank=True)
    nach_otopl = models.DecimalField("NACH_OTOPL", max_digits=8, decimal_places=2, null=True, blank=True)
    glav_potre = models.CharField("GLAV_POTRE", max_length=90, null=True, blank=True)
    pok_new = models.DecimalField("POK_NEW", max_digits=8, decimal_places=2, null=True, blank=True)
    pok_old = models.DecimalField("POK_OLD", max_digits=8, decimal_places=2, null=True, blank=True)
    koef_pok = models.DecimalField("KOEF_POK", max_digits=5, decimal_places=3, null=True, blank=True)
    cod_gor = models.ForeignKey("Danrasch", models.PROTECT, verbose_name="COD_GOR", to_field="cod_gorod", db_column="cod_gor", null=True, blank=True)
    potreb_id = models.IntegerField("POTREB_ID", null=True, blank=True)
    data_dog = models.DateField("DATA_DOG", null=True, blank=True)
    name_potre = models.CharField("NAME_POTRE", max_length=90, null=True, blank=True)
    cod_minist = models.ForeignKey("Minist", models.PROTECT, verbose_name="COD_MINIST", to_field="cod_minist", db_column="cod_minist", null=True, blank=True)
    v_zdan = models.DecimalField("V_ZDAN", max_digits=7, decimal_places=1, null=True, blank=True)
    v_zdanpr = models.DecimalField("V_ZDANPR", max_digits=7, decimal_places=1, null=True, blank=True)
    q_otop = models.DecimalField("Q_OTOP", max_digits=7, decimal_places=5, null=True, blank=True)
    q_otopobsh = models.DecimalField("Q_OTOPOBSH", max_digits=7, decimal_places=5, null=True, blank=True)
    q_otoppr = models.DecimalField("Q_OTOPPR", max_digits=7, decimal_places=5, null=True, blank=True)
    q_gvs = models.DecimalField("Q_GVS", max_digits=5, decimal_places=2, null=True, blank=True)
    id_kategor = models.IntegerField("ID_KATEGOR", null=True, blank=True)
    adres_sd = models.CharField("ADRES_SD", max_length=60, null=True, blank=True)
    adres_regi = models.CharField("ADRES_REGI", max_length=30, null=True, blank=True)
    telefon = models.CharField("TELEFON", max_length=20, null=True, blank=True)
    fax = models.CharField("FAX", max_length=8, null=True, blank=True)
    id_katabon = models.IntegerField("ID_KATABON", null=True, blank=True)
    cod_banka = models.IntegerField("COD_BANKA", null=True, blank=True)
    ras_chet = models.BigIntegerField("RAS_CHET", null=True, blank=True)
    fisk_cod = models.CharField("FISK_COD", max_length=11, null=True, blank=True)
    kor_chet = models.CharField("KOR_CHET", max_length=10, null=True, blank=True)
    direktor = models.CharField("DIREKTOR", max_length=20, null=True, blank=True)
    byhalter = models.CharField("BYHALTER", max_length=20, null=True, blank=True)
    id_koteln = models.IntegerField("ID_KOTELN", null=True, blank=True)
    id_poteri = models.IntegerField("ID_POTERI", null=True, blank=True)
    dngvs = models.DecimalField("DNGVS", max_digits=4, decimal_places=1, null=True, blank=True)
    dnotop = models.DecimalField("DNOTOP", max_digits=4, decimal_places=1, null=True, blank=True)
    poter_nag = models.DecimalField("POTER_NAG", max_digits=5, decimal_places=3, null=True, blank=True)
    poter_pr = models.DecimalField("POTER_PR", max_digits=5, decimal_places=3, null=True, blank=True)
    cod_pot = models.IntegerField("COD_POT", null=True, blank=True)
    nach_otpr = models.DecimalField("NACH_OTPR", max_digits=10, decimal_places=2, null=True, blank=True)
    nach_otnag = models.DecimalField("NACH_OTNAG", max_digits=10, decimal_places=2, null=True, blank=True)
    dn_pereras = models.IntegerField("DN_PERERAS", null=True, blank=True)
    tkf_perer = models.DecimalField("TKF_PERER", max_digits=5, decimal_places=3, null=True, blank=True)
    gkl_perer = models.DecimalField("GKL_PERER", max_digits=10, decimal_places=2, null=True, blank=True)
    posle_prib = models.IntegerField("POSLE_PRIB", null=True, blank=True)
    nacs_priso = models.DecimalField("NACS_PRISO", max_digits=10, decimal_places=2, null=True, blank=True)
    nach_gvs = models.DecimalField("NACH_GVS", max_digits=10, decimal_places=2, null=True, blank=True)
    nac_vsego = models.DecimalField("NAC_VSEGO", max_digits=10, decimal_places=2, null=True, blank=True)
    predopl = models.DecimalField("PREDOPL", max_digits=10, decimal_places=2, null=True, blank=True)
    accept = models.IntegerField("ACCEPT", null=True, blank=True)
    cod_buhg = models.IntegerField("COD_BUHG", null=True, blank=True)
    cod_ac = models.IntegerField("COD_AC", null=True, blank=True)
    nac_pogaz = models.DecimalField("NAC_POGAZ", max_digits=10, decimal_places=2, null=True, blank=True)
    otnos_dog = models.IntegerField("OTNOS_DOG", null=True, blank=True)
    nom_pribor = models.BigIntegerField("NOM_PRIBOR", null=True, blank=True)
    inf_pribor = models.IntegerField("INF_PRIBOR", null=True, blank=True)

    class Meta:
        db_table = "nam1"
        verbose_name = "NAM1"
        verbose_name_plural = "NAM1"
        ordering = ["pk"]


class Nastrsys(DbfModel):
    """Nastrsys.dbf (таблица базы): записей 0, кодировка cp1251."""

    dbf_source = "Nastrsys.dbf"

    potreb_id = models.IntegerField("POTREB_ID", null=True, blank=True)

    class Meta:
        db_table = "nastrsys"
        verbose_name = "NASTRSYS"
        verbose_name_plural = "NASTRSYS"
        ordering = ["pk"]


class Ot022010(DbfModel):
    """Ot022010.dbf (таблица базы): записей 3, кодировка cp1251."""

    dbf_source = "Ot022010.dbf"

    id_gorod = models.IntegerField("ID_GOROD", null=True, blank=True)
    tarif = models.DecimalField("TARIF", max_digits=10, decimal_places=2, null=True, blank=True)
    jil_hozras = models.DecimalField("JIL_HOZRAS", max_digits=10, decimal_places=2, null=True, blank=True)
    jil_budjet = models.DecimalField("JIL_BUDJET", max_digits=10, decimal_places=2, null=True, blank=True)
    nas_abon = models.DecimalField("NAS_ABON", max_digits=10, decimal_places=2, null=True, blank=True)
    vsego_nas = models.DecimalField("VSEGO_NAS", max_digits=10, decimal_places=2, null=True, blank=True)
    hozrasch = models.DecimalField("HOZRASCH", max_digits=10, decimal_places=2, null=True, blank=True)
    bud_mestn = models.DecimalField("BUD_MESTN", max_digits=10, decimal_places=2, null=True, blank=True)
    bud_respub = models.DecimalField("BUD_RESPUB", max_digits=10, decimal_places=2, null=True, blank=True)
    vsego_budj = models.DecimalField("VSEGO_BUDJ", max_digits=10, decimal_places=2, null=True, blank=True)
    vsego_gkl = models.DecimalField("VSEGO_GKL", max_digits=10, decimal_places=2, null=True, blank=True)
    bud_gvs = models.DecimalField("BUD_GVS", max_digits=10, decimal_places=2, null=True, blank=True)
    hoz_gvs = models.DecimalField("HOZ_GVS", max_digits=10, decimal_places=2, null=True, blank=True)
    nas_gvs = models.DecimalField("NAS_GVS", max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "ot022010"
        verbose_name = "OT022010"
        verbose_name_plural = "OT022010"
        ordering = ["pk"]


class OtKateg(DbfModel):
    """ot_kateg.dbf (свободная таблица): записей 27, кодировка cp1251."""

    dbf_source = "ot_kateg.dbf"

    nom_dog = models.IntegerField("NOM_DOG", null=True, blank=True)
    name_potre = models.CharField("NAME_POTRE", max_length=180, null=True, blank=True)
    accept = models.IntegerField("ACCEPT", null=True, blank=True)
    predopl = models.DecimalField("PREDOPL", max_digits=10, decimal_places=3, null=True, blank=True)
    nac_vsego = models.DecimalField("NAC_VSEGO", max_digits=10, decimal_places=3, null=True, blank=True)
    id_kategor = models.IntegerField("ID_KATEGOR", null=True, blank=True)
    cod_minist = models.ForeignKey("Minist", models.PROTECT, verbose_name="COD_MINIST", to_field="cod_minist", db_column="cod_minist", null=True, blank=True)
    cod_buhg = models.IntegerField("COD_BUHG", null=True, blank=True)
    potreb_id = models.ForeignKey("Potreb", models.PROTECT, verbose_name="POTREB_ID", to_field="potreb_id", db_column="potreb_id", null=True, blank=True)
    cod_ac = models.IntegerField("COD_AC", null=True, blank=True)
    cod_gor = models.ForeignKey("Danrasch", models.PROTECT, verbose_name="COD_GOR", to_field="cod_gorod", db_column="cod_gor", null=True, blank=True)

    class Meta:
        db_table = "ot_kateg"
        verbose_name = "OT_KATEG"
        verbose_name_plural = "OT_KATEG"
        ordering = ["pk"]


class PKot(DbfModel):
    """p_kot.dbf (таблица базы): записей 0, кодировка cp1251."""

    dbf_source = "p_kot.dbf"

    name_kot = models.CharField("NAME_KOT", max_length=20, null=True, blank=True)
    nac_kot = models.DecimalField("NAC_KOT", max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "p_kot"
        verbose_name = "P_KOT"
        verbose_name_plural = "P_KOT"
        ordering = ["pk"]


class PolezNak(DbfModel):
    """polez_nak.dbf (таблица базы): записей 183, кодировка cp1251."""

    dbf_source = "polez_nak.dbf"

    gorod = models.CharField("GOROD", max_length=10, null=True, blank=True)
    tarif = models.DecimalField("TARIF", max_digits=10, decimal_places=2, null=True, blank=True)
    jil_hozras = models.DecimalField("JIL_HOZRAS", max_digits=10, decimal_places=2, null=True, blank=True)
    jil_budjet = models.DecimalField("JIL_BUDJET", max_digits=10, decimal_places=2, null=True, blank=True)
    nas_abon = models.DecimalField("NAS_ABON", max_digits=10, decimal_places=2, null=True, blank=True)
    vsego_nas = models.DecimalField("VSEGO_NAS", max_digits=10, decimal_places=2, null=True, blank=True)
    hozrasch = models.DecimalField("HOZRASCH", max_digits=10, decimal_places=2, null=True, blank=True)
    bud_mestn = models.DecimalField("BUD_MESTN", max_digits=10, decimal_places=2, null=True, blank=True)
    bud_respub = models.DecimalField("BUD_RESPUB", max_digits=10, decimal_places=2, null=True, blank=True)
    vsego_budj = models.DecimalField("VSEGO_BUDJ", max_digits=10, decimal_places=2, null=True, blank=True)
    vsego_gkl = models.DecimalField("VSEGO_GKL", max_digits=10, decimal_places=2, null=True, blank=True)
    mes_god = models.CharField("MES_GOD", max_length=6, null=True, blank=True)
    mes_god1 = models.CharField("MES_GOD1", max_length=15, null=True, blank=True)
    hoz_gvs = models.DecimalField("HOZ_GVS", max_digits=10, decimal_places=2, null=True, blank=True)
    bud_gvs = models.DecimalField("BUD_GVS", max_digits=10, decimal_places=2, null=True, blank=True)
    nas_gvs = models.DecimalField("NAS_GVS", max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "polez_nak"
        verbose_name = "POLEZ_NAK"
        verbose_name_plural = "POLEZ_NAK"
        ordering = ["pk"]


class PolezOtpusk(DbfModel):
    """polez_otpusk.dbf (таблица базы): записей 3, кодировка cp1251."""

    dbf_source = "polez_otpusk.dbf"
    dbf_columns = {"jil_hozras_p": "JIL_HOZRAS", "bud_respubd": "BUD_RESPUB", "bud_resp_pd": "BUD_RESP_P"}

    id_gorod = models.IntegerField("ID_GOROD", null=True, blank=True)
    tarif = models.DecimalField("TARIF", max_digits=10, decimal_places=2, null=True, blank=True)
    jil_hozras_p = models.DecimalField("JIL_HOZRAS", max_digits=10, decimal_places=2, null=True, blank=True)
    jil_budjet = models.DecimalField("JIL_BUDJET", max_digits=10, decimal_places=2, null=True, blank=True)
    nas_abon = models.DecimalField("NAS_ABON", max_digits=10, decimal_places=2, null=True, blank=True)
    vsego_nas = models.DecimalField("VSEGO_NAS", max_digits=10, decimal_places=2, null=True, blank=True)
    hozrasch = models.DecimalField("HOZRASCH", max_digits=10, decimal_places=2, null=True, blank=True)
    bud_mestn = models.DecimalField("BUD_MESTN", max_digits=10, decimal_places=2, null=True, blank=True)
    bud_respubd = models.DecimalField("BUD_RESPUB", max_digits=10, decimal_places=2, null=True, blank=True)
    vsego_budj = models.DecimalField("VSEGO_BUDJ", max_digits=10, decimal_places=2, null=True, blank=True)
    vsego_gkl = models.DecimalField("VSEGO_GKL", max_digits=10, decimal_places=2, null=True, blank=True)
    bud_gvs = models.DecimalField("BUD_GVS", max_digits=10, decimal_places=2, null=True, blank=True)
    hoz_gvs = models.DecimalField("HOZ_GVS", max_digits=10, decimal_places=2, null=True, blank=True)
    nas_gvs = models.DecimalField("NAS_GVS", max_digits=10, decimal_places=2, null=True, blank=True)
    name_gorod = models.CharField("NAME_GOROD", max_length=10, null=True, blank=True)
    bud_skiot = models.DecimalField("BUD_SKIOT", max_digits=10, decimal_places=2, null=True, blank=True)
    skiot_gvs = models.DecimalField("SKIOT_GVS", max_digits=10, decimal_places=2, null=True, blank=True)
    bud_mes_p = models.DecimalField("BUD_MES_P", max_digits=10, decimal_places=2, null=True, blank=True)
    hozrasch_p = models.DecimalField("HOZRASCH_P", max_digits=10, decimal_places=2, null=True, blank=True)
    bud_resp_pd = models.DecimalField("BUD_RESP_P", max_digits=10, decimal_places=2, null=True, blank=True)
    jil_budj_p = models.DecimalField("JIL_BUDJ_P", max_digits=10, decimal_places=2, null=True, blank=True)
    jil_hozra2 = models.DecimalField("JIL_HOZRA2", max_digits=10, decimal_places=2, null=True, blank=True)
    nas_abon_p = models.DecimalField("NAS_ABON_P", max_digits=10, decimal_places=2, null=True, blank=True)
    bud_skio_p = models.DecimalField("BUD_SKIO_P", max_digits=10, decimal_places=2, null=True, blank=True)
    bud_gvs_p = models.DecimalField("BUD_GVS_P", max_digits=10, decimal_places=2, null=True, blank=True)
    hoz_gvs_p = models.DecimalField("HOZ_GVS_P", max_digits=10, decimal_places=2, null=True, blank=True)
    nas_gvs_p = models.DecimalField("NAS_GVS_P", max_digits=10, decimal_places=2, null=True, blank=True)
    skio_gvs_p = models.DecimalField("SKIO_GVS_P", max_digits=10, decimal_places=2, null=True, blank=True)
    nas_hozras = models.DecimalField("NAS_HOZRAS", max_digits=10, decimal_places=2, null=True, blank=True)
    nas_hozra2 = models.DecimalField("NAS_HOZRA2", max_digits=10, decimal_places=2, null=True, blank=True)
    nasabbez_n = models.DecimalField("NASABBEZ_N", max_digits=10, decimal_places=2, null=True, blank=True)
    nasabpod_n = models.DecimalField("NASABPOD_N", max_digits=10, decimal_places=2, null=True, blank=True)
    nasabbez_p = models.DecimalField("NASABBEZ_P", max_digits=10, decimal_places=2, null=True, blank=True)
    nasabpod_p = models.DecimalField("NASABPOD_P", max_digits=10, decimal_places=2, null=True, blank=True)
    bud_mes_pd = models.DecimalField("BUD_MES_PD", max_digits=10, decimal_places=2, null=True, blank=True)
    bud_mestnd = models.DecimalField("BUD_MESTND", max_digits=10, decimal_places=2, null=True, blank=True)
    bud_resp_2 = models.DecimalField("BUD_RESP_2", max_digits=10, decimal_places=2, null=True, blank=True)
    bud_respu2 = models.DecimalField("BUD_RESPU2", max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "polez_otpusk"
        verbose_name = "POLEZ_OTPUSK"
        verbose_name_plural = "POLEZ_OTPUSK"
        ordering = ["pk"]


class PolezTarif(DbfModel):
    """polez_tarif.dbf (таблица базы): записей 1, кодировка cp1251."""

    dbf_source = "polez_tarif.dbf"

    tar_1 = models.DecimalField("TAR_1", max_digits=10, decimal_places=2, null=True, blank=True)
    tar_2 = models.DecimalField("TAR_2", max_digits=10, decimal_places=2, null=True, blank=True)
    tar_3 = models.DecimalField("TAR_3", max_digits=10, decimal_places=2, null=True, blank=True)
    tar_4 = models.DecimalField("TAR_4", max_digits=10, decimal_places=2, null=True, blank=True)
    tar_5 = models.DecimalField("TAR_5", max_digits=10, decimal_places=2, null=True, blank=True)
    tar_6 = models.DecimalField("TAR_6", max_digits=10, decimal_places=2, null=True, blank=True)
    tar_7 = models.DecimalField("TAR_7", max_digits=10, decimal_places=2, null=True, blank=True)
    tar_8 = models.DecimalField("TAR_8", max_digits=10, decimal_places=2, null=True, blank=True)
    tar_9 = models.DecimalField("TAR_9", max_digits=10, decimal_places=2, null=True, blank=True)
    tar_10 = models.DecimalField("TAR_10", max_digits=10, decimal_places=2, null=True, blank=True)
    tar_11 = models.DecimalField("TAR_11", max_digits=10, decimal_places=2, null=True, blank=True)
    tar_12 = models.DecimalField("TAR_12", max_digits=10, decimal_places=2, null=True, blank=True)
    tar_13 = models.DecimalField("TAR_13", max_digits=10, decimal_places=2, null=True, blank=True)
    tar_14 = models.DecimalField("TAR_14", max_digits=10, decimal_places=2, null=True, blank=True)
    tar_1d = models.DecimalField("TAR_1D", max_digits=10, decimal_places=2, null=True, blank=True)
    tar_2d = models.DecimalField("TAR_2D", max_digits=10, decimal_places=2, null=True, blank=True)
    tar_3d = models.DecimalField("TAR_3D", max_digits=10, decimal_places=2, null=True, blank=True)
    tar_4d = models.DecimalField("TAR_4D", max_digits=10, decimal_places=2, null=True, blank=True)
    tar_5d = models.DecimalField("TAR_5D", max_digits=10, decimal_places=2, null=True, blank=True)
    tar_6d = models.DecimalField("TAR_6D", max_digits=10, decimal_places=2, null=True, blank=True)
    tar_7d = models.DecimalField("TAR_7D", max_digits=10, decimal_places=2, null=True, blank=True)
    tar_8d = models.DecimalField("TAR_8D", max_digits=10, decimal_places=2, null=True, blank=True)
    tar_9d = models.DecimalField("TAR_9D", max_digits=10, decimal_places=2, null=True, blank=True)
    tar_10d = models.DecimalField("TAR_10D", max_digits=10, decimal_places=2, null=True, blank=True)
    tar_11d = models.DecimalField("TAR_11D", max_digits=10, decimal_places=2, null=True, blank=True)
    tar_12d = models.DecimalField("TAR_12D", max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "polez_tarif"
        verbose_name = "POLEZ_TARIF"
        verbose_name_plural = "POLEZ_TARIF"
        ordering = ["pk"]


class PolezTarifK(DbfModel):
    """polez_tarif_k.DBF (таблица базы): записей 1, кодировка cp1251."""

    dbf_source = "polez_tarif_k.DBF"

    tar_1 = models.DecimalField("TAR_1", max_digits=10, decimal_places=2, null=True, blank=True)
    tar_2 = models.DecimalField("TAR_2", max_digits=10, decimal_places=2, null=True, blank=True)
    tar_3 = models.DecimalField("TAR_3", max_digits=10, decimal_places=2, null=True, blank=True)
    tar_4 = models.DecimalField("TAR_4", max_digits=10, decimal_places=2, null=True, blank=True)
    tar_5 = models.DecimalField("TAR_5", max_digits=10, decimal_places=2, null=True, blank=True)
    tar_6 = models.DecimalField("TAR_6", max_digits=10, decimal_places=2, null=True, blank=True)
    tar_7 = models.DecimalField("TAR_7", max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "polez_tarif_k"
        verbose_name = "POLEZ_TARIF_K"
        verbose_name_plural = "POLEZ_TARIF_K"
        ordering = ["pk"]


class Polezotpusk2(DbfModel):
    """polezotpusk.DBF (свободная таблица): записей 1, кодировка cp1251."""

    dbf_source = "polezotpusk.DBF"

    id_gorod = models.IntegerField("ID_GOROD", null=True, blank=True)
    tarif = models.DecimalField("TARIF", max_digits=10, decimal_places=2, null=True, blank=True)
    jil_hozras = models.DecimalField("JIL_HOZRAS", max_digits=10, decimal_places=2, null=True, blank=True)
    jil_budjet = models.DecimalField("JIL_BUDJET", max_digits=10, decimal_places=2, null=True, blank=True)
    nas_abon = models.DecimalField("NAS_ABON", max_digits=10, decimal_places=2, null=True, blank=True)
    vsego_nas = models.DecimalField("VSEGO_NAS", max_digits=10, decimal_places=2, null=True, blank=True)
    hozrasch = models.DecimalField("HOZRASCH", max_digits=10, decimal_places=2, null=True, blank=True)
    bud_mestn = models.DecimalField("BUD_MESTN", max_digits=10, decimal_places=2, null=True, blank=True)
    bud_respub = models.DecimalField("BUD_RESPUB", max_digits=10, decimal_places=2, null=True, blank=True)
    vsego_budj = models.DecimalField("VSEGO_BUDJ", max_digits=10, decimal_places=2, null=True, blank=True)
    vsego_gkl = models.DecimalField("VSEGO_GKL", max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "polezotpusk"
        verbose_name = "POLEZOTPUSK"
        verbose_name_plural = "POLEZOTPUSK"
        ordering = ["pk"]


class Potreb(DbfModel):
    """potreb.dbf (таблица базы): записей 963, кодировка cp1251."""

    dbf_source = "potreb.dbf"
    dbf_columns = {"nach_poslpr": "NACH_POSLP"}

    s_potreb = models.DecimalField("S_POTREB", max_digits=7, decimal_places=1, null=True, blank=True)
    nom_dogab = models.IntegerField("NOM_DOGAB", null=True, blank=True)
    s_obshaya = models.DecimalField("S_OBSHAYA", max_digits=7, decimal_places=1, null=True, blank=True)
    nom_dog = models.IntegerField("NOM_DOG", null=True, blank=True)
    tip_rasgvs = models.IntegerField("TIP_RASGVS", null=True, blank=True)
    tip_rasot = models.IntegerField("TIP_RASOT", null=True, blank=True)
    data_aktao = models.DateField("DATA_AKTAO", null=True, blank=True)
    nom_aktao = models.IntegerField("NOM_AKTAO", null=True, blank=True)
    data_otkot = models.DateField("DATA_OTKOT", null=True, blank=True)
    data_pdotp = models.DateField("DATA_PDOTP", null=True, blank=True)
    data_aktag = models.DateField("DATA_AKTAG", null=True, blank=True)
    nom_aktag = models.CharField("NOM_AKTAG", max_length=3, null=True, blank=True)
    data_otgvs = models.DateField("DATA_OTGVS", null=True, blank=True)
    data_pdgvs = models.DateField("DATA_PDGVS", null=True, blank=True)
    nach_otsub = models.DecimalField("NACH_OTSUB", max_digits=9, decimal_places=3, null=True, blank=True)
    nach_otopl = models.DecimalField("NACH_OTOPL", max_digits=9, decimal_places=3, null=True, blank=True)
    glav_potre = models.CharField("GLAV_POTRE", max_length=180, null=True, blank=True)
    pok_new = models.DecimalField("POK_NEW", max_digits=9, decimal_places=3, null=True, blank=True)
    pok_old = models.DecimalField("POK_OLD", max_digits=9, decimal_places=3, null=True, blank=True)
    koef_pok = models.DecimalField("KOEF_POK", max_digits=5, decimal_places=3, null=True, blank=True)
    cod_gor = models.ForeignKey("Danrasch", models.PROTECT, verbose_name="COD_GOR", to_field="cod_gorod", db_column="cod_gor", null=True, blank=True)
    potreb_id = models.IntegerField("POTREB_ID", unique=True, null=True, blank=True)
    data_dog = models.DateField("DATA_DOG", null=True, blank=True)
    name_potre = models.CharField("NAME_POTRE", max_length=180, null=True, blank=True)
    cod_minist = models.ForeignKey("Minist", models.PROTECT, verbose_name="COD_MINIST", to_field="cod_minist", db_column="cod_minist", null=True, blank=True)
    v_zdan = models.DecimalField("V_ZDAN", max_digits=7, decimal_places=1, null=True, blank=True)
    v_zdanpr = models.DecimalField("V_ZDANPR", max_digits=7, decimal_places=1, null=True, blank=True)
    q_otop = models.DecimalField("Q_OTOP", max_digits=8, decimal_places=5, null=True, blank=True)
    q_otopobsh = models.DecimalField("Q_OTOPOBSH", max_digits=8, decimal_places=5, null=True, blank=True)
    q_otoppr = models.DecimalField("Q_OTOPPR", max_digits=8, decimal_places=5, null=True, blank=True)
    q_gvs = models.DecimalField("Q_GVS", max_digits=8, decimal_places=5, null=True, blank=True)
    id_kategor = models.IntegerField("ID_KATEGOR", null=True, blank=True)
    adres_sd = models.CharField("ADRES_SD", max_length=60, null=True, blank=True)
    adres_regi = models.CharField("ADRES_REGI", max_length=30, null=True, blank=True)
    telefon = models.CharField("TELEFON", max_length=20, null=True, blank=True)
    fax = models.CharField("FAX", max_length=8, null=True, blank=True)
    id_katabon = models.IntegerField("ID_KATABON", null=True, blank=True)
    cod_banka = models.IntegerField("COD_BANKA", null=True, blank=True)
    ras_chet = models.BigIntegerField("RAS_CHET", null=True, blank=True)
    fisk_cod = models.CharField("FISK_COD", max_length=11, null=True, blank=True)
    kor_chet = models.CharField("KOR_CHET", max_length=12, null=True, blank=True)
    direktor = models.CharField("DIREKTOR", max_length=20, null=True, blank=True)
    byhalter = models.CharField("BYHALTER", max_length=20, null=True, blank=True)
    id_koteln = models.IntegerField("ID_KOTELN", null=True, blank=True)
    id_poteri = models.IntegerField("ID_POTERI", null=True, blank=True)
    dngvs = models.DecimalField("DNGVS", max_digits=4, decimal_places=1, null=True, blank=True)
    dnotop = models.DecimalField("DNOTOP", max_digits=4, decimal_places=1, null=True, blank=True)
    poter_nag = models.DecimalField("POTER_NAG", max_digits=6, decimal_places=3, null=True, blank=True)
    poter_pr = models.DecimalField("POTER_PR", max_digits=6, decimal_places=3, null=True, blank=True)
    cod_pot = models.IntegerField("COD_POT", null=True, blank=True)
    nach_otpr = models.DecimalField("NACH_OTPR", max_digits=10, decimal_places=3, null=True, blank=True)
    nach_otnag = models.DecimalField("NACH_OTNAG", max_digits=10, decimal_places=3, null=True, blank=True)
    dn_pereras = models.IntegerField("DN_PERERAS", null=True, blank=True)
    tkf_perer = models.DecimalField("TKF_PERER", max_digits=5, decimal_places=3, null=True, blank=True)
    gkl_perer = models.DecimalField("GKL_PERER", max_digits=13, decimal_places=3, null=True, blank=True)
    posle_prib = models.IntegerField("POSLE_PRIB", null=True, blank=True)
    nacs_priso = models.DecimalField("NACS_PRISO", max_digits=10, decimal_places=3, null=True, blank=True)
    nach_gvs = models.DecimalField("NACH_GVS", max_digits=10, decimal_places=3, null=True, blank=True)
    nac_vsego = models.DecimalField("NAC_VSEGO", max_digits=10, decimal_places=3, null=True, blank=True)
    predopl = models.DecimalField("PREDOPL", max_digits=10, decimal_places=3, null=True, blank=True)
    accept = models.IntegerField("ACCEPT", null=True, blank=True)
    cod_buhg = models.IntegerField("COD_BUHG", null=True, blank=True)
    cod_ac = models.IntegerField("COD_AC", null=True, blank=True)
    nac_pogaz = models.DecimalField("NAC_POGAZ", max_digits=10, decimal_places=3, null=True, blank=True)
    otnos_dog = models.IntegerField("OTNOS_DOG", null=True, blank=True)
    nom_pribor = models.BigIntegerField("NOM_PRIBOR", null=True, blank=True)
    inf_pribor = models.IntegerField("INF_PRIBOR", null=True, blank=True)
    diam_nag = models.IntegerField("DIAM_NAG", null=True, blank=True)
    dlina_nag = models.IntegerField("DLINA_NAG", null=True, blank=True)
    diam_prib = models.IntegerField("DIAM_PRIB", null=True, blank=True)
    dlina_prib = models.IntegerField("DLINA_PRIB", null=True, blank=True)
    vd_limit = models.DecimalField("VD_LIMIT", max_digits=10, decimal_places=3, null=True, blank=True)
    ost_limit = models.DecimalField("OST_LIMIT", max_digits=10, decimal_places=3, null=True, blank=True)
    nach_finan = models.DecimalField("NACH_FINAN", max_digits=10, decimal_places=3, null=True, blank=True)
    nach_otopi = models.DecimalField("NACH_OTOPI", max_digits=10, decimal_places=3, null=True, blank=True)
    pasp_got = models.DateField("PASP_GOT", null=True, blank=True)
    poterschob = models.DecimalField("POTERSCHOB", max_digits=10, decimal_places=3, null=True, blank=True)
    poternagob = models.DecimalField("POTERNAGOB", max_digits=10, decimal_places=3, null=True, blank=True)
    nalich_pot = models.IntegerField("NALICH_POT", null=True, blank=True)
    fio_rukov = models.CharField("FIO_RUKOV", max_length=40, null=True, blank=True)
    nameobakt = models.CharField("NAMEOBAKT", max_length=180, null=True, blank=True)
    doljn_ruk = models.CharField("DOLJN_RUK", max_length=50, null=True, blank=True)
    ura_dom = models.CharField("URA_DOM", max_length=6, null=True, blank=True)
    ura_kv = models.CharField("URA_KV", max_length=5, null=True, blank=True)
    oba_dom = models.CharField("OBA_DOM", max_length=6, null=True, blank=True)
    oba_kv = models.CharField("OBA_KV", max_length=5, null=True, blank=True)
    data_reg = models.DateField("DATA_REG", null=True, blank=True)
    nom_reg = models.CharField("NOM_REG", max_length=15, null=True, blank=True)
    ser_reg = models.CharField("SER_REG", max_length=3, null=True, blank=True)
    ser_nom = models.CharField("SER_NOM", max_length=10, null=True, blank=True)
    mail = models.CharField("MAIL", max_length=40, null=True, blank=True)
    dataotpr = models.DateTimeField("DATAOTPR", null=True, blank=True)
    posle_pri1 = models.IntegerField("POSLE_PRI1", null=True, blank=True)
    posle_pri2 = models.IntegerField("POSLE_PRI2", null=True, blank=True)
    posle_pri3 = models.IntegerField("POSLE_PRI3", null=True, blank=True)
    posle_pri4 = models.IntegerField("POSLE_PRI4", null=True, blank=True)
    pris_nag1 = models.IntegerField("PRIS_NAG1", null=True, blank=True)
    pris_nag2 = models.IntegerField("PRIS_NAG2", null=True, blank=True)
    pris_nag3 = models.IntegerField("PRIS_NAG3", null=True, blank=True)
    pris_nag4 = models.IntegerField("PRIS_NAG4", null=True, blank=True)
    pris_nag5 = models.IntegerField("PRIS_NAG5", null=True, blank=True)
    pris_nag6 = models.IntegerField("PRIS_NAG6", null=True, blank=True)
    pris_nag7 = models.IntegerField("PRIS_NAG7", null=True, blank=True)
    pris_nag8 = models.IntegerField("PRIS_NAG8", null=True, blank=True)
    doljn_podp = models.CharField("DOLJN_PODP", max_length=200, null=True, blank=True)
    name_kot = models.CharField("NAME_KOT", max_length=25, null=True, blank=True)
    inf = models.TextField("INF", null=True, blank=True)
    perc_peni = models.IntegerField("PERC_PENI", null=True, blank=True)
    gorod = models.CharField("GOROD", max_length=12, null=True, blank=True)
    gorod_o = models.CharField("GOROD_O", max_length=12, null=True, blank=True)
    d_dog = models.DateField("D_DOG", null=True, blank=True)
    dn_dog = models.DateField("DN_DOG", null=True, blank=True)
    dk_dog = models.DateField("DK_DOG", null=True, blank=True)
    d_stat = models.IntegerField("D_STAT", null=True, blank=True)
    d_stat_val = models.CharField("D_STAT_VAL", max_length=13, null=True, blank=True)
    ao_code = models.CharField("AO_CODE", max_length=31, null=True, blank=True)
    ao_code_o = models.CharField("AO_CODE_O", max_length=31, null=True, blank=True)
    stat_ob = models.IntegerField("STAT_OB", null=True, blank=True)
    name_banka = models.CharField("NAME_BANKA", max_length=30, null=True, blank=True)
    gorod_val = models.CharField("GOROD_VAL", max_length=12, null=True, blank=True)
    nach_poslpr = models.DecimalField("NACH_POSLP", max_digits=12, decimal_places=4, null=True, blank=True)
    ipredpinim = models.BooleanField("IPREDPINIM", null=True)
    kodt = models.IntegerField("KODT", null=True, blank=True)
    pid_in = models.CharField("PID_IN", max_length=36, null=True, blank=True)
    org_in = models.CharField("ORG_IN", max_length=36, null=True, blank=True)
    rric_acn = models.CharField("RRIC_ACN", max_length=10, null=True, blank=True)
    doctype_id = models.BigIntegerField("DOCTYPE_ID", null=True, blank=True)
    mail_ras = models.BooleanField("MAIL_RAS", null=True)
    kredo_ras = models.BooleanField("KREDO_RAS", null=True)
    prim_chot = models.CharField("PRIM_CHOT", max_length=250, null=True, blank=True)
    prim_chgvs = models.CharField("PRIM_CHGVS", max_length=250, null=True, blank=True)
    pok_newg = models.BigIntegerField("POK_NEWG", null=True, blank=True)
    pok_oldg = models.BigIntegerField("POK_OLDG", null=True, blank=True)
    vid_topl = models.BooleanField("VID_TOPL", null=True)
    a_type = models.IntegerField("A_TYPE", null=True, blank=True)
    liz = models.CharField("LIZ", max_length=6, null=True, blank=True)
    poter_gvs = models.DecimalField("POTER_GVS", max_digits=10, decimal_places=3, null=True, blank=True)
    date_pok = models.DateField("DATE_POK", null=True, blank=True)
    users_name = models.CharField("USERS_NAME", max_length=100, null=True, blank=True)
    pos_name = models.CharField("POS_NAME", max_length=200, null=True, blank=True)
    account = models.CharField("ACCOUNT", max_length=10, null=True, blank=True)

    class Meta:
        db_table = "potreb"
        verbose_name = "POTREB"
        verbose_name_plural = "POTREB"
        ordering = ["pk"]


class Potreb1(DbfModel):
    """potreb1.dbf (таблица базы): записей 17, кодировка cp1251."""

    dbf_source = "potreb1.dbf"

    nom_dogab = models.IntegerField("NOM_DOGAB", null=True, blank=True)
    s_potreb = models.DecimalField("S_POTREB", max_digits=7, decimal_places=1, null=True, blank=True)

    class Meta:
        db_table = "potreb1"
        verbose_name = "POTREB1"
        verbose_name_plural = "POTREB1"
        ordering = ["pk"]


class PotrebA(DbfModel):
    """Potreb_a.DBF (таблица базы): записей 174, кодировка cp1251."""

    dbf_source = "Potreb_a.DBF"

    s_potreb = models.DecimalField("S_POTREB", max_digits=7, decimal_places=1, null=True, blank=True)
    nom_dogab = models.IntegerField("NOM_DOGAB", null=True, blank=True)
    s_obshaya = models.DecimalField("S_OBSHAYA", max_digits=7, decimal_places=1, null=True, blank=True)
    nom_dog = models.IntegerField("NOM_DOG", null=True, blank=True)
    nach_otopl = models.DecimalField("NACH_OTOPL", max_digits=8, decimal_places=2, null=True, blank=True)
    nach_otsub = models.DecimalField("NACH_OTSUB", max_digits=8, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "potreb_a"
        verbose_name = "POTREB_A"
        verbose_name_plural = "POTREB_A"
        ordering = ["pk"]


class PotrebKoteln(DbfModel):
    """potreb_koteln.dbf (таблица базы): записей 175, кодировка cp1251."""

    dbf_source = "potreb_koteln.dbf"

    nach_otopl = models.DecimalField("NACH_OTOPL", max_digits=8, decimal_places=2, null=True, blank=True)
    cod_gor = models.ForeignKey("Danrasch", models.PROTECT, verbose_name="COD_GOR", to_field="cod_gorod", db_column="cod_gor", null=True, blank=True)
    id_koteln = models.IntegerField("ID_KOTELN", null=True, blank=True)
    name_kot = models.CharField("NAME_KOT", max_length=20, null=True, blank=True)

    class Meta:
        db_table = "potreb_koteln"
        verbose_name = "POTREB_KOTELN"
        verbose_name_plural = "POTREB_KOTELN"
        ordering = ["pk"]


class Potrebv(DbfModel):
    """potrebv.dbf (свободная таблица): записей 812, кодировка cp1251."""

    dbf_source = "potrebv.dbf"

    s_potreb = models.DecimalField("S_POTREB", max_digits=7, decimal_places=1, null=True, blank=True)
    nom_dogab = models.IntegerField("NOM_DOGAB", null=True, blank=True)
    s_obshaya = models.DecimalField("S_OBSHAYA", max_digits=7, decimal_places=1, null=True, blank=True)
    nom_dog = models.IntegerField("NOM_DOG", null=True, blank=True)
    tip_rasgvs = models.IntegerField("TIP_RASGVS", null=True, blank=True)
    tip_rasot = models.IntegerField("TIP_RASOT", null=True, blank=True)
    data_aktao = models.DateField("DATA_AKTAO", null=True, blank=True)
    nom_aktao = models.IntegerField("NOM_AKTAO", null=True, blank=True)
    data_otkot = models.DateField("DATA_OTKOT", null=True, blank=True)
    data_pdotp = models.DateField("DATA_PDOTP", null=True, blank=True)
    data_aktag = models.DateField("DATA_AKTAG", null=True, blank=True)
    nom_aktag = models.CharField("NOM_AKTAG", max_length=3, null=True, blank=True)
    data_otgvs = models.DateField("DATA_OTGVS", null=True, blank=True)
    data_pdgvs = models.DateField("DATA_PDGVS", null=True, blank=True)
    nach_otsub = models.DecimalField("NACH_OTSUB", max_digits=8, decimal_places=2, null=True, blank=True)
    nach_otopl = models.DecimalField("NACH_OTOPL", max_digits=8, decimal_places=2, null=True, blank=True)
    glav_potre = models.CharField("GLAV_POTRE", max_length=180, null=True, blank=True)
    pok_new = models.DecimalField("POK_NEW", max_digits=8, decimal_places=2, null=True, blank=True)
    pok_old = models.DecimalField("POK_OLD", max_digits=8, decimal_places=2, null=True, blank=True)
    koef_pok = models.DecimalField("KOEF_POK", max_digits=5, decimal_places=3, null=True, blank=True)
    cod_gor = models.ForeignKey("Danrasch", models.PROTECT, verbose_name="COD_GOR", to_field="cod_gorod", db_column="cod_gor", null=True, blank=True)
    potreb_id = models.IntegerField("POTREB_ID", null=True, blank=True)
    data_dog = models.DateField("DATA_DOG", null=True, blank=True)
    name_potre = models.CharField("NAME_POTRE", max_length=180, null=True, blank=True)
    cod_minist = models.ForeignKey("Minist", models.PROTECT, verbose_name="COD_MINIST", to_field="cod_minist", db_column="cod_minist", null=True, blank=True)
    v_zdan = models.DecimalField("V_ZDAN", max_digits=7, decimal_places=1, null=True, blank=True)
    v_zdanpr = models.DecimalField("V_ZDANPR", max_digits=7, decimal_places=1, null=True, blank=True)
    q_otop = models.DecimalField("Q_OTOP", max_digits=8, decimal_places=5, null=True, blank=True)
    q_otopobsh = models.DecimalField("Q_OTOPOBSH", max_digits=8, decimal_places=5, null=True, blank=True)
    q_otoppr = models.DecimalField("Q_OTOPPR", max_digits=8, decimal_places=5, null=True, blank=True)
    q_gvs = models.DecimalField("Q_GVS", max_digits=8, decimal_places=5, null=True, blank=True)
    id_kategor = models.IntegerField("ID_KATEGOR", null=True, blank=True)
    adres_sd = models.CharField("ADRES_SD", max_length=60, null=True, blank=True)
    adres_regi = models.CharField("ADRES_REGI", max_length=30, null=True, blank=True)
    telefon = models.CharField("TELEFON", max_length=20, null=True, blank=True)
    fax = models.CharField("FAX", max_length=8, null=True, blank=True)
    id_katabon = models.IntegerField("ID_KATABON", null=True, blank=True)
    cod_banka = models.IntegerField("COD_BANKA", null=True, blank=True)
    ras_chet = models.BigIntegerField("RAS_CHET", null=True, blank=True)
    fisk_cod = models.CharField("FISK_COD", max_length=11, null=True, blank=True)
    kor_chet = models.CharField("KOR_CHET", max_length=12, null=True, blank=True)
    direktor = models.CharField("DIREKTOR", max_length=20, null=True, blank=True)
    byhalter = models.CharField("BYHALTER", max_length=20, null=True, blank=True)
    id_koteln = models.IntegerField("ID_KOTELN", null=True, blank=True)
    id_poteri = models.IntegerField("ID_POTERI", null=True, blank=True)
    dngvs = models.DecimalField("DNGVS", max_digits=4, decimal_places=1, null=True, blank=True)
    dnotop = models.DecimalField("DNOTOP", max_digits=4, decimal_places=1, null=True, blank=True)
    poter_nag = models.DecimalField("POTER_NAG", max_digits=5, decimal_places=2, null=True, blank=True)
    poter_pr = models.DecimalField("POTER_PR", max_digits=5, decimal_places=2, null=True, blank=True)
    cod_pot = models.IntegerField("COD_POT", null=True, blank=True)
    nach_otpr = models.DecimalField("NACH_OTPR", max_digits=10, decimal_places=2, null=True, blank=True)
    nach_otnag = models.DecimalField("NACH_OTNAG", max_digits=10, decimal_places=2, null=True, blank=True)
    dn_pereras = models.IntegerField("DN_PERERAS", null=True, blank=True)
    tkf_perer = models.DecimalField("TKF_PERER", max_digits=5, decimal_places=3, null=True, blank=True)
    gkl_perer = models.DecimalField("GKL_PERER", max_digits=10, decimal_places=2, null=True, blank=True)
    posle_prib = models.IntegerField("POSLE_PRIB", null=True, blank=True)
    nacs_priso = models.DecimalField("NACS_PRISO", max_digits=10, decimal_places=2, null=True, blank=True)
    nach_gvs = models.DecimalField("NACH_GVS", max_digits=10, decimal_places=2, null=True, blank=True)
    nac_vsego = models.DecimalField("NAC_VSEGO", max_digits=10, decimal_places=2, null=True, blank=True)
    predopl = models.DecimalField("PREDOPL", max_digits=10, decimal_places=2, null=True, blank=True)
    accept = models.IntegerField("ACCEPT", null=True, blank=True)
    cod_buhg = models.IntegerField("COD_BUHG", null=True, blank=True)
    cod_ac = models.IntegerField("COD_AC", null=True, blank=True)
    nac_pogaz = models.DecimalField("NAC_POGAZ", max_digits=10, decimal_places=2, null=True, blank=True)
    otnos_dog = models.IntegerField("OTNOS_DOG", null=True, blank=True)
    nom_pribor = models.BigIntegerField("NOM_PRIBOR", null=True, blank=True)
    inf_pribor = models.IntegerField("INF_PRIBOR", null=True, blank=True)
    diam_nag = models.IntegerField("DIAM_NAG", null=True, blank=True)
    dlina_nag = models.IntegerField("DLINA_NAG", null=True, blank=True)
    diam_prib = models.IntegerField("DIAM_PRIB", null=True, blank=True)
    dlina_prib = models.IntegerField("DLINA_PRIB", null=True, blank=True)
    vd_limit = models.DecimalField("VD_LIMIT", max_digits=10, decimal_places=3, null=True, blank=True)
    ost_limit = models.DecimalField("OST_LIMIT", max_digits=10, decimal_places=3, null=True, blank=True)
    nach_finan = models.DecimalField("NACH_FINAN", max_digits=10, decimal_places=3, null=True, blank=True)
    nach_otopi = models.DecimalField("NACH_OTOPI", max_digits=10, decimal_places=3, null=True, blank=True)
    pasp_got = models.DateField("PASP_GOT", null=True, blank=True)
    poterschob = models.DecimalField("POTERSCHOB", max_digits=10, decimal_places=3, null=True, blank=True)
    poternagob = models.DecimalField("POTERNAGOB", max_digits=10, decimal_places=3, null=True, blank=True)
    nalich_pot = models.IntegerField("NALICH_POT", null=True, blank=True)
    fio_rukov = models.CharField("FIO_RUKOV", max_length=40, null=True, blank=True)
    nameobakt = models.CharField("NAMEOBAKT", max_length=180, null=True, blank=True)
    doljn_ruk = models.CharField("DOLJN_RUK", max_length=50, null=True, blank=True)
    ura_dom = models.CharField("URA_DOM", max_length=6, null=True, blank=True)
    ura_kv = models.CharField("URA_KV", max_length=5, null=True, blank=True)
    oba_dom = models.CharField("OBA_DOM", max_length=6, null=True, blank=True)
    oba_kv = models.CharField("OBA_KV", max_length=5, null=True, blank=True)
    data_reg = models.DateField("DATA_REG", null=True, blank=True)
    nom_reg = models.CharField("NOM_REG", max_length=15, null=True, blank=True)
    ser_reg = models.CharField("SER_REG", max_length=3, null=True, blank=True)
    ser_nom = models.CharField("SER_NOM", max_length=10, null=True, blank=True)
    mail = models.CharField("MAIL", max_length=30, null=True, blank=True)
    dataotpr = models.DateTimeField("DATAOTPR", null=True, blank=True)
    posle_pri1 = models.IntegerField("POSLE_PRI1", null=True, blank=True)
    posle_pri2 = models.IntegerField("POSLE_PRI2", null=True, blank=True)
    posle_pri3 = models.IntegerField("POSLE_PRI3", null=True, blank=True)
    posle_pri4 = models.IntegerField("POSLE_PRI4", null=True, blank=True)
    pris_nag1 = models.IntegerField("PRIS_NAG1", null=True, blank=True)
    pris_nag2 = models.IntegerField("PRIS_NAG2", null=True, blank=True)
    pris_nag3 = models.IntegerField("PRIS_NAG3", null=True, blank=True)
    pris_nag4 = models.IntegerField("PRIS_NAG4", null=True, blank=True)
    pris_nag5 = models.IntegerField("PRIS_NAG5", null=True, blank=True)
    pris_nag6 = models.IntegerField("PRIS_NAG6", null=True, blank=True)
    pris_nag7 = models.IntegerField("PRIS_NAG7", null=True, blank=True)
    pris_nag8 = models.IntegerField("PRIS_NAG8", null=True, blank=True)
    doljn_podp = models.CharField("DOLJN_PODP", max_length=200, null=True, blank=True)
    name_kot = models.CharField("NAME_KOT", max_length=25, null=True, blank=True)
    inf = models.TextField("INF", null=True, blank=True)

    class Meta:
        db_table = "potrebv"
        verbose_name = "POTREBV"
        verbose_name_plural = "POTREBV"
        ordering = ["pk"]


class Povtor(DbfModel):
    """povtor.dbf (таблица базы): записей 195, кодировка cp1251."""

    dbf_source = "povtor.dbf"

    cod_buh = models.BigIntegerField("COD_BUH", null=True, blank=True)
    cod_ac = models.BigIntegerField("COD_AC", null=True, blank=True)
    id1 = models.BigIntegerField("ID1", null=True, blank=True)
    id2 = models.BigIntegerField("ID2", null=True, blank=True)

    class Meta:
        db_table = "povtor"
        verbose_name = "POVTOR"
        verbose_name_plural = "POVTOR"
        ordering = ["pk"]


class Povtor1(DbfModel):
    """povtor1.dbf (таблица базы): записей 1026, кодировка cp1251."""

    dbf_source = "povtor1.dbf"

    sch = models.BigIntegerField("SCH", null=True, blank=True)

    class Meta:
        db_table = "povtor1"
        verbose_name = "POVTOR1"
        verbose_name_plural = "POVTOR1"
        ordering = ["pk"]


class Primari(DbfModel):
    """Primari.dbf (таблица базы): записей 2, кодировка cp1251."""

    dbf_source = "Primari.dbf"

    id_prim = models.IntegerField("ID_PRIM", null=True, blank=True)
    name_prim = models.CharField("NAME_PRIM", max_length=11, null=True, blank=True)

    class Meta:
        db_table = "primari"
        verbose_name = "PRIMARI"
        verbose_name_plural = "PRIMARI"
        ordering = ["pk"]


class PromFaktpotreb(DbfModel):
    """prom_faktpotreb.dbf (таблица базы): записей 182, кодировка cp1251."""

    dbf_source = "prom_faktpotreb.dbf"

    name_potre = models.CharField("NAME_POTRE", max_length=90, null=True, blank=True)
    tarif = models.DecimalField("TARIF", max_digits=10, decimal_places=2, null=True, blank=True)
    nom_dog = models.BigIntegerField("NOM_DOG", null=True, blank=True)
    data_dog = models.DateField("DATA_DOG", null=True, blank=True)
    nac_1 = models.DecimalField("NAC_1", max_digits=10, decimal_places=2, null=True, blank=True)
    nac_2 = models.DecimalField("NAC_2", max_digits=10, decimal_places=2, null=True, blank=True)
    nac_3 = models.DecimalField("NAC_3", max_digits=10, decimal_places=2, null=True, blank=True)
    nac_4 = models.DecimalField("NAC_4", max_digits=10, decimal_places=2, null=True, blank=True)
    nac_5 = models.DecimalField("NAC_5", max_digits=10, decimal_places=2, null=True, blank=True)
    nac_6 = models.DecimalField("NAC_6", max_digits=10, decimal_places=2, null=True, blank=True)
    nac_7 = models.DecimalField("NAC_7", max_digits=10, decimal_places=2, null=True, blank=True)
    nac_8 = models.DecimalField("NAC_8", max_digits=10, decimal_places=2, null=True, blank=True)
    nac_9 = models.DecimalField("NAC_9", max_digits=10, decimal_places=2, null=True, blank=True)
    nac_10 = models.DecimalField("NAC_10", max_digits=10, decimal_places=2, null=True, blank=True)
    nac_11 = models.DecimalField("NAC_11", max_digits=10, decimal_places=2, null=True, blank=True)
    nac_12 = models.DecimalField("NAC_12", max_digits=10, decimal_places=2, null=True, blank=True)
    id_kategor = models.BigIntegerField("ID_KATEGOR", null=True, blank=True)
    id_katabon = models.BigIntegerField("ID_KATABON", null=True, blank=True)
    cod_minist = models.ForeignKey("Minist", models.PROTECT, verbose_name="COD_MINIST", to_field="cod_minist", db_column="cod_minist", null=True, blank=True)
    potreb_id = models.BigIntegerField("POTREB_ID", null=True, blank=True)
    cod_gor = models.ForeignKey("Danrasch", models.PROTECT, verbose_name="COD_GOR", to_field="cod_gorod", db_column="cod_gor", null=True, blank=True)

    class Meta:
        db_table = "prom_faktpotreb"
        verbose_name = "PROM_FAKTPOTREB"
        verbose_name_plural = "PROM_FAKTPOTREB"
        ordering = ["pk"]


class RasAbonenta(DbfModel):
    """ras_abonenta.dbf (таблица базы): записей 0, кодировка cp1251."""

    dbf_source = "ras_abonenta.dbf"

    t_vozd = models.DecimalField("T_VOZD", max_digits=5, decimal_places=1, null=True, blank=True)
    t_koef = models.DecimalField("T_KOEF", max_digits=5, decimal_places=3, null=True, blank=True)
    nach_gvs = models.DecimalField("NACH_GVS", max_digits=10, decimal_places=2, null=True, blank=True)
    nach_otopl = models.DecimalField("NACH_OTOPL", max_digits=10, decimal_places=2, null=True, blank=True)
    predopl = models.DecimalField("PREDOPL", max_digits=10, decimal_places=2, null=True, blank=True)
    period = models.CharField("PERIOD", max_length=20, null=True, blank=True)
    poter_nag = models.DecimalField("POTER_NAG", max_digits=10, decimal_places=3, null=True, blank=True)
    poter_pr = models.DecimalField("POTER_PR", max_digits=10, decimal_places=3, null=True, blank=True)
    nach_otnag = models.DecimalField("NACH_OTNAG", max_digits=10, decimal_places=4, null=True, blank=True)
    nach_otpr = models.DecimalField("NACH_OTPR", max_digits=10, decimal_places=4, null=True, blank=True)
    q_otoppr = models.DecimalField("Q_OTOPPR", max_digits=10, decimal_places=4, null=True, blank=True)
    dnotop = models.BigIntegerField("DNOTOP", null=True, blank=True)
    gkl_perer = models.DecimalField("GKL_PERER", max_digits=10, decimal_places=3, null=True, blank=True)

    class Meta:
        db_table = "ras_abonenta"
        verbose_name = "RAS_ABONENTA"
        verbose_name_plural = "RAS_ABONENTA"
        ordering = ["pk"]


class ReestrDog(DbfModel):
    """reestr_dog.dbf (таблица базы): записей 231, кодировка cp1251."""

    dbf_source = "reestr_dog.dbf"

    nom_dog = models.IntegerField("NOM_DOG", null=True, blank=True)
    name_potre = models.CharField("NAME_POTRE", max_length=180, null=True, blank=True)
    id_kategor = models.IntegerField("ID_KATEGOR", null=True, blank=True)
    cod_minist = models.ForeignKey("Minist", models.PROTECT, verbose_name="COD_MINIST", to_field="cod_minist", db_column="cod_minist", null=True, blank=True)
    cod_gor = models.ForeignKey("Danrasch", models.PROTECT, verbose_name="COD_GOR", to_field="cod_gorod", db_column="cod_gor", null=True, blank=True)
    data_dog = models.DateField("DATA_DOG", null=True, blank=True)

    class Meta:
        db_table = "reestr_dog"
        verbose_name = "REESTR_DOG"
        verbose_name_plural = "REESTR_DOG"
        ordering = ["pk"]


class ReestrMail(DbfModel):
    """reestr_mail.dbf (таблица базы): записей 7, кодировка cp1251."""

    dbf_source = "reestr_mail.dbf"

    nom_dog = models.IntegerField("NOM_DOG", null=True, blank=True)
    potreb_id = models.ForeignKey("Potreb", models.PROTECT, verbose_name="POTREB_ID", to_field="potreb_id", db_column="potreb_id", null=True, blank=True)
    name_potre = models.CharField("NAME_POTRE", max_length=90, null=True, blank=True)
    dataotpr = models.DateTimeField("DATAOTPR", null=True, blank=True)
    name_gorod = models.CharField("NAME_GOROD", max_length=9, null=True, blank=True)

    class Meta:
        db_table = "reestr_mail"
        verbose_name = "REESTR_MAIL"
        verbose_name_plural = "REESTR_MAIL"
        ordering = ["pk"]


class Reestrmail2(DbfModel):
    """reestrmail.dbf (таблица базы): записей 16861, кодировка cp1251."""

    dbf_source = "reestrmail.dbf"
    dbf_columns = {"id_dbf": "ID"}

    id_dbf = models.IntegerField("ID", null=True, blank=True)
    nameabon = models.CharField("NAMEABON", max_length=100, null=True, blank=True)
    dataotpr = models.DateTimeField("DATAOTPR", null=True, blank=True)
    poterigkl = models.DecimalField("POTERIGKL", max_digits=10, decimal_places=4, null=True, blank=True)
    nachgkl = models.DecimalField("NACHGKL", max_digits=10, decimal_places=4, null=True, blank=True)
    ln = models.CharField("LN", max_length=10, null=True, blank=True)
    nomdog = models.CharField("NOMDOG", max_length=10, null=True, blank=True)
    gorod = models.IntegerField("GOROD", null=True, blank=True)
    mes = models.CharField("MES", max_length=10, null=True, blank=True)
    god = models.CharField("GOD", max_length=4, null=True, blank=True)

    class Meta:
        db_table = "reestrmail"
        verbose_name = "REESTRMAIL"
        verbose_name_plural = "REESTRMAIL"
        ordering = ["pk"]


class SetUrabon(DbfModel):
    """Set_URAbon.DBF (таблица базы): записей 130, кодировка cp1251."""

    dbf_source = "Set_URAbon.DBF"
    dbf_columns = {"a_name_full": "A_NAME_FUL", "a_name_short": "A_NAME_SHO"}

    liz = models.CharField("LIZ", max_length=10, null=True, blank=True)
    a_type = models.BigIntegerField("A_TYPE", null=True, blank=True)
    a_name_full = models.CharField("A_NAME_FUL", max_length=240, null=True, blank=True)
    ao_code = models.CharField("AO_CODE", max_length=31, null=True, blank=True)
    house = models.CharField("HOUSE", max_length=10, null=True, blank=True)
    flat = models.CharField("FLAT", max_length=10, null=True, blank=True)
    ru_name = models.CharField("RU_NAME", max_length=20, null=True, blank=True)
    ru_phone = models.CharField("RU_PHONE", max_length=10, null=True, blank=True)
    fiscode = models.CharField("FISCODE", max_length=10, null=True, blank=True)
    rs = models.CharField("RS", max_length=25, null=True, blank=True)
    bank = models.CharField("BANK", max_length=50, null=True, blank=True)
    a_name_short = models.CharField("A_NAME_SHO", max_length=200, null=True, blank=True)
    account = models.CharField("ACCOUNT", max_length=10, null=True, blank=True)

    class Meta:
        db_table = "set_urabon"
        verbose_name = "SET_URABON"
        verbose_name_plural = "SET_URABON"
        ordering = ["pk"]


class SetUrdevice(DbfModel):
    """set_urdevice.dbf (таблица базы): записей 227, кодировка cp1251."""

    dbf_source = "set_urdevice.dbf"
    dbf_columns = {"del_dbf": "DEL"}

    liz = models.CharField("Номер лицевого счёта абонента", max_length=10, null=True, blank=True)
    p_kod = models.CharField("Номер лицевого счёта потребителя", max_length=10, null=True, blank=True)
    d_kod = models.CharField("Код прибора учёта", max_length=10, null=True, blank=True)
    d_tip = models.BigIntegerField("Код типа прибора учёта", null=True, blank=True)
    d_num = models.CharField("Номер прибора", max_length=10, null=True, blank=True)
    d_date = models.DateField("Дата установки", null=True, blank=True)
    d_mesto = models.BigIntegerField("Код места установки", null=True, blank=True)
    d_pok = models.BigIntegerField("Показания при установке", null=True, blank=True)
    d_pov = models.DateField("Дата последней поверки", null=True, blank=True)
    d_prov = models.DateField("Дата последней проверки", null=True, blank=True)
    d_stat = models.BigIntegerField("Статус прибора учёта", null=True, blank=True)
    d_next_pov = models.DateField("Дата следующей поверки", null=True, blank=True)
    balans = models.IntegerField("BALANS", null=True, blank=True)
    koef = models.DecimalField("KOEF", max_digits=8, decimal_places=2, null=True, blank=True)
    del_dbf = models.IntegerField("DEL", null=True, blank=True)

    class Meta:
        db_table = "set_urdevice"
        verbose_name = "Информация о приборах учёта"
        verbose_name_plural = "Информация о приборах учёта"
        ordering = ["pk"]


class SetUrdevicelist(DbfModel):
    """Set_URDeviceList.DBF (таблица базы): записей 18, кодировка cp1251."""

    dbf_source = "Set_URDeviceList.DBF"

    kod = models.CharField("Код прибора учёта", max_length=10, null=True, blank=True)
    name = models.CharField("Наименование прибора учёта (марка)", max_length=20, null=True, blank=True)
    tip_kod = models.BigIntegerField("Код типа прибора учёта", null=True, blank=True)
    firma = models.CharField("Наименование производителя", max_length=10, null=True, blank=True)
    kol_razr = models.BigIntegerField("Значность", null=True, blank=True)
    tochn = models.BigIntegerField("Точность", null=True, blank=True)
    koef = models.DecimalField("Коэффициент перевода в Гкал", max_digits=8, decimal_places=2, null=True, blank=True)
    edn = models.CharField("Единица измерения счётчика", max_length=10, null=True, blank=True)
    p_date = models.IntegerField("Период поверки", null=True, blank=True)
    stat = models.IntegerField("Статус записи справочника", null=True, blank=True)

    class Meta:
        db_table = "set_urdevicelist"
        verbose_name = "Приборы учёта"
        verbose_name_plural = "Приборы учёта"
        ordering = ["pk"]


class SetUrdevicemeters(DbfModel):
    """Set_URDeviceMeters.DBF (свободная таблица): записей 8, кодировка cp1251."""

    dbf_source = "Set_URDeviceMeters.DBF"

    liz = models.CharField("LIZ", max_length=15, null=True, blank=True)
    p_kod = models.CharField("P_KOD", max_length=15, null=True, blank=True)
    d_kod = models.CharField("D_KOD", max_length=15, null=True, blank=True)
    d_tip = models.BigIntegerField("D_TIP", null=True, blank=True)
    d_num = models.CharField("D_NUM", max_length=15, null=True, blank=True)
    tip_pok = models.IntegerField("TIP_POK", null=True, blank=True)
    last_pok = models.DecimalField("LAST_POK", max_digits=12, decimal_places=2, null=True, blank=True)
    pok_date = models.DateField("POK_DATE", null=True, blank=True)

    class Meta:
        db_table = "set_urdevicemeters"
        verbose_name = "SET_URDEVICEMETERS"
        verbose_name_plural = "SET_URDEVICEMETERS"
        ordering = ["pk"]


class SetUrdevplacelist(DbfModel):
    """Set_URDevPlaceList.DBF (таблица базы): записей 4, кодировка cp1251."""

    dbf_source = "Set_URDevPlaceList.DBF"

    kod = models.BigIntegerField("Код места установки", null=True, blank=True)
    name = models.CharField("Наименование места установки", max_length=30, null=True, blank=True)
    stat = models.IntegerField("Статус записи справочника", null=True, blank=True)

    class Meta:
        db_table = "set_urdevplacelist"
        verbose_name = "Места установки приборов учёта"
        verbose_name_plural = "Места установки приборов учёта"
        ordering = ["pk"]


class SetUrdevtypelist(DbfModel):
    """Set_URDevTypeList.DBF (таблица базы): записей 1, кодировка cp1251."""

    dbf_source = "Set_URDevTypeList.DBF"

    kod = models.BigIntegerField("Код типа прибора учёта", null=True, blank=True)
    name = models.CharField("Наименование типа прибора учёта", max_length=200, null=True, blank=True)
    stat = models.IntegerField("Статус записи справочника", null=True, blank=True)

    class Meta:
        db_table = "set_urdevtypelist"
        verbose_name = "Типы приборов учёта"
        verbose_name_plural = "Типы приборов учёта"
        ordering = ["pk"]


class SetUrdocument(DbfModel):
    """Set_URDocument.DBF (свободная таблица): записей 1, кодировка cp1251."""

    dbf_source = "Set_URDocument.DBF"

    ret_kod = models.IntegerField("RET_KOD", null=True, blank=True)
    ret_val = models.CharField("RET_VAL", max_length=60, null=True, blank=True)

    class Meta:
        db_table = "set_urdocument"
        verbose_name = "SET_URDOCUMENT"
        verbose_name_plural = "SET_URDOCUMENT"
        ordering = ["pk"]


class SetUrdogv(DbfModel):
    """Set_URDogv.DBF (таблица базы): записей 58, кодировка cp1251."""

    dbf_source = "Set_URDogv.DBF"

    liz = models.CharField("LIZ", max_length=10, null=True, blank=True)
    tip = models.CharField("TIP", max_length=10, null=True, blank=True)
    n_dog = models.CharField("N_DOG", max_length=10, null=True, blank=True)
    d_dog = models.DateField("D_DOG", null=True, blank=True)
    dn_dog = models.DateField("DN_DOG", null=True, blank=True)
    dk_dog = models.DateField("DK_DOG", null=True, blank=True)
    d_stat = models.BigIntegerField("D_STAT", null=True, blank=True)

    class Meta:
        db_table = "set_urdogv"
        verbose_name = "SET_URDOGV"
        verbose_name_plural = "SET_URDOGV"
        ordering = ["pk"]


class SetUrplomb(DbfModel):
    """set_urplomb.dbf (таблица базы): записей 0, кодировка cp1251."""

    dbf_source = "set_urplomb.dbf"

    liz = models.CharField("LIZ", max_length=10, null=True, blank=True)
    p_kod = models.CharField("P_KOD", max_length=10, null=True, blank=True)
    d_kod = models.CharField("D_KOD", max_length=10, null=True, blank=True)
    d_num = models.CharField("D_NUM", max_length=10, null=True, blank=True)
    pl_num = models.CharField("PL_NUM", max_length=10, null=True, blank=True)
    pl_kod = models.BigIntegerField("PL_KOD", null=True, blank=True)
    pl_date = models.DateField("PL_DATE", null=True, blank=True)
    pl_mesto = models.BigIntegerField("PL_MESTO", null=True, blank=True)
    pl_stat = models.IntegerField("PL_STAT", null=True, blank=True)
    fio_oplb = models.CharField("FIO_OPLB", max_length=50, null=True, blank=True)

    class Meta:
        db_table = "set_urplomb"
        verbose_name = "SET_URPLOMB"
        verbose_name_plural = "SET_URPLOMB"
        ordering = ["pk"]


class SetUrplomblist(DbfModel):
    """set_URPlombList.dbf (свободная таблица): записей 0, кодировка cp1251."""

    dbf_source = "set_URPlombList.dbf"

    kod = models.BigIntegerField("Код типа пломбы", null=True, blank=True)
    name = models.CharField("Наименование пломбы", max_length=20, null=True, blank=True)
    stat = models.BigIntegerField("Статус записи справочника", null=True, blank=True)

    class Meta:
        db_table = "set_urplomblist"
        verbose_name = "Типы пломб"
        verbose_name_plural = "Типы пломб"
        ordering = ["pk"]


class SetUrplombplacelist(DbfModel):
    """Set_URPlombPlaceList.dbf (таблица базы): записей 0, кодировка cp1251."""

    dbf_source = "Set_URPlombPlaceList.dbf"

    kod = models.BigIntegerField("KOD", null=True, blank=True)
    name = models.CharField("NAME", max_length=30, null=True, blank=True)
    stat = models.BigIntegerField("STAT", null=True, blank=True)

    class Meta:
        db_table = "set_urplombplacelist"
        verbose_name = "SET_URPLOMBPLACELIST"
        verbose_name_plural = "SET_URPLOMBPLACELIST"
        ordering = ["pk"]


class SetUrpotr(DbfModel):
    """Set_URPotr.DBF (таблица базы): записей 130, кодировка cp1251."""

    dbf_source = "Set_URPotr.DBF"

    liz = models.CharField("LIZ", max_length=10, null=True, blank=True)
    p_kod = models.CharField("P_KOD", max_length=10, null=True, blank=True)
    p_name = models.CharField("P_NAME", max_length=250, null=True, blank=True)
    ao_code = models.CharField("AO_CODE", max_length=32, null=True, blank=True)
    house = models.CharField("HOUSE", max_length=10, null=True, blank=True)
    flat = models.CharField("FLAT", max_length=10, null=True, blank=True)
    stat = models.IntegerField("STAT", null=True, blank=True)

    class Meta:
        db_table = "set_urpotr"
        verbose_name = "SET_URPOTR"
        verbose_name_plural = "SET_URPOTR"
        ordering = ["pk"]


class SmtpNas(DbfModel):
    """smtp_nas.dbf (таблица базы): записей 1, кодировка cp1251."""

    dbf_source = "smtp_nas.dbf"
    dbf_columns = {"from_dbf": "FROM"}

    tema = models.CharField("TEMA", max_length=50, null=True, blank=True)
    pismo = models.CharField("PISMO", max_length=254, null=True, blank=True)
    from_dbf = models.CharField("FROM", max_length=70, null=True, blank=True)
    sendusing = models.IntegerField("SENDUSING", null=True, blank=True)
    smtp = models.CharField("SMTP", max_length=50, null=True, blank=True)
    port = models.IntegerField("PORT", null=True, blank=True)
    paunt = models.IntegerField("PAUNT", null=True, blank=True)
    password = models.CharField("PASSWORD", max_length=40, null=True, blank=True)
    puses = models.IntegerField("PUSES", null=True, blank=True)
    timeout = models.IntegerField("TIMEOUT", null=True, blank=True)
    senduserna = models.CharField("SENDUSERNA", max_length=50, null=True, blank=True)
    nom_dov = models.CharField("NOM_DOV", max_length=10, null=True, blank=True)
    data_dov = models.DateField("DATA_DOV", null=True, blank=True)

    class Meta:
        db_table = "smtp_nas"
        verbose_name = "Настройка рассылки писем"
        verbose_name_plural = "Настройка рассылки писем"
        ordering = ["pk"]


class SpBank(DbfModel):
    """sp_bank.dbf (таблица базы): записей 2, кодировка cp1251."""

    dbf_source = "sp_bank.dbf"

    name = models.CharField("Наименование банка", max_length=250, null=True, blank=True)
    sity = models.CharField("Город", max_length=20, null=True, blank=True)
    kub16 = models.CharField("Куб банка", max_length=20, null=True, blank=True)
    ur_adres = models.CharField("Юридический адрес", max_length=250, null=True, blank=True)
    fisk_cod = models.CharField("Фискальный код", max_length=30, null=True, blank=True)
    kor_chet = models.CharField("Корреспондентский счёт", max_length=30, null=True, blank=True)
    tel_priemn = models.CharField("Номер телефона приёмной", max_length=50, null=True, blank=True)
    fax = models.CharField("Номер факса", max_length=20, null=True, blank=True)
    mail = models.CharField("Адрес электронной почты", max_length=50, null=True, blank=True)
    id_cod = models.IntegerField("id", null=True, blank=True)

    class Meta:
        db_table = "sp_bank"
        verbose_name = "Банки"
        verbose_name_plural = "Банки"
        ordering = ["pk"]


class SpDiametr(DbfModel):
    """sp_diametr.dbf (таблица базы): записей 9, кодировка cp1251."""

    dbf_source = "sp_diametr.dbf"

    id_diam = models.IntegerField("ID_DIAM", null=True, blank=True)
    diametr = models.IntegerField("DIAMETR", null=True, blank=True)

    class Meta:
        db_table = "sp_diametr"
        verbose_name = "SP_DIAMETR"
        verbose_name_plural = "SP_DIAMETR"
        ordering = ["pk"]


class SpSobpr(DbfModel):
    """Sp_SobPr.dbf (таблица базы): записей 2, кодировка cp1251."""

    dbf_source = "Sp_SobPr.dbf"

    kod = models.IntegerField("KOD", null=True, blank=True)
    sobst_prib = models.CharField("SOBST_PRIB", max_length=30, null=True, blank=True)

    class Meta:
        db_table = "sp_sobpr"
        verbose_name = "SP_SOBPR"
        verbose_name_plural = "SP_SOBPR"
        ordering = ["pk"]


class SpTeplosch(DbfModel):
    """sp_teplosch.dbf (таблица базы): записей 274, кодировка cp1251."""

    dbf_source = "sp_teplosch.dbf"

    ln = models.BigIntegerField("LN", null=True, blank=True)
    name_obek = models.CharField("NAME_OBEK", max_length=250, null=True, blank=True)
    adres_obek = models.CharField("ADRES_OBEK", max_length=50, null=True, blank=True)
    data_zapus = models.DateField("DATA_ZAPUS", null=True, blank=True)
    nomer_prib = models.CharField("NOMER_PRIB", max_length=20, null=True, blank=True)
    tip_prib = models.CharField("TIP_PRIB", max_length=20, null=True, blank=True)
    ndata_pov = models.DateField("NDATA_POV", null=True, blank=True)
    kdata_pov = models.DateField("KDATA_POV", null=True, blank=True)
    mesto_ust = models.CharField("MESTO_UST", max_length=200, null=True, blank=True)
    mesto_ustp = models.CharField("MESTO_USTP", max_length=200, null=True, blank=True)
    tip_kod = models.BigIntegerField("TIP_KOD", null=True, blank=True)

    class Meta:
        db_table = "sp_teplosch"
        verbose_name = "SP_TEPLOSCH"
        verbose_name_plural = "SP_TEPLOSCH"
        ordering = ["pk"]


class SpTeplpoteri(DbfModel):
    """sp_teplpoteri.dbf (таблица базы): записей 986, кодировка cp1251."""

    dbf_source = "sp_teplpoteri.dbf"

    ln = models.BigIntegerField("LN", null=True, blank=True)
    diametr1 = models.BigIntegerField("DIAMETR1", null=True, blank=True)
    dlina1 = models.DecimalField("DLINA1", max_digits=10, decimal_places=1, null=True, blank=True)
    poteri_pr1 = models.DecimalField("POTERI_PR1", max_digits=10, decimal_places=3, null=True, blank=True)
    diametr2 = models.BigIntegerField("DIAMETR2", null=True, blank=True)
    dlina2 = models.DecimalField("DLINA2", max_digits=10, decimal_places=1, null=True, blank=True)
    poteri_pr2 = models.DecimalField("POTERI_PR2", max_digits=10, decimal_places=3, null=True, blank=True)
    diametr3 = models.BigIntegerField("DIAMETR3", null=True, blank=True)
    dlina3 = models.DecimalField("DLINA3", max_digits=10, decimal_places=1, null=True, blank=True)
    poteri_pr3 = models.DecimalField("POTERI_PR3", max_digits=10, decimal_places=3, null=True, blank=True)
    diametr4 = models.BigIntegerField("DIAMETR4", null=True, blank=True)
    dlina4 = models.DecimalField("DLINA4", max_digits=10, decimal_places=1, null=True, blank=True)
    poteri_pr4 = models.DecimalField("POTERI_PR4", max_digits=10, decimal_places=3, null=True, blank=True)
    diametr5 = models.BigIntegerField("DIAMETR5", null=True, blank=True)
    dlina5 = models.DecimalField("DLINA5", max_digits=10, decimal_places=1, null=True, blank=True)
    poteri_pr5 = models.DecimalField("POTERI_PR5", max_digits=10, decimal_places=3, null=True, blank=True)
    diametr6 = models.BigIntegerField("DIAMETR6", null=True, blank=True)
    dlina6 = models.DecimalField("DLINA6", max_digits=10, decimal_places=1, null=True, blank=True)
    vs_poteri = models.DecimalField("VS_POTERI", max_digits=10, decimal_places=3, null=True, blank=True)
    poteri_pr6 = models.DecimalField("POTERI_PR6", max_digits=10, decimal_places=3, null=True, blank=True)

    class Meta:
        db_table = "sp_teplpoteri"
        verbose_name = "SP_TEPLPOTERI"
        verbose_name_plural = "SP_TEPLPOTERI"
        ordering = ["pk"]


class Sph(DbfModel):
    """sph.dbf (таблица базы): записей 27, кодировка cp1251."""

    dbf_source = "sph.dbf"

    tip_prib = models.CharField("TIP_PRIB", max_length=25, null=True, blank=True)
    tip_kod = models.BigIntegerField("TIP_KOD", null=True, blank=True)

    class Meta:
        db_table = "sph"
        verbose_name = "SPH"
        verbose_name_plural = "SPH"
        ordering = ["pk"]


class Spisok1(DbfModel):
    """spisok1.dbf (свободная таблица): записей 948, кодировка cp1251."""

    dbf_source = "spisok1.dbf"

    name_potre = models.CharField("NAME_POTRE", max_length=180, null=True, blank=True)
    glav_potre = models.CharField("GLAV_POTRE", max_length=180, null=True, blank=True)
    adres_sd = models.CharField("ADRES_SD", max_length=60, null=True, blank=True)
    q_otoppr = models.DecimalField("Q_OTOPPR", max_digits=8, decimal_places=5, null=True, blank=True)
    id_koteln = models.IntegerField("ID_KOTELN", null=True, blank=True)
    potreb_id = models.IntegerField("POTREB_ID", null=True, blank=True)
    name_kot = models.CharField("NAME_KOT", max_length=30, null=True, blank=True)
    cod_gor = models.ForeignKey("Danrasch", models.PROTECT, verbose_name="COD_GOR", to_field="cod_gorod", db_column="cod_gor", null=True, blank=True)

    class Meta:
        db_table = "spisok1"
        verbose_name = "SPISOK1"
        verbose_name_plural = "SPISOK1"
        ordering = ["pk"]


class Spisok2(DbfModel):
    """spisok2.dbf (свободная таблица): записей 821, кодировка cp1251."""

    dbf_source = "spisok2.dbf"

    q_otoppr = models.DecimalField("Q_OTOPPR", max_digits=8, decimal_places=5, null=True, blank=True)
    id_kategor = models.IntegerField("ID_KATEGOR", null=True, blank=True)
    cod_gor = models.ForeignKey("Danrasch", models.PROTECT, verbose_name="COD_GOR", to_field="cod_gorod", db_column="cod_gor", null=True, blank=True)
    name_kateg = models.CharField("NAME_KATEG", max_length=25, null=True, blank=True)

    class Meta:
        db_table = "spisok2"
        verbose_name = "SPISOK2"
        verbose_name_plural = "SPISOK2"
        ordering = ["pk"]


class Spisok3(DbfModel):
    """spisok3.dbf (свободная таблица): записей 925, кодировка cp1251."""

    dbf_source = "spisok3.dbf"

    q_otoppr = models.DecimalField("Q_OTOPPR", max_digits=8, decimal_places=5, null=True, blank=True)
    id_kategor = models.IntegerField("ID_KATEGOR", null=True, blank=True)
    cod_gor = models.ForeignKey("Danrasch", models.PROTECT, verbose_name="COD_GOR", to_field="cod_gorod", db_column="cod_gor", null=True, blank=True)
    name_kateg = models.CharField("NAME_KATEG", max_length=25, null=True, blank=True)

    class Meta:
        db_table = "spisok3"
        verbose_name = "SPISOK3"
        verbose_name_plural = "SPISOK3"
        ordering = ["pk"]


class Sprtch(DbfModel):
    """sprtch.DBF (таблица базы): записей 28, кодировка cp1251."""

    dbf_source = "sprtch.DBF"

    tip_prib = models.CharField("TIP_PRIB", max_length=25, null=True, blank=True)

    class Meta:
        db_table = "sprtch"
        verbose_name = "SPRTCH"
        verbose_name_plural = "SPRTCH"
        ordering = ["pk"]


class Spt(DbfModel):
    """spt.DBF (таблица базы): записей 54, кодировка cp1251."""

    dbf_source = "spt.DBF"

    tip_prib = models.CharField("TIP_PRIB", max_length=20, null=True, blank=True)

    class Meta:
        db_table = "spt"
        verbose_name = "SPT"
        verbose_name_plural = "SPT"
        ordering = ["pk"]


class StatZap(DbfModel):
    """Stat_zap.dbf (свободная таблица): записей 2, кодировка cp1251."""

    dbf_source = "Stat_zap.dbf"

    name = models.CharField("NAME", max_length=20, null=True, blank=True)
    kod = models.IntegerField("KOD", null=True, blank=True)

    class Meta:
        db_table = "stat_zap"
        verbose_name = "STAT_ZAP"
        verbose_name_plural = "STAT_ZAP"
        ordering = ["pk"]


class SubAbonent(DbfModel):
    """sub_abonent.DBF (таблица базы): записей 38, кодировка cp1251."""

    dbf_source = "sub_abonent.DBF"

    tip_rasgvs = models.IntegerField("TIP_RASGVS", null=True, blank=True)
    tip_rasot = models.IntegerField("TIP_RASOT", null=True, blank=True)
    data_aktao = models.DateField("DATA_AKTAO", null=True, blank=True)
    nom_aktao = models.IntegerField("NOM_AKTAO", null=True, blank=True)
    data_otkot = models.DateField("DATA_OTKOT", null=True, blank=True)
    data_pdotp = models.DateField("DATA_PDOTP", null=True, blank=True)
    data_aktag = models.DateField("DATA_AKTAG", null=True, blank=True)
    nom_aktag = models.CharField("NOM_AKTAG", max_length=3, null=True, blank=True)
    data_otgvs = models.DateField("DATA_OTGVS", null=True, blank=True)
    data_pdgvs = models.DateField("DATA_PDGVS", null=True, blank=True)
    nach_otgla = models.DecimalField("NACH_OTGLA", max_digits=8, decimal_places=2, null=True, blank=True)
    nach_otopl = models.DecimalField("NACH_OTOPL", max_digits=8, decimal_places=2, null=True, blank=True)
    glav_potre = models.CharField("GLAV_POTRE", max_length=90, null=True, blank=True)
    pok_new = models.DecimalField("POK_NEW", max_digits=8, decimal_places=2, null=True, blank=True)
    pok_old = models.DecimalField("POK_OLD", max_digits=8, decimal_places=2, null=True, blank=True)
    koef_pok = models.DecimalField("KOEF_POK", max_digits=5, decimal_places=3, null=True, blank=True)
    cod_gor = models.ForeignKey("Danrasch", models.PROTECT, verbose_name="COD_GOR", to_field="cod_gorod", db_column="cod_gor", null=True, blank=True)
    potreb_id = models.ForeignKey("Potreb", models.PROTECT, verbose_name="POTREB_ID", to_field="potreb_id", db_column="potreb_id", null=True, blank=True)
    nom_dog = models.IntegerField("NOM_DOG", null=True, blank=True)
    data_dog = models.DateField("DATA_DOG", null=True, blank=True)
    name_potre = models.CharField("NAME_POTRE", max_length=90, null=True, blank=True)
    cod_minist = models.ForeignKey("Minist", models.PROTECT, verbose_name="COD_MINIST", to_field="cod_minist", db_column="cod_minist", null=True, blank=True)
    v_zdan = models.DecimalField("V_ZDAN", max_digits=7, decimal_places=1, null=True, blank=True)
    v_zdanpr = models.DecimalField("V_ZDANPR", max_digits=7, decimal_places=1, null=True, blank=True)
    s_potreb = models.DecimalField("S_POTREB", max_digits=7, decimal_places=1, null=True, blank=True)
    s_obshaya = models.DecimalField("S_OBSHAYA", max_digits=7, decimal_places=1, null=True, blank=True)
    q_otop = models.DecimalField("Q_OTOP", max_digits=7, decimal_places=5, null=True, blank=True)
    q_otoppr = models.DecimalField("Q_OTOPPR", max_digits=7, decimal_places=5, null=True, blank=True)
    q_gvs = models.DecimalField("Q_GVS", max_digits=5, decimal_places=2, null=True, blank=True)
    id_kategor = models.IntegerField("ID_KATEGOR", null=True, blank=True)
    adres_sd = models.CharField("ADRES_SD", max_length=60, null=True, blank=True)
    adres_regi = models.CharField("ADRES_REGI", max_length=30, null=True, blank=True)
    telefon = models.CharField("TELEFON", max_length=20, null=True, blank=True)
    fax = models.CharField("FAX", max_length=8, null=True, blank=True)
    id_katabon = models.IntegerField("ID_KATABON", null=True, blank=True)
    cod_banka = models.IntegerField("COD_BANKA", null=True, blank=True)
    ras_chet = models.BigIntegerField("RAS_CHET", null=True, blank=True)
    fisk_cod = models.CharField("FISK_COD", max_length=11, null=True, blank=True)
    kor_chet = models.CharField("KOR_CHET", max_length=10, null=True, blank=True)
    direktor = models.CharField("DIREKTOR", max_length=20, null=True, blank=True)
    byhalter = models.CharField("BYHALTER", max_length=20, null=True, blank=True)
    id_koteln = models.IntegerField("ID_KOTELN", null=True, blank=True)
    id_poteri = models.IntegerField("ID_POTERI", null=True, blank=True)

    class Meta:
        db_table = "sub_abonent"
        verbose_name = "SUB_ABONENT"
        verbose_name_plural = "SUB_ABONENT"
        ordering = ["pk"]


class Tarif(DbfModel):
    """tarif.dbf (таблица базы): записей 12, кодировка cp1251."""

    dbf_source = "tarif.dbf"

    id_tar = models.IntegerField("№", null=True, blank=True)
    name_tar = models.CharField("Наименование", max_length=30, null=True, blank=True)
    zn_tar = models.DecimalField("Тариф (Г)", max_digits=6, decimal_places=2, null=True, blank=True)
    diz_tar = models.DecimalField("Тариф (Д)", max_digits=6, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "tarif"
        verbose_name = "Тарифы"
        verbose_name_plural = "Тарифы"
        ordering = ["pk"]


class Tarif2(DbfModel):
    """tarif_.dbf (свободная таблица): записей 13, кодировка cp1251."""

    dbf_source = "tarif_.dbf"

    id_tar = models.IntegerField("ID_TAR", null=True, blank=True)
    name_tar = models.CharField("NAME_TAR", max_length=30, null=True, blank=True)
    zn_tar = models.DecimalField("ZN_TAR", max_digits=6, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "tarif_2"
        verbose_name = "TARIF_"
        verbose_name_plural = "TARIF_"
        ordering = ["pk"]


class TeplPot(DbfModel):
    """tepl_pot.DBF (таблица базы): записей 2, кодировка cp1251."""

    dbf_source = "tepl_pot.DBF"

    id_proc = models.IntegerField("ID_PROC", null=True, blank=True)
    proc_pot = models.DecimalField("% потерь", max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "tepl_pot"
        verbose_name = "Тепловые потери"
        verbose_name_plural = "Тепловые потери"
        ordering = ["pk"]


class Tippotreb(DbfModel):
    """tippotreb.dbf (таблица базы): записей 2, кодировка cp1251."""

    dbf_source = "tippotreb.dbf"

    tip_potreb = models.IntegerField("TIP_POTREB", null=True, blank=True)
    name_tip = models.CharField("NAME_TIP", max_length=20, null=True, blank=True)

    class Meta:
        db_table = "tippotreb"
        verbose_name = "TIPPOTREB"
        verbose_name_plural = "TIPPOTREB"
        ordering = ["pk"]


class Udnorm(DbfModel):
    """udnorm.DBF (таблица базы): записей 5, кодировка cp1251."""

    dbf_source = "udnorm.DBF"

    id_norm = models.IntegerField("№", null=True, blank=True)
    name_norm = models.CharField("Наименование", max_length=40, null=True, blank=True)
    ud_norma = models.DecimalField("Уд. норма", max_digits=6, decimal_places=4, null=True, blank=True)

    class Meta:
        db_table = "udnorm"
        verbose_name = "Удельные нормы"
        verbose_name_plural = "Удельные нормы"
        ordering = ["pk"]


class VedPotreb(DbfModel):
    """ved_potreb.dbf (свободная таблица): записей 124, кодировка cp1251."""

    dbf_source = "ved_potreb.dbf"

    nom_dog = models.IntegerField("NOM_DOG", null=True, blank=True)
    name_potre = models.CharField("NAME_POTRE", max_length=180, null=True, blank=True)
    nach_otpr = models.DecimalField("NACH_OTPR", max_digits=10, decimal_places=3, null=True, blank=True)
    tip_rasot = models.IntegerField("TIP_RASOT", null=True, blank=True)
    cod_gor = models.ForeignKey("Danrasch", models.PROTECT, verbose_name="COD_GOR", to_field="cod_gorod", db_column="cod_gor", null=True, blank=True)
    id_katabon = models.IntegerField("ID_KATABON", null=True, blank=True)

    class Meta:
        db_table = "ved_potreb"
        verbose_name = "VED_POTREB"
        verbose_name_plural = "VED_POTREB"
        ordering = ["pk"]


class VedomMail(DbfModel):
    """vedom_mail.dbf (таблица базы): записей 78, кодировка cp1251."""

    dbf_source = "vedom_mail.dbf"

    nom_dog = models.IntegerField("NOM_DOG", null=True, blank=True)
    potreb_id = models.IntegerField("POTREB_ID", null=True, blank=True)
    name_potre = models.CharField("NAME_POTRE", max_length=90, null=True, blank=True)
    dataotpr = models.DateTimeField("DATAOTPR", null=True, blank=True)
    name_gorod = models.CharField("NAME_GOROD", max_length=9, null=True, blank=True)

    class Meta:
        db_table = "vedom_mail"
        verbose_name = "VEDOM_MAIL"
        verbose_name_plural = "VEDOM_MAIL"
        ordering = ["pk"]
