from django import forms

from mailings.models import Recipient


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