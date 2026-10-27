"""Тесты экранов справочников и ролей на настоящих моделях (без данных из DBF)."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase

from catalogs.models import Minist, SmtpNas, Tarif
from catalogs.registry import catalog_models


class RoleTests(TestCase):
    def setUp(self):
        call_command("init_roles", stdout=open("/dev/null", "w"))
        Minist.objects.create(cod_minist=1, name_minis="Министерство экономического развития")
        Minist.objects.create(cod_minist=2, name_minis="Министерство просвещения")

    def login(self, role):
        user = get_user_model().objects.create_user(role, password="x")
        user.groups.add(Group.objects.get(name=role))
        self.client.force_login(user)

    def test_menu_directories_are_listed_in_menu_order(self):
        names = [m._meta.model_name for m in catalog_models()]
        self.assertEqual(names[:3], ["danrasch", "minist", "gvskot"])
        self.assertEqual(len(names), 14)
        self.assertNotIn("sul", names)
        self.assertNotIn("smtpnas", names)

    def test_anonymous_redirected_to_login(self):
        response = self.client.get("/catalogs/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response["Location"])

    def test_viewer_sees_catalog_but_cannot_edit(self):
        self.login("Наблюдатель")
        self.assertContains(self.client.get("/catalogs/"), "Министерства")
        self.assertContains(self.client.get("/catalogs/minist/"), "просвещения")
        self.assertNotContains(self.client.get("/catalogs/minist/"), "Добавить")
        self.assertEqual(self.client.get("/catalogs/minist/new/").status_code, 403)

    def test_operator_can_add_but_not_delete(self):
        self.login("Оператор")
        response = self.client.post("/catalogs/tarif/new/", {"id_tar": 99, "name_tar": "Проверка", "zn_tar": "100.5"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Tarif.objects.filter(id_tar=99).exists())
        minist = Minist.objects.first()
        self.assertEqual(self.client.post(f"/catalogs/minist/{minist.pk}/delete/").status_code, 403)

    def test_search_is_case_insensitive_for_cyrillic(self):
        self.login("Наблюдатель")
        response = self.client.get("/catalogs/minist/", {"q": "ПРОСВЕЩЕНИЯ"})
        self.assertContains(response, "просвещения")
        self.assertNotContains(response, "экономического")

    def test_smtp_password_hidden_in_admin(self):
        admin = get_user_model().objects.create_superuser("root", password="x")
        self.client.force_login(admin)
        smtp = SmtpNas.objects.create(smtp="mail.example", password="secret-value")
        response = self.client.get(f"/admin/catalogs/smtpnas/{smtp.pk}/change/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "secret-value")
