"""admin forms for the users app"""

from django.contrib.auth.forms import BaseUserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from django.forms import ModelForm, TextInput

from apps.users.models import CustomUser, Niche


class CustomUserCreationForm(BaseUserCreationForm):
    class Meta:
        """Meta class for CustomUserCreationForm"""

        model = CustomUser
        fields = (
            "email",
            "full_name",
            "role",
        )


class CustomUserChangeForm(UserChangeForm):
    """change form: only hashed pass never raw form"""

    class Meta:
        """m.c for CustomUserChangeForm"""

        model = CustomUser
        fields = "__all__"


class NicheAdminForm(ModelForm):
    """NIche form with a placeHolder and our own check of the full name field"""

    MIN_NAME_LEN = 2

    class Meta:
        """m.c for NicheAdminForm"""

        model = Niche
        fields = "__all__"
        widgets = {
            "name": TextInput(attrs={"placeholder": "e.g. Beauty"}),
        }

    def clean_name(self) -> str:
        """checking the field: the niche name must be a real word."""

        name: str = self.cleaned.data["name"]
        if len(name) < self.MIN_NAME_LEN:
            raise ValidationError("The niche name is too short")
        return name.capitalize()
