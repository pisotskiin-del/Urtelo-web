"""Тепловые потери по участкам трубопровода (форма kalcul_poteri старой программы).

Для каждого из шести участков задаются диаметр и длина. Потери участка, Гкал:
коэффициент диаметра × длина × 24 × дни отопления × 0,000001, округлённо до сотых.
Коэффициенты по диаметрам заданы в старой программе прямо в коде формы."""

from decimal import ROUND_HALF_UP, Decimal

SECTIONS = range(1, 7)

# Диаметр трубы, мм → коэффициент потерь (kalcul_poteri, кнопка «Расчитать»).
DIAM_KOEF = {32: 45, 57: 56, 76: 64, 89: 69, 108: 76, 159: 94, 219: 113, 273: 132, 325: 149}


def _round2(value):
    # VFP ROUND округляет половину от нуля.
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def section_loss(diametr, dlina, dnotop):
    koef = DIAM_KOEF.get(diametr or 0, 0)
    return _round2(Decimal(koef) * (dlina or 0) * 24 * (dnotop or 0) * Decimal("0.000001"))


def raschet(sp, p):
    """Рассчитать потери участков sp (SpTeplpoteri) для абонента p (Potreb) и,
    как форма kalcul_poteri, записать итог в потери по прибору или по нагрузке.
    Записи не сохраняет."""
    total = Decimal(0)
    for i in SECTIONS:
        loss = section_loss(getattr(sp, f"diametr{i}"), getattr(sp, f"dlina{i}"), p.dnotop)
        setattr(sp, f"poteri_pr{i}", loss)
        total += loss
    sp.vs_poteri = total

    delta = (p.pok_new or 0) - (p.pok_old or 0)
    p.poter_pr = total if (delta > 0 or p.nalich_pot == 1) and p.tip_rasot == 1 else 0
    p.poter_nag = total if ((p.q_otoppr or 0) > 0 or p.nalich_pot == 1) and p.tip_rasot == 3 else 0
    return total
