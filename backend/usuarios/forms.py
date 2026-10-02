from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

Usuario = get_user_model()


def exigir(form, *campos):
    """En el modelo son opcionales (por el login con Google), pero estos formularios los piden."""
    for campo in campos:
        form.fields[campo].required = True


class RegistroForm(UserCreationForm):
    """Valida username único, password1 == password2 y los AUTH_PASSWORD_VALIDATORS."""

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ['username', 'email', 'first_name', 'last_name', 'telefono', 'direccion']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        exigir(self, 'telefono', 'direccion')

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise ValidationError('Ya existe un usuario con este email.')
        return email


class PerfilForm(forms.ModelForm):
    """Datos que faltan tras entrar con Google (o para cambiarlos después)."""

    class Meta:
        model = Usuario
        fields = ['telefono', 'direccion']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        exigir(self, *self.Meta.fields)
    