from django.conf import settings
from django.db import migrations, models

PAPKA_1C = r"\\server-ff\Abon_teplo1C"


def fill(apps, schema_editor):
    """Одна запись настроек; папка для 1С — из TEPLO_1C_DIR, если она была задана."""
    Nastroika = apps.get_model("abonents", "Nastroika")
    if not Nastroika.objects.exists():
        Nastroika.objects.create(papka_1c=getattr(settings, "TEPLO_1C_DIR", "") or PAPKA_1C)


class Migration(migrations.Migration):
    dependencies = [("abonents", "0005_tarifgorod_data")]
    operations = [
        migrations.CreateModel(
            name="Nastroika",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("papka_1c", models.CharField(
                    blank=True, max_length=255, verbose_name="Папка для выгрузки в 1С",
                    help_text="Сюда при переходе на новый месяц записывается файл Abpt<ГГ><ММ>.dbf. "
                              "Пусто — файл только скачивается в «Закрытых месяцах».")),
            ],
            options={"verbose_name": "Настройки программы", "verbose_name_plural": "Настройки программы",
                     "ordering": ["pk"]},
        ),
        migrations.RunPython(fill, migrations.RunPython.noop),
    ]
