from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from captcha.fields import CaptchaField
from .models import UserProfile


class RegistrationForm(forms.ModelForm):
    """Форма чтобы регать юзера с  профилем"""
    password = forms.CharField(widget=forms.PasswordInput, label="Пароль")
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Подтверждение пароля")
    phone = forms.CharField(max_length=20, label="Номер телефона")

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("пароли не совп!")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                phone=self.cleaned_data["phone"]
            )
        return user


class LoginWithCaptchaForm(AuthenticationForm):
    """Форма автори с  проверкой капчи."""
    captcha = CaptchaField(label="Введите символы с имеджа")