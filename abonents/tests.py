"""Тесты карты абонента на выдуманных записях (без данных из DBF)."""

import re
from collections import Counter
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase

from abonents import layout
from catalogs.models import Akcept, Danrasch, GvsKot, Kategorpot, Limit, Minist, Potreb, SpTeplpoteri


class KartaBase(TestCase):
    def setUp(self):
        call_command("init_roles", stdout=open("/dev/null", "w"))
        self.ryb = Danrasch.objects.create(cod_gorod=1, name_gorod="Рыбница", name_mes="Октябрь", god=2026,
                                           tkoef=Decimal("0.229"), t_vozd=Decimal("10.0"))
        self.dub = Danrasch.objects.create(cod_gorod=2, name_gorod="Дубоссары", name_mes="Октябрь", god=2026)
        Minist.objects.create(cod_minist=1, name_minis="Без министерства")
        Kategorpot.objects.create(id_kotegor=1, name_kateg="Хозрасчет")
        GvsKot.objects.create(id_kot=16, name_kot="(Р) Котельная №2", kod_gor=self.ryb)
        Akcept.objects.create(id_akc=1, name_akc="БА")
        Akcept.objects.create(id_akc=3, name_akc="С")
        common = dict(cod_gor=self.ryb, cod_minist_id=1, id_kategor=1, id_koteln=16, accept=3, tip_rasot=1)
        self.a = Potreb.objects.create(potreb_id=5, nom_dog=6, name_potre='ООО "Крипс"', glav_potre="Магазин",
                                       id_katabon=1, nac_vsego=Decimal("10.5"), posle_prib=7, inf="Примечание",
                                       pok_new=Decimal("12.5"), dn_pereras=0, tkf_perer=Decimal("1.1"),
                                       gkl_perer=Decimal("3.3"), **common)
        self.b = Potreb.objects.create(potreb_id=7, nom_dog=6, name_potre='ООО "Крипс"', glav_potre="Склад",
                                       id_katabon=3, nom_dogab=6, nac_vsego=Decimal("2"), **common)
        self.c = Potreb.objects.create(potreb_id=9, nom_dog=8, name_potre="Школа  № 1", **common)
        Potreb.objects.create(potreb_id=11, nom_dog=8, name_potre="Чужой город", cod_gor=self.dub)

    def login(self, role):
        user = get_user_model().objects.create_user(role, password="x")
        user.groups.add(Group.objects.get(name=role))
        self.client.force_login(user)


