from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils import timezone

from mailings.models import Mailing, MailingAttempt


def send_mailing(mailing: Mailing) -> tuple[int, int]:
    """Отправляет рассылку и сохраняет попытки одним запросом."""

    current_time = timezone.now()
    mailing.update_status()

    if not mailing.is_active:
        raise ValidationError(
            "Рассылка отключена."
        )

    if not (
        mailing.start_time
        <= current_time
        <= mailing.end_time
    ):
        raise ValidationError(
            "Сейчас рассылку отправлять нельзя. "
            "Проверьте время начала и окончания."
        )

    attempts = []
    successful_count = 0
    failed_count = 0

    for recipient in mailing.recipients.all():
        try:
            result = send_mail(
                subject=mailing.message.subject,
                message=mailing.message.body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=False,
            )

            if result == 1:
                status = MailingAttempt.Status.SUCCESS
                server_response = (
                    f"Письмо отправлено: {recipient.email}"
                )
                successful_count += 1
            else:
                status = MailingAttempt.Status.FAILED
                server_response = (
                    "Почтовый сервер не подтвердил отправку: "
                    f"{recipient.email}"
                )
                failed_count += 1

        except Exception as error:
            status = MailingAttempt.Status.FAILED
            server_response = (
                f"{recipient.email}: {error}"
            )
            failed_count += 1

        attempts.append(
            MailingAttempt(
                mailing=mailing,
                status=status,
                server_response=server_response,
            )
        )

    MailingAttempt.objects.bulk_create(attempts)

    return successful_count, failed_count