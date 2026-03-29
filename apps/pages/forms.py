from django import forms
from django.utils.translation import gettext_lazy as _


class ContactForm(forms.Form):
    name = forms.CharField(
        label=_("Name"),
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": _("Your name")}),
    )
    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={"placeholder": "you@example.com"}),
    )
    message = forms.CharField(
        label=_("Message"),
        widget=forms.Textarea(attrs={"rows": 5, "placeholder": _("How can we help?")}),
    )
