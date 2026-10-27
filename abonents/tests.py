"""Тесты карты абонента на выдуманных записях (без данных из DBF)."""

import re
from collections import Counter
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase

from abonents import layout
from catalogs.models import Akcept, Danrasch, GvsKot, Kategorpot, Minist, Potreb


class KartaTests(TestCase):
    def setUp(self):
        call_command("init_roles", stdout=open("/dev/null", "w"))
        self.ryb = Danrasch.objects.create(cod_gorod=1, name_gorod="Рыбница", name_mes="Октябрь", god=2026,
                                           tkoef=Decimal("0.229"), t_vozd=Decimal("10.0"))
        self.dub = Danrasch.objects.create(cod_gorod=2, name_gorod="Дубоссары", name_mes="Октябрь", god=2026)
        Minist.objects.create(cod_minist=1, name_minis="Без министерства")
        Kategorpot.objects.create(id_kotegor=1, name_kateg="Хозрасчет")
        GvsKot.objects.create(id_kot=16, name_kot="(Р) Котельная №2", kod_gor=self.ryb)
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
