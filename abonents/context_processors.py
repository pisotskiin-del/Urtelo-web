from catalogs.models import Danrasch


def raschet_mes(request):
    """Расчетный месяц для верхней строки: по выбранному городу (обычно у всех
    городов он один и тот же). При просмотре закрытого месяца — он и список
    закрытых месяцев для выбора."""
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {}
    from . import arhiv, prosmotr
    out = {"mesyacy_arhiv": arhiv.vybor()}
    m = prosmotr.get(request)
    if m is not None:
        out.update(prosmotr=m, prosmotr_mes=prosmotr.kod(m))
    cities = list(Danrasch.objects.exclude(cod_gorod=None).order_by("cod_gorod"))
    code = request.session.get("kod_gorod")
    city = next((c for c in cities if c.cod_gorod == code), cities[0] if cities else None)
    if city is None or not city.name_mes:
        return out
    out["raschet_mes"] = f"{city.name_mes.strip()} {city.god or ''}".strip()
    return out
