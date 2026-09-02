from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.db.models import Count, Q
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from mailings.forms import MailingForm, MessageForm, RecipientForm
from mailings.models import (
    Mailing,
    MailingAttempt,
    Message,
    Recipient,
)
from mailings.services import send_mailing


def user_is_manager(user) -> bool:
    """Проверяет наличие прав менеджера."""

    return user.has_perm(
        "mailings.can_disable_mailing"
    )


class HomeView(LoginRequiredMixin, TemplateView):
    """Главная страница со статистикой."""

    template_name = "mailings/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_superuser or user_is_manager(user):
            mailings = Mailing.objects.all()
            recipients = Recipient.objects.all()
        else:
            mailings = Mailing.objects.filter(
                owner=user,
            )
            recipients = Recipient.objects.filter(
                owner=user,
            )

        for mailing in mailings:
            mailing.update_status()

        current_time = timezone.now()

        active_mailings = mailings.filter(
            start_time__lte=current_time,
            end_time__gte=current_time,
            status=Mailing.Status.STARTED,
            is_active=True,
        )

        context["total_mailings"] = mailings.count()
        context["active_mailings"] = (
            active_mailings.count()
        )
        context["unique_recipients"] = (
            recipients.count()
        )

        return context


class StatisticsView(
    LoginRequiredMixin,
    TemplateView,
):
    """Отображает статистику рассылок пользователя."""

    template_name = "mailings/statistics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        attempts = (
            MailingAttempt.objects
            .select_related(
                "mailing",
                "mailing__message",
            )
        )

        if not user.is_superuser:
            attempts = attempts.filter(
                mailing__owner=user,
            )

        summary = attempts.aggregate(
            total_attempts=Count("id"),
            successful_attempts=Count(
                "id",
                filter=Q(
                    status=MailingAttempt.Status.SUCCESS,
                ),
            ),
            failed_attempts=Count(
                "id",
                filter=Q(
                    status=MailingAttempt.Status.FAILED,
                ),
            ),
        )

        context.update(summary)
        context["sent_messages"] = (
            summary["successful_attempts"]
        )
        context["recent_attempts"] = attempts[:20]

        return context


class RecipientVisibleQuerysetMixin:
    """Показывает менеджеру всё, пользователю — своё."""

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.is_superuser or user_is_manager(user):
            return queryset

        return queryset.filter(owner=user)


class RecipientOwnerQuerysetMixin:
    """Разрешает изменение только владельцу."""

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.is_superuser:
            return queryset

        return queryset.filter(owner=user)


class RecipientListView(
    LoginRequiredMixin,
    RecipientVisibleQuerysetMixin,
    ListView,
):
    model = Recipient
    template_name = "mailings/recipient_list.html"
    context_object_name = "recipients"


class RecipientDetailView(
    LoginRequiredMixin,
    RecipientVisibleQuerysetMixin,
    DetailView,
):
    model = Recipient
    template_name = "mailings/recipient_detail.html"
    context_object_name = "recipient"


class RecipientCreateView(
    LoginRequiredMixin,
    CreateView,
):
    model = Recipient
    form_class = RecipientForm
    template_name = "mailings/recipient_form.html"
    success_url = reverse_lazy(
        "mailings:recipient_list"
    )

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class RecipientUpdateView(
    LoginRequiredMixin,
    RecipientOwnerQuerysetMixin,
    UpdateView,
):
    model = Recipient
    form_class = RecipientForm
    template_name = "mailings/recipient_form.html"

    def get_success_url(self):
        return reverse(
            "mailings:recipient_detail",
            kwargs={"pk": self.object.pk},
        )


class RecipientDeleteView(
    LoginRequiredMixin,
    RecipientOwnerQuerysetMixin,
    DeleteView,
):
    model = Recipient
    template_name = (
        "mailings/recipient_confirm_delete.html"
    )
    success_url = reverse_lazy(
        "mailings:recipient_list"
    )


class MessageOwnerQuerysetMixin:
    """Показывает пользователю только его сообщения."""

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.is_superuser:
            return queryset

        return queryset.filter(owner=user)


class MessageListView(
    LoginRequiredMixin,
    MessageOwnerQuerysetMixin,
    ListView,
):
    model = Message
    template_name = "mailings/message_list.html"
    context_object_name = "message_list"


class MessageDetailView(
    LoginRequiredMixin,
    MessageOwnerQuerysetMixin,
    DetailView,
):
    model = Message
    template_name = "mailings/message_detail.html"
    context_object_name = "mailing_message"