class KartaTests(KartaBase):
    def test_each_editable_field_has_one_input_on_its_page(self):
        for key in layout.TAB_KEYS:
            _, _, groups = layout.tab(key)
            items = layout.HEADER + [f for _, fields in groups for f in fields]
            editable = Counter(f.name for f in items if not f.ro and not f.related)
            self.assertTrue(all(n == 1 for n in editable.values()), (key, editable))
            for name in editable:
                Potreb._meta.get_field(name)

    def test_viewer_sees_card_but_cannot_edit(self):
        self.login("Наблюдатель")
        response = self.client.get("/abonents/5/")
        self.assertContains(response, "Крипс")
        self.assertContains(response, "Рыбница")
        self.assertContains(response, "Октябрь 2026")
        self.assertContains(response, "(Р) Котельная №2")
        self.assertContains(response, 'href="/abonents/7/"')  # присоединённый прибор — ссылка
        self.assertNotContains(response, "Изменить")
        self.assertEqual(self.client.get("/abonents/5/edit/").status_code, 403)
        for key in layout.TAB_KEYS:
            self.assertEqual(self.client.get(f"/abonents/5/?tab={key}").status_code, 200)

    def test_navigation_stays_in_city(self):
        self.login("Наблюдатель")
        response = self.client.get("/abonents/9/")
        self.assertContains(response, "3 из 3")
        self.assertContains(response, 'href="/abonents/7/?tab=otop"')
        self.assertNotContains(response, "/abonents/11/")

    def test_saving_unchanged_page_keeps_all_values(self):
        self.login("Оператор")
        before = {f.attname: getattr(self.a, f.attname) for f in Potreb._meta.concrete_fields}
        for key in layout.TAB_KEYS:
            html = self.client.get(f"/abonents/5/edit/?tab={key}").content.decode()
            names = re.findall(r'name="([a-z_0-9]+)"', html)
            data = {}
            for name in set(names) - {"csrfmiddlewaretoken", "tab"}:
                self.assertEqual(names.count(name), 1, name)
                m = re.search(rf'<input[^>]*name="{name}"[^>]*value="([^"]*)"', html)
                if m:
                    data[name] = m.group(1).replace("&quot;", '"')
                    continue
                m = re.search(rf'<select name="{name}".*?<option value="([^"]*)"[^>]*selected', html, re.S)
                if m:
                    data[name] = m.group(1)
                    continue
                m = re.search(rf'<textarea name="{name}"[^>]*>\s*(.*?)</textarea>', html, re.S)
                if m:
                    data[name] = m.group(1)
            data["tab"] = key
            response = self.client.post(f"/abonents/5/edit/?tab={key}", data)
            self.assertEqual(response.status_code, 302, key)
        self.a.refresh_from_db()
        after = {f.attname: getattr(self.a, f.attname) for f in Potreb._meta.concrete_fields}
        self.assertEqual(before, after)

    def test_new_days_of_recalculation_reset_coefficient(self):
        self.login("Оператор")
        html = self.client.get("/abonents/5/edit/?tab=otop").content.decode()
        self.assertIn('name="dn_pereras"', html)
        data = {"tab": "otop", "tip_rasot": "2", "dn_pereras": "3", "tkf_perer": "1.100", "gkl_perer": "3.300",
                "nom_dog": "6", "name_potre": "ООО Крипс", "nom_dogab": "", "glav_potre": "Магазин"}
        self.client.post("/abonents/5/edit/", data)
        self.a.refresh_from_db()
        self.assertEqual(self.a.tip_rasot, 2)
        self.assertEqual(self.a.dn_pereras, 3)
        self.assertEqual(self.a.tkf_perer, 0)
        self.assertEqual(self.a.gkl_perer, 0)

    def test_accept_zero_is_not_allowed(self):
        self.login("Оператор")
        Potreb.objects.filter(potreb_id=9).update(accept=0)
        html = self.client.get("/abonents/9/edit/?tab=ishod").content.decode()
        self.assertNotIn('<option value="0"', html)
        self.assertNotIn('<option value=""', re.search(r'<select name="accept".*?</select>', html, re.S).group(0))
        from abonents.forms import karta_form
        form = karta_form("ishod", {"accept": "0"}, instance=Potreb.objects.get(potreb_id=9))
        self.assertFalse(form.is_valid())
        self.assertIn("accept", form.errors)

    def test_search(self):
        self.login("Наблюдатель")
        self.assertRedirects(self.client.get("/abonents/", {"gorod": 1, "dog": 8}), "/abonents/9/")
        response = self.client.get("/abonents/", {"gorod": 1, "dog": 6})
        self.assertContains(response, "Магазин")
        self.assertContains(response, "Склад")
        response = self.client.get("/abonents/", {"gorod": 1, "q": "школа №1"})
        self.assertContains(response, "Школа")
        self.assertNotContains(response, "Крипс")
        self.assertRedirects(self.client.get("/abonents/", {"ls": 11}), "/abonents/11/")
        self.assertContains(self.client.get("/abonents/", {"ls": 99}, follow=True), "не найден")
        response = self.client.get("/abonents/", {"gorod": 1, "sub": 6})
        self.assertContains(response, "Склад")
        self.assertNotContains(response, "Магазин")

    def test_dogovor_card_totals(self):
        self.login("Наблюдатель")
        response = self.client.get("/abonents/dogovor/1/6/")
        self.assertContains(response, "Магазин")
        self.assertContains(response, "Склад")
        self.assertContains(response, "12,500")

    def test_only_admin_deletes(self):
        self.login("Оператор")
        self.assertEqual(self.client.post("/abonents/9/delete/").status_code, 403)
        self.client.logout()
        self.login("Администратор")
        self.assertRedirects(self.client.post("/abonents/9/delete/"), "/abonents/")
        self.assertFalse(Potreb.objects.filter(potreb_id=9).exists())


