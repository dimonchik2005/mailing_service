from django.contrib import admin

from mailings.models import (
    Mailing,
    MailingAttempt,
    Message,
    Recipient,
)


@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "full_name",
        "owner",
    )
    search_fields = (
        "email",
        "full_name",
    )
    list_filter = ("owner",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "subject",
        "owner",
    )
    search_fields = ("subject",)
    list_filter = ("owner",)


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "message",
        "start_time",
        "end_time",
        "status",
        "is_active",
        "owner",
    )
    list_filter = (
        "status",
        "is_active",
        "owner",
    )
    search_fields = (
        "message__subject",
        "owner__email",
    )
    filter_horizontal = ("recipients",)


@admin.register(MailingAttempt)
class MailingAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "mailing",
        "attempt_time",
        "status",
    )
    list_filter = (
        "status",
        "attempt_time",
    )
    search_fields = (
        "mailing__message__subject",
        "server_response",
    )
    readonly_fields = ("attempt_time",)