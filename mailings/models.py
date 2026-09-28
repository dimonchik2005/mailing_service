from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Recipient(models.Model):
    """Получатель рассылки."""

    email = models.EmailField(
        unique=True,
        verbose_name="Email",
    )
    full_name = models.CharField(
        max_length=255,
        verbose_name="Ф. И. О.",
    )
    comment = models.TextField(
        blank=True,
        verbose_name="Комментарий",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recipients",
        verbose_name="Владелец",
    )

    class Meta:
        verbose_name = "Получатель"
        verbose_name_plural = "Получатели"
        ordering = ("full_name",)

    def __str__(self) -> str:
        return f"{self.full_name} ({self.email})"


class Message(models.Model):
    """Сообщение для рассылки."""

    subject = models.CharField(
        max_length=255,
        verbose_name="Тема письма",
    )
    body = models.TextField(
        verbose_name="Тело письма",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="Владелец",
    )

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ("subject",)

    def __str__(self) -> str:
        return self.subject


class Mailing(models.Model):
    """Рассылка сообщений получателям."""

    class Status(models.TextChoices):
        CREATED = "Создана", "Создана"
        STARTED = "Запущена", "Запущена"
        FINISHED = "Завершена", "Завершена"

    start_time = models.DateTimeField(
        verbose_name="Дата и время начала отправки",
    )
    end_time = models.DateTimeField(
        verbose_name="Дата и время окончания отправки",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CREATED,
        editable=False,
        verbose_name="Статус",
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.PROTECT,
        related_name="mailings",
        verbose_name="Сообщение",
    )
    recipients = models.ManyToManyField(
        Recipient,
        related_name="mailings",
        verbose_name="Получатели",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mailings",
        verbose_name="Владелец",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Рассылка включена",
    )

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        ordering = ("-start_time",)
        permissions = [
            (
                "can_disable_mailing",
                "Может отключать рассылки",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"{self.message.subject} — "
            f"{self.start_time:%d.%m.%Y %H:%M}"
        )

    def clean(self):
        """Проверяет корректность времени рассылки."""

        super().clean()

        errors = {}

        if (
                self.start_time
                and self.start_time < timezone.now()
        ):
            errors["start_time"] = (
                "Время начала не может быть в прошлом."
            )

        if (
            self.start_time
            and self.end_time
            and self.start_time >= self.end_time
        ):
            errors["end_time"] = (
                "Время окончания должно быть позже времени начала."
            )

        if errors:
            raise ValidationError(errors)

    def update_status(self) -> str:
        """Пересчитывает и сохраняет текущий статус."""

        current_time = timezone.now()

        if current_time < self.start_time:
            new_status = self.Status.CREATED
        elif self.start_time <= current_time <= self.end_time:
            new_status = self.Status.STARTED
        else:
            new_status = self.Status.FINISHED

        if self.status != new_status:
            self.status = new_status

            if self.pk:
                self.save(
                    update_fields=["status"],
                )

        return self.status


class MailingAttempt(models.Model):
    """Результат попытки отправки письма."""

    class Status(models.TextChoices):
        SUCCESS = "Успешно", "Успешно"
        FAILED = "Не успешно", "Не успешно"

    attempt_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата и время попытки",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        verbose_name="Статус",
    )
    server_response = models.TextField(
        blank=True,
        verbose_name="Ответ почтового сервера",
    )
    mailing = models.ForeignKey(
        Mailing,
        on_delete=models.CASCADE,
        related_name="attempts",
        verbose_name="Рассылка",
    )

    class Meta:
        verbose_name = "Попытка отправки"
        verbose_name_plural = "Попытки отправки"
        ordering = ("-attempt_time",)

    def __str__(self) -> str:
        return (
            f"{self.status} — "
            f"{self.attempt_time:%d.%m.%Y %H:%M}"
        )