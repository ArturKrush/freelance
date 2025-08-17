from django import forms
from django.forms import ModelForm, TextInput
from .models import SpecialtyTb, SpecBranchTb, UserTb

class PerformerFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="Ім'я виконавця",
        widget=forms.TextInput(attrs={'placeholder': "Ім'я виконавця"})
    )
    specialty = forms.ModelChoiceField(
        queryset=SpecialtyTb.objects.all(),
        required=False,
        label='Спеціальність'
    )
    branch = forms.ModelMultipleChoiceField(
        queryset=SpecBranchTb.objects.all(),  # Завантажуємо всі напрямки (не none)
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Напрямки'
    )
    min_cost = forms.IntegerField(
        required=False,
        min_value=0,
        label='Мін. вартість'
    )
    max_cost = forms.IntegerField(
        required=False,
        min_value=0,
        label='Макс. вартість'
    )
    AVAILABILITY_CHOICES = (
        ('', 'Неважливо'),
        ('available', 'Тільки вільні'),
    )
    availability = forms.ChoiceField(choices=AVAILABILITY_CHOICES, required=False, label='Готовність')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Отримаємо вибрану спеціальність з переданих даних (якщо є)
        specialty = None
        if 'specialty' in self.data:
            try:
                specialty_id = int(self.data.get('specialty'))
                specialty = SpecialtyTb.objects.filter(id=specialty_id).first()
            except (ValueError, TypeError):
                pass
        # Якщо спеціальність вибрана — підвантажуємо напрямки для неї
        if specialty:
            self.fields['branch'].queryset = SpecBranchTb.objects.filter(specialty=specialty)
        else:
            self.fields['branch'].queryset = SpecBranchTb.objects.none()


class PgLoginForm(forms.Form):
    username = forms.CharField(label="Логін", max_length=150)
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)


class ChangeClientProfileTbForm(ModelForm):
    class Meta:
        model = UserTb
        fields = ['email', 'phone_num', 'account', 'city']

        widgets = {
            "email": TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ваш email'
            }),
            "phone_num": TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ваш номер телефона'
            }),
            "account": TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Ваш банківський рахунок'
                }
            )
        }

class ClientSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="Ім'я замовника",
        widget=forms.TextInput(attrs={'placeholder': "Ім'я замовника"})
    )

'''
class ChangeAdminProfileTbForm(ModelForm):
    class Meta:
        model = UserTb
        fields = ['email', 'phone_num', 'account', 'city']

        widgets = {
            "email": TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ваш email'
            }),
            "phone_num": TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ваш номер телефона'
            }),
            "account": TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Ваш банківський рахунок'
                }
            )
        }
'''