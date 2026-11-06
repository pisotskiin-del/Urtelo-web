"""Схема договора: кто к кому подключён и как считается.

Связи берутся из тех же полей, по которым идёт расчёт (raschet.py):

- общий прибор: главный по договору — запись, у которой nom_dog = nom_dogab;
  на его приборе сидят записи с nom_dogab = его договору и тем же nom_pribor
  (шаг 6 расчёта: начисление по прибору делится по нагрузке);
- присоединённый прибор (posle_prib…posle_pri4): показания прибора этого
  лицевого вычитаются из начисления по прибору родителя (шаг 4);
- присоединённая нагрузка (pris_nag1…8): лицевому начисляется доля прибора
  родителя пропорционально нагрузке (шаг 5).

Остальные записи договора показываются отдельными ветками от договора.
"""

from dataclasses import dataclass, field

from django.db.models import Q

from catalogs.models import Potreb

from . import layout
from .raschet import POSLE, PRIS_NAG

OBSHCHIJ, POSLE_PRIB, NAGRUZKA = "obshchij", "posle", "nagruzka"
SVYAZI = {
    OBSHCHIJ: "на общем приборе",
    POSLE_PRIB: "присоединённый прибор: показания вычитаются",
    NAGRUZKA: "по присоединённой нагрузке от прибора",
}


@dataclass
class Uzel:
    p: Potreb
    svyaz: str = ""                 # как подключён к родителю
    deti: list = field(default_factory=list)
    tekushchij: bool = False

    @property
    def svyaz_text(self):
        t = SVYAZI.get(self.svyaz, "")
        if self.svyaz == OBSHCHIJ and self.p.nom_pribor:
            t += f" № {self.p.nom_pribor}"
        return t

    @property
    def sposob(self):
        """«прибор» / «нагрузка» / «прибор и нагрузка» — для цвета и подписи."""
        return {1: "pribor", 2: "oba", 3: "nagruzka"}.get(self.p.tip_rasot, "")

    @property
    def sposob_text(self):
        p = self.p
        nom = p.nom_pribor or p.inf_pribor
        pribor = f"прибор № {nom}" if nom else "прибор"
        nagr = f"нагрузка {_ch(p.q_otoppr)} Гкал/ч" if p.q_otoppr else "нагрузка"
        return {1: pribor, 2: f"{pribor} + {nagr}", 3: nagr}.get(p.tip_rasot, "способ расчёта не задан")

    @property
    def pribor(self):
        """На лицевом стоит свой прибор: расчёт по прибору, и он не сидит на
        общем приборе главного по договору."""
        return self.p.tip_rasot in (1, 2) and self.svyaz != OBSHCHIJ

    @property
    def abonent(self):
        return self.p.id_katabon == 1

    @property
    def prinadl(self):
        return dict(layout.ID_KATABON).get(self.p.id_katabon, "")

    @property
    def otkluchen(self):
        return self.p.d_stat not in layout.RASCHET

    @property
    def status(self):
        return {61: "Приостановлен", 63: "Расторгнут"}.get(self.p.d_stat, "Не заключён")


def _ch(v):
    s = f"{v:f}".rstrip("0").rstrip(".") if v is not None else ""
    return s.replace(".", ",")


def _ssylki(p, polya):
    return [int(getattr(p, f)) for f in polya if getattr(p, f)]


def postroit(p):
    """Дерево схемы договора лицевого p: (корневые узлы, договор, главный по
    договору, которому p приходится субабонентом, или None)."""
    gor, dog = p.cod_gor_id, p.nom_dog
    if dog:
        zapisi = {r.potreb_id: r for r in Potreb.objects.filter(cod_gor=gor).filter(
            Q(nom_dog=dog) | Q(nom_dogab=dog))}
    else:
        zapisi = {p.potreb_id: p}
    zapisi.setdefault(p.potreb_id, p)
    # Присоединённые приборы и нагрузка могут ссылаться на лицевые других договоров.
    for _ in range(3):
        nuzhny = {n for r in zapisi.values() for n in _ssylki(r, POSLE + PRIS_NAG)} - set(zapisi)
        if not nuzhny:
            break
        zapisi.update({r.potreb_id: r for r in Potreb.objects.filter(potreb_id__in=nuzhny)})

    uzly = {pid: Uzel(r, tekushchij=pid == p.potreb_id) for pid, r in zapisi.items()}
    roditel = {}
    for r in sorted(zapisi.values(), key=lambda r: r.potreb_id):
        for n in _ssylki(r, POSLE):
            if n in uzly and n != r.potreb_id:
                roditel.setdefault(n, (r.potreb_id, POSLE_PRIB))
        for n in _ssylki(r, PRIS_NAG):
            if n in uzly and n != r.potreb_id:
                roditel.setdefault(n, (r.potreb_id, NAGRUZKA))
    glavnye = {}
    for r in zapisi.values():
        if r.nom_dog and r.nom_dog == r.nom_dogab:
            glavnye.setdefault((r.nom_dog, r.nom_pribor or 0), r.potreb_id)
    for r in zapisi.values():
        g = glavnye.get((r.nom_dogab, r.nom_pribor or 0)) if r.nom_dogab else None
        if g is not None and g != r.potreb_id:
            roditel.setdefault(r.potreb_id, (g, OBSHCHIJ))

    def petlya(pid):
        vidal = set()
        while pid in roditel:
            if pid in vidal:
                return True
            vidal.add(pid)
            pid = roditel[pid][0]
        return False

    korni = []
    for pid in sorted(uzly, key=lambda i: (zapisi[i].id_katabon or 9, i)):
        u = uzly[pid]
        if pid in roditel and not petlya(pid):
            par, svyaz = roditel[pid]
            u.svyaz = svyaz
            uzly[par].deti.append(u)
        else:
            korni.append(u)
    # Сначала ветки с подключёнными, затем одиночные объекты.
    korni.sort(key=lambda u: (not u.deti, u.p.id_katabon or 9, u.p.potreb_id))
    glav_ab = None
    if p.nom_dogab and p.nom_dogab != dog:
        glav_ab = Potreb.objects.filter(cod_gor=gor, nom_dog=p.nom_dogab, nom_dogab=p.nom_dogab).order_by(
            "potreb_id").first()
    return korni, dog, glav_ab
