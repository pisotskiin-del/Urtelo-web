from django.db import migrations

UCHASTKI = (1, 2, 3)


def fill(apps, schema_editor):
    """Каждому участку — копия общего справочника тарифов с теми же кодами."""
    Tarif = apps.get_model("catalogs", "Tarif")
    TarifGorod = apps.get_model("abonents", "TarifGorod")
    for t in Tarif.objects.exclude(id_tar=None).order_by("id_tar"):
        for gorod in UCHASTKI:
            TarifGorod.objects.get_or_create(gorod=gorod, id_tar=t.id_tar, defaults={
                "name_tar": (t.name_tar or "").strip(), "zn_tar": t.zn_tar, "diz_tar": t.diz_tar})


class Migration(migrations.Migration):
    dependencies = [("abonents", "0004_tarifgorod"), ("catalogs", "0001_initial")]
    operations = [migrations.RunPython(fill, migrations.RunPython.noop)]
