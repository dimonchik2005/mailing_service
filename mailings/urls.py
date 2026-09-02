from django.urls import path

from mailings.views import (
    HomeView,
    RecipientCreateView,
    RecipientDeleteView,
    RecipientDetailView,
    RecipientListView,
    RecipientUpdateView,
    MessageCreateView,
    MessageDeleteView,
    MessageDetailView,
    MessageListView,
    MessageUpdateView,
)

app_name = "mailings"

urlpatterns = [
    path(
        "",
        HomeView.as_view(),
        name="home",
    ),
    path(
        "recipients/",
        RecipientListView.as_view(),
        name="recipient_list",
    ),
    path(
        "recipients/create/",
        RecipientCreateView.as_view(),
        name="recipient_create",
    ),
    path(
        "recipients/<int:pk>/",
        RecipientDetailView.as_view(),
        name="recipient_detail",
    ),
    path(
        "recipients/<int:pk>/update/",
        RecipientUpdateView.as_view(),
        name="recipient_update",
    ),
    path(
        "recipients/<int:pk>/delete/",
        RecipientDeleteView.as_view(),
        name="recipient_delete",
    ),
    path(
        "messages/",
        MessageListView.as_view(),
        name="message_list",
    ),
    path(
        "messages/create/",
        MessageCreateView.as_view(),
        name="message_create",
    ),
    path(
        "messages/<int:pk>/",
        MessageDetailView.as_view(),
        name="message_detail",
    ),
    path(
        "messages/<int:pk>/update/",
        MessageUpdateView.as_view(),
        name="message_update",
    ),
    path(
        "messages/<int:pk>/delete/",
        MessageDeleteView.as_view(),
        name="message_delete",
    ),
]
