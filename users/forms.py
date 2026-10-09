from django import forms
from django.contrib.auth.models import User


class RegisterForm(forms.Form):
    """A deliberately simple registration form: name and password only."""

    name = forms.CharField(
        label="Ime",
        min_length=2,
        max_length=40,
        widget=forms.TextInput(attrs={"autocomplete": "username", "placeholder": "Na primer: Ana"}),
    )
    password = forms.CharField(
        label="Lozinka",
        min_length=8,
        help_text="Najmanje 8 karaktera.",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", "placeholder": "Najmanje 8 karaktera"}),
    )

    def clean_name(self):
        name = " ".join(self.cleaned_data["name"].split())
        if User.objects.filter(username__iexact=name).exists():
            raise forms.ValidationError("Nalog sa ovim imenom već postoji. Izaberi drugo ime.")
        return name

    def save(self):
        return User.objects.create_user(
            username=self.cleaned_data["name"],
            password=self.cleaned_data["password"],
        )
