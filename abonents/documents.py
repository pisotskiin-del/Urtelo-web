"""Документы абоненту за месяц: «Информация-счёт» и «Акт о фактическом
потреблении тепловой энергии» (процедуры proced.info_potreb_* и
akt_potreb_pr, отчеты infpotreb1.frx, aktpotreb_p.frx старой программы).

Документ составляется по договору: все лицевые счета участка с тем же
номером договора, у которых договор заключён или возобновлён, по категориям
потребителей.

Деньги, как в старой программе:
- тариф по участку, категории, признаку «тариф для населения с
  возмещением» (kodt) и виду топлива (дизель — diz_tar);
- сумма строки = (отопление + ГВС) Гкал × тариф без округления. Потери ГВС
  в сумму не входят (решение 31.10.2026; так считала массовая рассылка
  auto_send_mail, а карта прибавляла poter_gvs);
- в строке печатается сумма, округлённая до копеек, итог категории — сумма
  неокруглённых строк, округлённая до копеек; разница строк и итога
  показывается как «Арифметическое отклонение».
"""

import datetime
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

from catalogs.models import Danrasch, Kategorpot, Potreb

from .layout import RASCHET

KOP = Decimal("0.01")

# Код тарифа: {участок: {категория: код}}; для категорий 4–6 при kodt=1 — код 12
# («тариф для населения с возмещением»). Коды — из tarif.dbf старой программы,
# значения берутся из тарифов участка (справочник «Тарифы»).
TARIF_KOD = {
    1: {1: 1, 2: 2, 3: 2, 4: 3, 5: 3, 6: 3, 7: 10},
    2: {1: 4, 2: 5, 3: 5, 4: 6, 5: 6, 6: 6, 7: 10},
    3: {1: 7, 2: 8, 3: 8, 4: 9, 5: 9, 6: 9, 7: 10},
}
TARIF_VOZMESH = 12
NASELENIE = (4, 5, 6)

# Лицевые счета, у которых старая программа не копила копеечный остаток и
# прибавляла копейку к итогу категории (proced.info_potreb_*; в карте 2026 года
# этот код закомментирован).
KOPEIKA_PLUS = (676, 1174)

# Лицевой счет, которому акт печатается по старому шаблону aktpotreb (без
# колонки адреса), остальным — aktpotreb_p.
AKT_STARYI = (124,)

ORG = {
    "name": 'МГУП "ТИРАСТЕПЛОЭНЕРГО"',
    "lines": ["MD-5500, г.Рыбница, ул.Маяковского, 43",
              "Тел.: (555) 32907, факс: (555) 31807",
              "Р/сч. 2211290000000025",
              "ЗАО «Приднестровский сбербанк»",
              "г.Тирасполь, КУБ 29",
              "ф/к 0200013318, Кор.сч. 20210000094"],
    "telefon": "32671",
    "email": "r.ourt@yandex.ru",
}

MES_IM = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август",
          "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
MES_PR = ["Январе", "Феврале", "Марте", "Апреле", "Мае", "Июне", "Июле", "Августе",
          "Сентябре", "Октябре", "Ноябре", "Декабре"]


def _d(v):
    return Decimal(v or 0)


def tarif_kod(gorod, kategor, kodt):
    kod = TARIF_KOD.get(gorod, {}).get(kategor)
    if kod and kategor in NASELENIE and kodt == 1:
        return TARIF_VOZMESH
    return kod


def tarif(p, tarify):
    """Тариф записи potreb; tarify — {код: (тариф, тариф для дизеля)} участка."""
    kod = tarif_kod(p.cod_gor_id, p.id_kategor, p.kodt)
    zn, diz = tarify.get(kod, (0, 0))
    return _d(diz if p.vid_topl else zn)


@dataclass
class Stroka:
    p: Potreb
    otopl: Decimal      # отопление без потерь
    gvs: Decimal
    poteri: Decimal     # потери отопления (по прибору и по нагрузке)
    gkal: Decimal       # итого Гкал: отопление с потерями + ГВС
    tarif: Decimal
    itog: Decimal       # сумма без округления

    @property
    def itog_r(self):
        return self.itog.quantize(KOP, ROUND_HALF_UP)

    @property
    def adres(self):
        p = self.p
        parts = [(p.adres_sd or "").strip(), (p.oba_dom or "").strip(), (p.oba_kv or "").strip()]
        return ("ул." + " ".join(x for x in parts if x)) if parts[0] else " ".join(x for x in parts if x)


