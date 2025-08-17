from main.models import ReviewTb, ComplaintTb, UserTb, PortfolioTb
from django.forms import ModelForm, Textarea, TextInput
from django import forms
from django.db.models import Q


class ReviewTbForm(ModelForm):
    class Meta:
        model = ReviewTb
        fields = ['review_text']

        widgets = {
            "review_text": Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Напишіть відгук'
            })
        }

        labels = {
            "review_text": "Додайте відгук"
        }

        help_texts = {
            "review_text": "Додайте відгук"
        }


class AddComplaintForm(forms.ModelForm):
    offender = forms.ModelChoiceField(
        queryset=UserTb.objects.filter(is_banned=False),
        to_field_name='username',  # Показує username
        empty_label="Оберіть користувача",
        label="На кого подаєте скаргу",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = ComplaintTb
        fields = ['offender', 'reason', 'description']
        widgets = {
            "description": forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Опишіть причину скарги'
            }),
            "reason": forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)

        if current_user:
            base_queryset = UserTb.objects.exclude(
                Q(id=current_user.id) |                     # виключити себе
                Q(role=UserTb.UserRole.ADMIN) |            # виключити адміністраторів
                Q(is_banned=True)                          # виключити заблокованих
            )

            # --- Вибір доступних користувачів ---
            if current_user.role == UserTb.UserRole.CUSTOMER:
                self.fields['offender'].queryset = base_queryset.filter(
                    role=UserTb.UserRole.PERFORMER
                )
                self.fields['reason'].choices = [
                    ('Відсутність зв`язку з виконавцем', 'Відсутність зв`язку з виконавцем'),
                    ('Робота не відповідає вимогам', 'Робота не відповідає вимогам'),
                    ('Порушення термінів виконання', 'Порушення термінів виконання'),
                    ('Порушення інтелект. власності', 'Порушення інтелект. власності'),
                    ('Неетична поведінка', 'Неетична поведінка'),
                    ('', 'Оберіть причину')
                ]
            elif current_user.role == UserTb.UserRole.PERFORMER:
                self.fields['offender'].queryset = base_queryset.filter(
                    role=UserTb.UserRole.CUSTOMER
                )
                self.fields['reason'].choices = [
                    ('Відсутність зв`язку з замовником', 'Відсутність зв`язку з замовником'),
                    ('Затримка або відмова в оплаті', 'Затримка або відмова в оплаті'),
                    ('Необговорена зміна вимог', 'Необговорена зміна вимог'),
                    ('Неетична поведінка', 'Неетична поведінка'),
                    ('', 'Оберіть причину')
                ]
            else:
                self.fields['offender'].queryset = UserTb.objects.none()
                self.fields['reason'].choices = []


class AddPortfolioForm(forms.ModelForm):
    class Meta:
        model = PortfolioTb
        fields = ['description', 'screenshot']

        widgets = {
            "description": Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Опишіть Вашу пророблену роботу'
            }),
            'screenshot': TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Посилання на зображення'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['screenshot'].required = False  # зробити необов'язковим