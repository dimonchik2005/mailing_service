from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone

from mailings.models import (
    Mailing,
    MailingAttempt,
    Message,
    Recipient,
)
from mailings.services import send_mailing


User = get_user_model()


@override_settings(
    EMAIL_BACKEND=(
        "django.core.mail.backends.locmem.EmailBackend"
    ),
)
class MailingServiceTests(TestCase):
    """Проверяет основную логику рассылок."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="owner@example.com",
            password="TestPassword123!",
            is_active=True,
        )

        self.message = Message.objects.create(
            subject="Тестовая рассылка",
            body="Текст тестового письма",
            owner=self.user,
        )

        self.first_recipient = Recipient.objects.create(
            email="first@example.com",
            full_name="Первый получатель",
            owner=self.user,
        )
        self.second_recipient = Recipient.objects.create(
            email="second@example.com",
            full_name="Второй получатель",
            owner=self.user,
        )

    def create_mailing(
        self,
        start_time,
        end_time,
    ):
        mailing = Mailing.objects.create(
            start_time=start_time,
            end_time=end_time,
            message=self.message,
            owner=self.user,
        )
        mailing.recipients.set(
            [
                self.first_recipient,
                self.second_recipient,
            ]
        )

        return mailing

    def test_update_status_for_active_mailing(self):
        """Активная по времени рассылка получает статус Запущена."""

        current_time = timezone.now()

        mailing = self.create_mailing(
            start_time=current_time - timedelta(minutes=1),
            end_time=current_time + timedelta(minutes=10),
        )

        mailing.update_status()

        self.assertEqual(
            mailing.status,
            Mailing.Status.STARTED,
        )

    def test_invalid_time_order(self):
        """Начало рассылки должно быть раньше окончания."""

        current_time = timezone.now()

        mailing = Mailing(
            start_time=current_time + timedelta(hours=2),
            end_time=current_time + timedelta(hours=1),
            message=self.message,
            owner=self.user,
        )

        with self.assertRaises(ValidationError) as error:
            mailing.full_clean()

        self.assertIn(
            "end_time",
            error.exception.message_dict,
        )

    def test_send_mailing_creates_attempts_in_batch(self):
        """Для каждого получателя сохраняется попытка."""

        current_time = timezone.now()

        mailing = self.create_mailing(
            start_time=current_time - timedelta(minutes=1),
            end_time=current_time + timedelta(minutes=10),
        )

        successful_count, failed_count = (
            send_mailing(mailing)
        )

        self.assertEqual(successful_count, 2)
        self.assertEqual(failed_count, 0)

        self.assertEqual(
            MailingAttempt.objects.filter(
                mailing=mailing,
            ).count(),
            2,
        )
        self.assertEqual(len(mail.outbox), 2)

        self.assertFalse(
            MailingAttempt.objects.filter(
                mailing=mailing,
                status=MailingAttempt.Status.FAILED,
            ).exists()
        )

    def test_mailing_cannot_run_outside_allowed_time(self):
        """Рассылка не запускается раньше времени."""

        current_time = timezone.now()

        mailing = self.create_mailing(
            start_time=current_time + timedelta(hours=1),
            end_time=current_time + timedelta(hours=2),
        )

        with self.assertRaises(ValidationError):
            send_mailing(mailing)

        self.assertFalse(
            MailingAttempt.objects.filter(
                mailing=mailing,
            ).exists()
        )