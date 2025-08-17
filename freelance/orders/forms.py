from main.models import OrderTb, SpecBranchTb, ProgressTb, SpecialtyTb
from django import forms
from django.forms import ModelForm, TextInput, DateTimeInput, Textarea, NumberInput


class OrderTbForm(forms.ModelForm):
    spec_branches = forms.ModelMultipleChoiceField(
        queryset=SpecBranchTb.objects.all(),
        widget=forms.CheckboxSelectMultiple,  # або SelectMultiple, якщо потрібен випадаючий список
        required=True,
        label="Напрямки замовлення"
    )

    class Meta:
        model = OrderTb
        fields = ['topic', 'description', 'order_deadline', 'spec_branches']
        widgets = {
            "topic": forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Topic'}),
            "description": forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Description'}),
            "order_deadline": forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            )
        }
        labels = {"order_deadline": "Deadline для замовлення"}
        help_texts = {"order_deadline": "Вкажіть крайній термін виконання"}

class CompleteOrderTbForm(forms.Form):
    ORDER_STATUS_CHOICES = [
        ('Виконане успішно', 'Виконане успішно'),
        ('Виконане невдало', 'Виконане невдало'),
    ]

    order_status = forms.ChoiceField(choices=ORDER_STATUS_CHOICES, widget=forms.Select(attrs={
        'class': 'form-control',
        'placeholder': 'Виконане успішно чи невдало'
    }))
    performance_grade = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={
        'class': 'form-control',
        'placeholder': 'Оцінка (1-10)'
    }))
    final_review = forms.CharField(required=False, widget=forms.Textarea(attrs={
        'class': 'form-control',
        'placeholder': 'Відгук'
    }))


class ProgressTbForm(ModelForm):
    class Meta:
        model = ProgressTb
        fields = ['text_info', 'screenshot']

        widgets = {
            "text_info": Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Опишіть пророблену роботу (ітерацію)'
            }),
            'screenshot': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Посилання на зображення'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['screenshot'].required = False  # зробити необов'язковим


class OrderFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="Тема замовлення",
        widget=forms.TextInput(attrs={'placeholder': "Ключові слова в темі (назві) замовлення"})
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        specialty = None
        if 'specialty' in self.data:
            try:
                specialty_id = int(self.data.get('specialty'))
                specialty = SpecialtyTb.objects.filter(id=specialty_id).first()
            except (ValueError, TypeError):
                pass

        if specialty:
            self.fields['branch'].queryset = SpecBranchTb.objects.filter(specialty=specialty)
        else:
            # Видаляємо поле, якщо спеціальність не вибрана
            self.fields.pop('branch')