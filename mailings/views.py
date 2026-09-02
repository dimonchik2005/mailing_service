from django.contrib.auth.mixins import (
    LoginRequiredMixin,
)
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

from mailings.forms import RecipientForm
from mailings.models import Mailing, Recipient


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
