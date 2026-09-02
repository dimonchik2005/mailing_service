import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from users.managers import UserManager


class User(AbstractUser):
    """Пользователь сервиса рассылок."""

    username = None

    email = models.EmailField(
        unique=True,
        verbose_name="Email",
    )

    is_email_verified = models.BooleanField(
        default=False,
        verbose_name="Email подтверждён",
    )

    verification_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name="Токен подтверждения",
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        permissions = [
            (
                "can_block_user",
                "Может блокировать пользователей",
            ),
        ]

    def __str__(self) -> str:
        return self.email
