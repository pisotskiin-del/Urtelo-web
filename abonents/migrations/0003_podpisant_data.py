from django.db import migrations

# Подписанты, которые были вписаны в отчеты программы 2026 года. Их меняют в
# справочнике «Подписанты документов».
START = [
    ("utv", None, 'Начальник Рыбницкого участка по эксплуатации котельных и тепловых сетей МГУП "Тирастеплоэнерго"',
     "А.Г.Тищенко"),
    ("ved", None, "Ведущий специалист", "Борсуковский С.В."),
    ("isp", None, "Исполнитель", ""),
    ("pribor", 1, "Инспектор по контролю за потреблением тепловой энергии юридическим лицам", "Химач Н.И."),
    ("pribor", 2, "Контролёр по учёту и сбыту тепловой энергии", "Дабижа И.Н."),
    ("pribor", 3, "Контролёр по учёту и сбыту тепловой энергии", "Кушнир В.И."),
]


def fill(apps, schema_editor):
    Podpisant = apps.get_model("abonents", "Podpisant")
    for rol, gorod, doljnost, fio in START:
        Podpisant.objects.create(rol=rol, gorod=gorod, doljnost=doljnost, fio=fio)


class Migration(migrations.Migration):
    dependencies = [("abonents", "0002_podpisant")]
    operations = [migrations.RunPython(fill, migrations.RunPython.noop)]