class MessageCreateView(
    LoginRequiredMixin,
    CreateView,
):
    model = Message
    form_class = MessageForm
    template_name = "mailings/message_form.html"
    success_url = reverse_lazy(
        "mailings:message_list"
    )

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MessageUpdateView(
    LoginRequiredMixin,
    MessageOwnerQuerysetMixin,
    UpdateView,
):
    model = Message
    form_class = MessageForm
    template_name = "mailings/message_form.html"

    def get_success_url(self):
        return reverse(
            "mailings:message_detail",
            kwargs={"pk": self.object.pk},
        )


class MessageDeleteView(
    LoginRequiredMixin,
    MessageOwnerQuerysetMixin,
    DeleteView,
):
    model = Message
    template_name = (
        "mailings/message_confirm_delete.html"
    )
    success_url = reverse_lazy(
        "mailings:message_list"
    )


class MailingVisibleQuerysetMixin:
    """Показывает менеджеру все рассылки, пользователю — свои."""

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .select_related("message", "owner")
            .prefetch_related("recipients")
        )
        user = self.request.user

        if user.is_superuser or user_is_manager(user):
            return queryset

        return queryset.filter(owner=user)


class MailingOwnerQuerysetMixin:
    """Разрешает изменение рассылки только владельцу."""

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.is_superuser:
            return queryset

        return queryset.filter(owner=user)


class MailingListView(
    LoginRequiredMixin,
    MailingVisibleQuerysetMixin,
    ListView,
):
    model = Mailing
    template_name = "mailings/mailing_list.html"
    context_object_name = "mailings"

    def get_queryset(self):
        queryset = super().get_queryset()

        for mailing in queryset:
            mailing.update_status()

        return queryset


class MailingDetailView(
    LoginRequiredMixin,
    MailingVisibleQuerysetMixin,
    DetailView,
):
    model = Mailing
    template_name = "mailings/mailing_detail.html"
    context_object_name = "mailing"

    def get_object(self, queryset=None):
        mailing = super().get_object(queryset)
        mailing.update_status()
        return mailing


class MailingCreateView(
    LoginRequiredMixin,
    CreateView,
):
    model = Mailing
    form_class = MailingForm
    template_name = "mailings/mailing_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "mailings:mailing_detail",
            kwargs={"pk": self.object.pk},
        )


class MailingUpdateView(
    LoginRequiredMixin,
    MailingOwnerQuerysetMixin,
    UpdateView,
):
    model = Mailing
    form_class = MailingForm
    template_name = "mailings/mailing_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        if self.request.user.is_superuser:
            kwargs["user"] = self.object.owner
        else:
            kwargs["user"] = self.request.user

        return kwargs

    def get_success_url(self):
        return reverse(
            "mailings:mailing_detail",
            kwargs={"pk": self.object.pk},
        )


class MailingDeleteView(
    LoginRequiredMixin,
    MailingOwnerQuerysetMixin,
    DeleteView,
):
    model = Mailing
    template_name = (
        "mailings/mailing_confirm_delete.html"
    )
    success_url = reverse_lazy(
        "mailings:mailing_list"
    )


class MailingSendView(
    LoginRequiredMixin,
    View,
):
    """Запускает рассылку вручную."""

    def post(self, request, pk):
        queryset = (
            Mailing.objects
            .select_related("message")
            .prefetch_related("recipients")
        )

        if not request.user.is_superuser:
            queryset = queryset.filter(
                owner=request.user,
            )

        mailing = get_object_or_404(
            queryset,
            pk=pk,
        )

        try:
            successful_count, failed_count = (
                send_mailing(mailing)
            )

            messages.success(
                request,
                (
                    "Рассылка завершена. "
                    f"Успешно: {successful_count}, "
                    f"не успешно: {failed_count}."
                ),
            )

        except ValidationError as error:
            messages.error(
                request,
                " ".join(error.messages),
            )

        return redirect(
            "mailings:mailing_detail",
            pk=mailing.pk,
        )


class MailingDisableView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    View,
):
    """Отключает рассылку по запросу менеджера."""

    permission_required = (
        "mailings.can_disable_mailing"
    )
    raise_exception = True

    def post(self, request, pk):
        mailing = get_object_or_404(
            Mailing,
            pk=pk,
        )

        if not mailing.is_active:
            messages.info(
                request,
                "Рассылка уже отключена.",
            )
        else:
            mailing.is_active = False
            mailing.save(
                update_fields=["is_active"],
            )

            messages.success(
                request,
                "Рассылка отключена.",
            )

        return redirect(
            "mailings:mailing_detail",
            pk=mailing.pk,
        )
