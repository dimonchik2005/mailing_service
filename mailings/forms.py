from django import forms

from mailings.models import Mailing, Message, Recipient


class RecipientForm(forms.ModelForm):
    """Форма создания и редактирования получателя."""

    class Meta:
        model = Recipient
        fields = (
            "email",
            "full_name",
            "comment",
        )
        widgets = {
            "comment": forms.Textarea(
                attrs={"rows": 4},
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = (
                "form-control"
            )


class MessageForm(forms.ModelForm):
    """Форма создания и редактирования сообщения."""

    class Meta:
        model = Message
        fields = (
            "subject",
            "body",
        )
        widgets = {
            "body": forms.Textarea(
                attrs={"rows": 8},
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = (
                "form-control"
            )

class MailingForm(forms.ModelForm):
    """Форма создания и редактирования рассылки."""

    class Meta:
        model = Mailing
        fields = (
            "start_time",
            "end_time",
            "message",
            "recipients",
        )
        widgets = {
            "start_time": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "end_time": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "recipients": forms.SelectMultiple(
                attrs={"size": 8},
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["start_time"].widget.attrs["class"] = (
            "form-control"
        )
        self.fields["end_time"].widget.attrs["class"] = (
            "form-control"
        )
        self.fields["message"].widget.attrs["class"] = (
            "form-select"
        )
        self.fields["recipients"].widget.attrs["class"] = (
            "form-select"
        )

        if user is None:
            self.fields["message"].queryset = (
                Message.objects.none()
            )
            self.fields["recipients"].queryset = (
                Recipient.objects.none()
            )
        else:
            self.fields["message"].queryset = (
                Message.objects.filter(owner=user)
            )
            self.fields["recipients"].queryset = (
                Recipient.objects.filter(owner=user)
            )