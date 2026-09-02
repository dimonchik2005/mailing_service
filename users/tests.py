from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse


User = get_user_model()


@override_settings(
    EMAIL_BACKEND=(
        "django.core.mail.backends.locmem.EmailBackend"
    ),
)
class UserAuthenticationTests(TestCase):
    """Проверяет регистрацию и восстановление доступа."""

    def test_registration_creates_inactive_user(self):
        """До подтверждения email пользователь неактивен."""

        response = self.client.post(
            reverse("users:register"),
            data={
                "email": "new@example.com",
                "password1": "StrongTestPassword123!",
                "password2": "StrongTestPassword123!",
            },
        )

        user = User.objects.get(
            email="new@example.com",
        )

        self.assertRedirects(
            response,
            reverse("users:login"),
        )
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_email_verified)
        self.assertEqual(len(mail.outbox), 1)

    def test_email_verification_activates_user(self):
        """Ссылка подтверждения активирует аккаунт."""

        user = User.objects.create_user(
            email="verify@example.com",
            password="StrongTestPassword123!",
            is_active=False,
        )

        response = self.client.get(
            reverse(
                "users:verify_email",
                kwargs={
                    "token": user.verification_token,
                },
            )
        )

        user.refresh_from_db()

        self.assertRedirects(
            response,
            reverse("users:login"),
        )
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_email_verified)

    def test_password_reset_sends_email(self):
        """Активному пользователю отправляется сброс пароля."""

        User.objects.create_user(
            email="reset@example.com",
            password="StrongTestPassword123!",
            is_active=True,
            is_email_verified=True,
        )

        response = self.client.post(
            reverse("users:password_reset"),
            data={
                "email": "reset@example.com",
            },
        )

        self.assertRedirects(
            response,
            reverse("users:password_reset_done"),
        )
        self.assertEqual(len(mail.outbox), 1)


class ManagerPermissionTests(TestCase):
    """Проверяет ограничение менеджерских действий."""

    def setUp(self):
        self.manager = User.objects.create_user(
            email="manager@example.com",
            password="StrongTestPassword123!",
            is_active=True,
        )
        self.regular_user = User.objects.create_user(
            email="user@example.com",
            password="StrongTestPassword123!",
            is_active=True,
        )

    def test_regular_user_cannot_open_user_list(self):
        """Обычный пользователь получает 403."""

        self.client.force_login(
            self.regular_user,
        )

        response = self.client.get(
            reverse("users:user_list"),
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_manager_can_block_user(self):
        """Менеджер может заблокировать пользователя."""

        permission = Permission.objects.get(
            content_type__app_label="users",
            codename="can_block_user",
        )
        self.manager.user_permissions.add(
            permission,
        )

        self.client.force_login(
            self.manager,
        )

        response = self.client.post(
            reverse(
                "users:user_toggle_active",
                kwargs={
                    "pk": self.regular_user.pk,
                },
            )
        )

        self.regular_user.refresh_from_db()

        self.assertRedirects(
            response,
            reverse("users:user_list"),
        )
        self.assertFalse(
            self.regular_user.is_active,
        )