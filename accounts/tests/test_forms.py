from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from accounts.forms import UserCreateForm
from accounts.models import Profile
from companies.models import OilCompany

User = get_user_model()


class UserCreateFormTests(TestCase):
    def setUp(self):
        self.company = OilCompany.objects.create(
            name="Test Oil",
            region="Aktau",
        )
        Group.objects.get_or_create(name="Manager")

    def test_user_create_form_rejects_mismatched_passwords(self):
        form = UserCreateForm(
            data={
                "username": "alihan",
                "first_name": "Alihan",
                "last_name": "Z",
                "email": "alihan@example.com",
                "password1": "StrongPass123",
                "password2": "WrongPass123",
                "role": "Manager",
                "oil_company": self.company.id,
                "department": "IT",
                "phone_number": "+77001234567",
                "bio": "Test user",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)
        self.assertIn("Пароли не совпадают.", form.errors["__all__"])

    def test_user_create_form_creates_user_and_profile(self):
        form = UserCreateForm(
            data={
                "username": "dariya",
                "first_name": "Dariya",
                "last_name": "A",
                "email": "dariya@example.com",
                "password1": "StrongPass123",
                "password2": "StrongPass123",
                "role": "Manager",
                "oil_company": self.company.id,
                "department": "Geology",
                "phone_number": "+77005554433",
                "bio": "Engineer",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()

        self.assertTrue(User.objects.filter(username="dariya").exists())
        self.assertTrue(Profile.objects.filter(user=user).exists())
        self.assertEqual(user.profile.oil_company, self.company)
        self.assertEqual(user.profile.department, "Geology")
        self.assertEqual(user.profile.phone_number, "+77005554433")
        self.assertEqual(user.profile.bio, "Engineer")
        self.assertTrue(user.groups.filter(name="Manager").exists())
        self.assertTrue(user.check_password("StrongPass123"))