from main.models import OrderTb, PerformanceOfferTb
from django import forms
from django.forms import ModelForm, TextInput, DateTimeInput, Textarea, NumberInput


class PerformanceOfferTbForm(forms.ModelForm):
    class Meta:
        model = PerformanceOfferTb
        fields = ['offer_text', 'offer_price', 'is_breaking_agreed']
        widgets = {
            "offer_text": forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Текст Вашої пропозиції'}),
            "offer_price": forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ви пропонуєте ціну'}),
            "is_breaking_agreed": forms.CheckboxInput(attrs={'class': 'form-check-input'})}

        labels = {"is_breaking_agreed": "Чи допускаєте розрив замовником?"}