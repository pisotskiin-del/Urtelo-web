from catalogs.models import Danrasch


def raschet_mes(request):
    """Расчетный месяц для верхней строки: по выбранному городу (обычно у всех
    городов он один и тот же)."""
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {}
    cities = list(Danrasch.objects.exclude(cod_gorod=None).order_by("cod_gorod"))
    code = request.session.get("kod_gorod")
    city = next((c for c in cities if c.cod_gorod == code), cities[0] if cities else None)
    if city is None or not city.name_mes:
        return {}
    return {"raschet_mes": f"{city.name_mes.strip()} {city.god or ''}".strip()}