class NewAbonentAndPoteriTests(KartaBase):
    """Ввод нового абонента, тепловые потери и теплосчетчик."""

    def test_new_abonent_gets_next_number_and_defaults(self):
        self.login("Оператор")
        self.assertContains(self.client.get("/abonents/"), "Новый абонент")
        response = self.client.post("/abonents/new/", {
            "cod_gor": "1", "nom_dog": "77", "name_potre": "ООО Новое", "id_kategor": "1", "id_koteln": "16",
            "cod_minist": "1",
        })
        p = Potreb.objects.get(nom_dog=77)
        self.assertRedirects(response, f"/abonents/{p.potreb_id}/edit/?tab=ishod")
        self.assertEqual(p.potreb_id, 12)
        self.assertEqual(p.cod_gor_id, 1)
        self.assertEqual(p.accept, 1)
        self.assertEqual(p.name_kot, "(Р) Котельная №2")
        self.assertEqual(p.tip_rasot, 0)
        self.assertEqual(p.adres_sd, "")

    def test_new_abonent_needs_contract_and_city_kotel(self):
        self.login("Оператор")
        response = self.client.post("/abonents/new/", {"cod_gor": "2", "nom_dog": "", "id_koteln": "16"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Котельная из другого города")
        self.assertFalse(Potreb.objects.filter(potreb_id=12).exists())
        self.client.logout()
        self.login("Наблюдатель")
        self.assertEqual(self.client.get("/abonents/new/").status_code, 403)

    def test_poteri_raschet(self):
        from catalogs.models import SpDiametr, SpTeplpoteri
        SpDiametr.objects.create(id_diam=2, diametr=57)
        Potreb.objects.filter(potreb_id=5).update(dnotop=Decimal("30"), tip_rasot=1, nalich_pot=1)
        self.login("Оператор")
        self.assertContains(self.client.get("/abonents/5/"), "/abonents/5/poteri/")
        self.assertFalse(SpTeplpoteri.objects.filter(ln=5).exists())  # просмотр ничего не создаёт
        data = {"diametr1": "57", "dlina1": "100", "raschet": "1"}
        for i in range(2, 7):
            data.update({f"diametr{i}": "", f"dlina{i}": ""})
        self.assertRedirects(self.client.post("/abonents/5/poteri/", data), "/abonents/5/poteri/")
        sp = SpTeplpoteri.objects.get(ln=5)
        # 56 × 100 × 24 × 30 × 0,000001 = 4,032 → 4,03
        self.assertEqual(sp.poteri_pr1, Decimal("4.03"))
        self.assertEqual(sp.vs_poteri, Decimal("4.03"))
        self.a.refresh_from_db()
        self.assertEqual(self.a.poter_pr, Decimal("4.03"))
        self.assertEqual(self.a.poter_nag, 0)

    def test_teploschetchik_created_with_object_name(self):
        from catalogs.models import SpTeplosch
        self.login("Оператор")
        self.assertContains(self.client.get("/abonents/5/teploschetchik/"), 'value="ООО &quot;Крипс&quot;"')
        self.client.post("/abonents/5/teploschetchik/", {
            "name_obek": 'ООО "Крипс"', "adres_obek": "", "tip_prib": "СВТУ 10М", "kdata_pov": "2027-01-31",
        })
        obj = SpTeplosch.objects.get(ln=5)
        self.assertEqual(obj.tip_prib, "СВТУ 10М")
        self.assertEqual(str(obj.kdata_pov), "2027-01-31")
        self.client.logout()
        self.login("Наблюдатель")
        self.assertEqual(self.client.post("/abonents/5/teploschetchik/", {"tip_prib": "x"}).status_code, 403)

    def test_changing_kotel_updates_its_name(self):
        GvsKot.objects.create(id_kot=17, name_kot="(Р) Котельная №3", kod_gor=self.ryb)
        from abonents.forms import karta_form
        p = Potreb.objects.get(potreb_id=5)
        form = karta_form("ishod", None, instance=p)
        data = {name: form[name].value() for name in form.fields}
        data = {k: ("" if v is None else v) for k, v in data.items()}
        data["id_koteln"] = "17"
        form = karta_form("ishod", data, instance=p)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        p.refresh_from_db()
        self.assertEqual(p.name_kot, "(Р) Котельная №3")


class RaschetTests(TestCase):
    """Расчет начислений на небольшом примере, посчитанном вручную."""

    def setUp(self):
        call_command("init_roles", stdout=open("/dev/null", "w"))
        self.ryb = Danrasch.objects.create(cod_gorod=1, name_gorod="Рыбница", tkoef=Decimal("0.5"),
                                           qpfakt=Decimal("46"), t_vozd=Decimal("10"), t_proekt=-17)
        self.dub = Danrasch.objects.create(cod_gorod=2, name_gorod="Дубоссары", qpfakt=Decimal("0"))
        common = dict(nalich_pot=3, dnotop=Decimal("30"), accept=1, id_katabon=1)
        # По прибору: (20 − 10) × 1,5 = 15 Гкал, ГВС 2, лимит 40 при выставленных 10.
        self.a = Potreb.objects.create(potreb_id=1, nom_dog=1, cod_gor=self.ryb, tip_rasot=1, pok_old=10,
                                       pok_new=20, koef_pok=Decimal("1.5"), nach_gvs=2, vd_limit=40, nach_finan=10,
                                       name_potre="По прибору", **common)
        # По нагрузке: 0,1 × 24 × 30 × 0,5 = 36 Гкал.
        self.b = Potreb.objects.create(potreb_id=2, nom_dog=2, cod_gor=self.ryb, tip_rasot=3,
                                       q_otoppr=Decimal("0.1"), **common)
        # По прибору и нагрузке: 4 Гкал по прибору и 0,05 × 24 × 30 × 0,5 = 18 по нагрузке.
        self.c = Potreb.objects.create(potreb_id=3, nom_dog=3, cod_gor=self.ryb, tip_rasot=2, pok_new=4,
                                       koef_pok=1, q_otoppr=Decimal("0.05"), **common)
        # Договор 50 в Дубоссарах: общий прибор (10 Гкал) делится по нагрузке 0,3 и 0,1.
        self.h = Potreb.objects.create(potreb_id=4, nom_dog=50, nom_dogab=50, nom_pribor=1, cod_gor=self.dub,
                                       tip_rasot=1, pok_new=10, koef_pok=1, q_otop=Decimal("0.3"), **common)
        self.s = Potreb.objects.create(potreb_id=5, nom_dog=51, nom_dogab=50, nom_pribor=1, cod_gor=self.dub,
                                       tip_rasot=1, q_otop=Decimal("0.1"), **common)
        # Договор расторгнут: дней отопления 0, по нагрузке ничего не начисляется.
        self.x = Potreb.objects.create(potreb_id=6, nom_dog=6, cod_gor=self.ryb, tip_rasot=3, d_stat=63,
                                       q_otoppr=Decimal("0.1"), **common)

    def login(self, role):
        user = get_user_model().objects.create_user(role, password="x")
        user.groups.add(Group.objects.get(name=role))
        self.client.force_login(user)

    def test_raschet(self):
        self.login("Оператор")
        response = self.client.post("/abonents/raschet/")
        self.assertRedirects(response, "/abonents/raschet/itog/")
        a, b, c, h, s = (Potreb.objects.get(pk=x.pk) for x in (self.a, self.b, self.c, self.h, self.s))
        self.assertEqual((a.nach_otpr, a.nach_otnag), (Decimal("15.000"), Decimal("0.000")))
        self.assertEqual((b.nach_otpr, b.nach_otnag), (Decimal("0.000"), Decimal("36.000")))
        self.assertEqual((c.nach_otpr, c.nach_otnag), (Decimal("4.000"), Decimal("18.000")))
        # По факту: 46 − 15 − 4 − 2 (ГВС) = 25 Гкал делятся пропорционально 36 и 18.
        self.assertEqual((b.nac_pogaz, c.nac_pogaz), (Decimal("16.667"), Decimal("8.333")))
        self.assertEqual(Danrasch.objects.get(cod_gorod=1).qpras, Decimal("54.00"))
        self.assertEqual((a.nach_otopl, b.nach_otopl, c.nach_otopl),
                         (Decimal("15.000"), Decimal("16.670"), Decimal("12.330")))
        self.assertEqual(a.nac_vsego, Decimal("17.000"))
        self.assertEqual((h.nach_otsub, s.nach_otsub, h.q_otopobsh), (Decimal("7.500"), Decimal("2.500"),
                                                                      Decimal("0.40000")))
        self.assertEqual((h.nach_otopl, s.nach_otopl), (Decimal("7.500"), Decimal("2.500")))
        # 10 + 17 × 2 ≥ 40, но 10 + 17 ≤ 40.
        self.assertEqual(list(Limit.objects.values_list("potreb_id", "koment")), [(1, "Лимит заканчивается")])
        x = Potreb.objects.get(pk=self.x.pk)
        self.assertEqual((x.dnotop, x.nach_otnag, x.nac_vsego), (Decimal("0.0"), Decimal("0.000"), Decimal("0.000")))
        self.assertEqual(SpTeplpoteri.objects.count(), 6)  # записи потерь создаются, как в старой программе
        page = self.client.get("/abonents/raschet/itog/")
        self.assertContains(page, "рассчитано абонентов 6")
        self.assertContains(page, "Лимит заканчивается")

    def test_viewer_cannot_run(self):
        self.login("Наблюдатель")
        self.assertEqual(self.client.get("/abonents/raschet/").status_code, 200)
        self.assertEqual(self.client.post("/abonents/raschet/").status_code, 403)

    def test_dan_rasch_sets_koef_and_days(self):
        self.login("Оператор")
        response = self.client.post("/abonents/raschet/dannye/?gorod=1", {
            "t_vozd": "4", "t_proekt": "-17", "dnotop": "31", "dngvs": "", "qpfakt": "46", "dnotop_vsem": "on",
        })
        self.assertRedirects(response, "/abonents/raschet/dannye/")
        d = Danrasch.objects.get(cod_gorod=1)
        self.assertEqual(d.tkoef, Decimal("0.400"))  # (18 − 4) / (18 + 17)
        self.assertEqual(set(Potreb.objects.filter(cod_gor=1, d_stat=None).values_list("dnotop", flat=True)),
                         {Decimal("31.0")})
        self.assertEqual(Potreb.objects.get(potreb_id=6).dnotop, Decimal("0.0"))
        self.assertEqual(set(Potreb.objects.filter(cod_gor=2).values_list("dnotop", flat=True)), {Decimal("30.0")})