@dataclass
class Kategoria:
    kod: int
    name: str
    stroki: list = field(default_factory=list)
    plus: Decimal = Decimal(0)

    def _sum(self, name):
        return sum((getattr(s, name) for s in self.stroki), Decimal(0))

    @property
    def otopl(self):
        return self._sum("otopl")

    @property
    def gvs(self):
        return self._sum("gvs")

    @property
    def poteri(self):
        return self._sum("poteri")

    @property
    def gkal(self):
        return self._sum("gkal")

    @property
    def tarif(self):
        t = {s.tarif for s in self.stroki}
        return t.pop() if len(t) == 1 else None

    @property
    def itog(self):
        """Итог категории: сумма неокруглённых строк, округлённая до копеек."""
        return (self._sum("itog") + self.plus).quantize(KOP, ROUND_HALF_UP)

    @property
    def otklonenie(self):
        """Арифметическое отклонение: копеечные остатки округления строк."""
        return sum((s.itog - s.itog_r for s in self.stroki if s.p.potreb_id not in KOPEIKA_PLUS),
                   Decimal(0)).quantize(KOP, ROUND_HALF_UP)


@dataclass
class Dokument:
    gorod: object          # Danrasch участка
    glav: Potreb           # запись, по которой берутся реквизиты договора
    kategorii: list
    data: datetime.date

    @property
    def nom_dog(self):
        return self.glav.nom_dog

    @property
    def mes(self):
        return self.gorod.nom_mes

    @property
    def god(self):
        return self.gorod.god

    @property
    def mes_im(self):
        return MES_IM[self.mes - 1] if self.mes else ""

    @property
    def mes_pr(self):
        return MES_PR[self.mes - 1] if self.mes else ""

    @property
    def stroki(self):
        return [s for k in self.kategorii for s in k.stroki]

    def _sum(self, name):
        return sum((getattr(k, name) for k in self.kategorii), Decimal(0))

    @property
    def otopl(self):
        return self._sum("otopl")

    @property
    def gvs(self):
        return self._sum("gvs")

    @property
    def poteri(self):
        return self._sum("poteri")

    @property
    def gkal(self):
        return self._sum("gkal")

    @property
    def itog(self):
        return self._sum("itog")

    @property
    def akt_staryi(self):
        return any(s.p.potreb_id in AKT_STARYI for s in self.stroki)

    @property
    def filename(self):
        """Имя PDF как в старой программе: <№ договора>_<л/№>.pdf."""
        return f"{self.nom_dog}_{self.glav.potreb_id}"


def zapisi(cod_gor, nom_dog):
    """Лицевые счета договора, которые входят в документ."""
    return list(Potreb.objects.filter(cod_gor=cod_gor, nom_dog=nom_dog, d_stat__in=RASCHET)
                .order_by("id_kategor", "potreb_id"))


def stroka(p, tarify):
    otopl_vse, gvs = _d(p.nach_otopl), _d(p.nach_gvs)
    poteri = _d(p.poterschob) + _d(p.poternagob)
    t = tarif(p, tarify)
    gkal = otopl_vse + gvs
    return Stroka(p=p, otopl=max(otopl_vse - poteri, Decimal(0)), gvs=gvs, poteri=poteri, gkal=gkal,
                  tarif=t, itog=gkal * t)


def sobrat(cod_gor, nom_dog, data=None):
    """Документ по договору; None, если в договоре нет действующих лицевых."""
    from .models import TarifGorod
    recs = zapisi(cod_gor, nom_dog)
    if not recs:
        return None
    gorod = Danrasch.objects.filter(cod_gorod=cod_gor).first()
    tarify = TarifGorod.dlya(cod_gor)
    names = {k.id_kotegor: (k.name_kateg or "").strip() for k in Kategorpot.objects.all()}
    kats = {}
    for p in recs:
        k = kats.setdefault(p.id_kategor, Kategoria(kod=p.id_kategor, name=names.get(p.id_kategor, "")))
        k.stroki.append(stroka(p, tarify))
    for k in kats.values():
        if k.stroki[0].p.potreb_id in KOPEIKA_PLUS:
            k.plus = KOP
    # Реквизиты договора (наименование, руководитель, дата) — у первого лицевого договора.
    glav = min(recs, key=lambda p: p.potreb_id)
    return Dokument(gorod=gorod, glav=glav, kategorii=list(kats.values()), data=data or datetime.date.today())


def po_licevomu(potreb):
    return sobrat(potreb.cod_gor_id, potreb.nom_dog)


def dogovory(cod_gor, s_nachisleniem=True):
    """Номера договоров участка для пакета документов за месяц: договоры с
    действующими лицевыми и (по умолчанию) начислением больше нуля, как в
    массовой рассылке старой программы (nac_vsego > 0)."""
    qs = Potreb.objects.filter(cod_gor=cod_gor, d_stat__in=RASCHET).exclude(nom_dog=None)
    if s_nachisleniem:
        qs = qs.filter(nac_vsego__gt=0)
    return sorted(set(qs.values_list("nom_dog", flat=True)))
