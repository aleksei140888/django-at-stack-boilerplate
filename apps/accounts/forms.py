from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "you@example.com"}),
    )
    first_name = forms.CharField(
        label=_("First name"),
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "given-name"}),
    )
    last_name = forms.CharField(
        label=_("Last name"),
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "family-name"}),
    )
    gdpr_consent = forms.BooleanField(
        label=_("I agree to the Privacy Policy and Terms of Use"),
        required=True,
    )

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "password1", "password2", "gdpr_consent")

    # No save() override on purpose: creating the account (and stamping the
    # consent date with it) belongs to services.register_user, so the management
    # command and any future API endpoint go through the same code path.


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(
            attrs={"autofocus": True, "autocomplete": "email", "placeholder": "you@example.com"}
        ),
    )
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "current-password", "placeholder": "••••••••"}
        ),
    )
    remember_me = forms.BooleanField(label=_("Remember me"), required=False, initial=True)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "bio", "avatar", "email_notifications")
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4}),
        }


class CustomPasswordChangeForm(PasswordChangeForm):
    pass


class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label=_("Email"),
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "you@example.com"}),
    )


class CustomSetPasswordForm(SetPasswordForm):
    pass


class DeleteAccountForm(forms.Form):
    confirm = forms.BooleanField(
        label=_("I understand this action is irreversible"),
        required=True,
    )
    password = forms.CharField(
        label=_("Current password"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if not self.user.check_password(password):
            raise forms.ValidationError(_("Incorrect password."))
        return password
