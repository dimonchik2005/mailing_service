from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserChangeForm,
    UserCreationForm,
    PasswordResetForm,
    SetPasswordForm,
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


class RegistrationForm(UserCreationForm):
    """Регистрация пользователя на сайте."""

    class Meta:
        model = User
        fields = ("email",)
        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "name@example.com",
                    "autocomplete": "email",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["password1"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Введите пароль",
                "autocomplete": "new-password",
            }
        )
        self.fields["password2"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Повторите пароль",
                "autocomplete": "new-password",
            }
        )


class UserPasswordResetForm(PasswordResetForm):
    """Форма запроса восстановления пароля."""

    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "name@example.com",
                "autocomplete": "email",
            }
        ),
    )


class UserSetPasswordForm(SetPasswordForm):
    """Форма установки нового пароля."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["new_password1"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Новый пароль",
                "autocomplete": "new-password",
            }
        )
        self.fields["new_password2"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Повторите новый пароль",
                "autocomplete": "new-password",
            }
        )
