from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import Profile
from companies.models import OilCompany

User = get_user_model()


class ProfileSignalTests(TestCase):
    def setUp(self):
        self.company = OilCompany.objects.create(
            name="Signal Oil",
            region="Atyrau",
        )

    def test_profile_is_created_automatically_after_user_creation(self):
        user = User.objects.create_user(
            username="signal_user",
            password="TestPass123",
        )

        self.assertTrue(Profile.objects.filter(user=user).exists())
        self.assertEqual(user.profile.oil_company, self.company)
