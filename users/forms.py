from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserChangeForm,
    UserCreationForm,
)

from users.models import User

class CustomUserCreationForm(UserCreationForm):
    """Создание пользователя в административной панели."""

    class Meta:
        model = User
        fields = ("email",)


class CustomUserChangeForm(UserChangeForm):
    """Редактирование пользователя в административной панели."""

    class Meta:
        model = User
        fields = "__all__"

class UserLoginForm(AuthenticationForm):
    """Форма входа по email."""

    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control form-control-lg",
                "placeholder": "name@example.com",
                "autocomplete": "email",
            }
        ),
    )

    password = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control form-control-lg",
                "placeholder": "Введите пароль",
                "autocomplete": "current-password",
            }
        ),
    )