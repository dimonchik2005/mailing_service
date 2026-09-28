from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.views.generic import CreateView

from users.forms import RegistrationForm

User = get_user_model()


class RegisterView(CreateView):
    """Регистрирует пользователя и отправляет подтверждение."""

    model = User
    form_class = RegistrationForm
    template_name = "users/register.html"

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.is_active = False
        self.object.is_email_verified = False
        self.object.save()

        verification_url = (
            self.request.build_absolute_uri(
                reverse(
                    "users:verify_email",
                    kwargs={
                        "token": self.object.verification_token,
                    },
                )
            )
        )

        send_mail(
            subject="Подтверждение регистрации",
            message=(
                "Для подтверждения регистрации перейдите "
                f"по ссылке:\n{verification_url}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.object.email],
            fail_silently=False,
        )

        messages.success(
            self.request,
            (
                "Регистрация завершена. Ссылка подтверждения "
                "отправлена на вашу почту."
            ),
        )

        return redirect("users:login")


class VerifyEmailView(View):
    """Подтверждает email пользователя."""

    def get(self, request, token):
        selected_user = get_object_or_404(
            User,
            verification_token=token,
        )

        if selected_user.is_email_verified:
            messages.info(
                request,
                "Email уже был подтверждён.",
            )
        else:
            selected_user.is_email_verified = True
            selected_user.is_active = True
            selected_user.save(
                update_fields=[
                    "is_email_verified",
                    "is_active",
                ],
            )

            messages.success(
                request,
                "Email подтверждён. Теперь можно войти.",
            )

        return redirect("users:login")


class UserListView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    ListView,
):
    """Показывает менеджеру список пользователей."""

    model = User
    template_name = "users/user_list.html"
    context_object_name = "users"
    permission_required = "users.can_block_user"
    raise_exception = True
    ordering = ("email",)


class UserToggleActiveView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    View,
):
    """Блокирует или разблокирует пользователя."""

    permission_required = "users.can_block_user"
    raise_exception = True

    def post(self, request, pk):
        selected_user = get_object_or_404(
            User,
            pk=pk,
        )

        if selected_user == request.user:
            messages.error(
                request,
                "Нельзя заблокировать собственный аккаунт.",
            )

        elif selected_user.is_superuser:
            messages.error(
                request,
                "Нельзя заблокировать суперпользователя.",
            )

        else:
            selected_user.is_active = (
                not selected_user.is_active
            )
            selected_user.save(
                update_fields=["is_active"],
            )

            if selected_user.is_active:
                message = "Пользователь разблокирован."
            else:
                message = "Пользователь заблокирован."

            messages.success(
                request,
                message,
            )

        return redirect("users:user_list")
