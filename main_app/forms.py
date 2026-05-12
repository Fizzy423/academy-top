# main_app/forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from dal import autocomplete

# Импорты всех моделей
from .models import (
    Abiturient, Roditel, Specialnost, Zdorovie, Document, Dogovor, AbiturientRoditel
)

# ----------------------------------------
# Пользовательская форма для авторизации
# ----------------------------------------
class CustomAuthForm(AuthenticationForm):
    error_messages = {
        'invalid_login': "Неверный логин или пароль. Пожалуйста, попробуйте снова.",
        'inactive': "Ваш аккаунт не активен.",
    }


# ------------------------------
# Форма для родителей (Roditel) 
# ------------------------------
class RoditelForm(forms.ModelForm):
    class Meta:
        model = Roditel
        fields = ['fio', 'phone', 'email', 'workplace', 'address'] 
        labels = {
            'fio': 'ФИО родителя',
            'phone': 'Номер телефона',
            'email': 'Электронная почта',
            'workplace': 'Место работы',
            'address': 'Адрес проживания',
        }
        widgets = {
            'fio': forms.TextInput(attrs={'class': 'form-control'}), 
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (900) 000-00-00'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@mail.ru'}),
            'workplace': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название организации, должность'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Город, улица, дом, кв.'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
       
        if self.prefix == 'father':
            self.fields['fio'].widget.attrs['placeholder'] = 'Иванов Иван Иванович'
        elif self.prefix == 'mother':
            self.fields['fio'].widget.attrs['placeholder'] = 'Иванова Мария Ивановна'
        else:
            self.fields['fio'].widget.attrs['placeholder'] = 'Иванов Иван Иванович'


# ------------------------------
# Форма для здоровья (Zdorovie)
# ------------------------------
class ZdorovieForm(forms.ModelForm):
    class Meta:
        model = Zdorovie
        fields = ['diseases', 'disability', 'restrictions', 'additional_info']
        labels = {
            'diseases': 'Информация о заболеваниях',
            'disability': 'Инвалидность',
            'restrictions': 'Ограничения для занятий физкультурой',
            'additional_info': 'Дополнительная информация',
        }
        widgets = {
            'diseases': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Опишите заболевания, если есть'}),
            'disability': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'restrictions': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Например: подготовительная группа'}),
            'additional_info': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


# -----------------------------------
# Форма для абитуриента (Abiturient)
# -----------------------------------
class AbiturientForm(forms.ModelForm):
    class Meta:
        model = Abiturient
        fields = [
            'fio', 'date_of_birth', 'class_of_entry', 'specialnost',
            'hobby', 'phone', 'address', 'email', 'is_guardianship',
        ]
        labels = {
            'fio': 'ФИО студента',
            'date_of_birth': 'Дата рождения студента',
            'class_of_entry': 'На базе какого класса поступил',
            'specialnost': 'Специальность',
            'hobby': 'Хобби и увлечения',
            'phone': 'Номер телефона студента',
            'address': 'Адрес проживания (фактический)',
            'email': 'Электронная почта студента',
            'is_guardianship': 'Опекунство или сирота',
        }
        widgets = {
            'fio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иванов Иван Иванович'}),
            'date_of_birth': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'class_of_entry': forms.Select(attrs={'class': 'form-select'}),
            'specialnost': forms.Select(attrs={'class': 'form-select'}),
            'hobby': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Рисование, программирование и т.д.'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (900) 123-45-67'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'г. Москва, ул. Ленина, д. 1'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'student@example.com'}),
            'is_guardianship': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# -------------------------------
# Форма для документа (Document)
# -------------------------------
class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['type', 'available', 'scan'] 
        labels = {
            'type': 'Тип документа',
            'available': 'Наличие (да/нет)',
            'scan': 'Прикрепить скан/фото',
        }
        widgets = {
            'type': forms.Select(attrs={'class': 'form-select'}),
            'available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'scan': forms.FileInput(attrs={'class': 'form-control'}), 
        }


# -----------------------------
# Форма для договора (Dogovor) 
# -----------------------------
class DogovorForm(forms.ModelForm):
    class Meta:
        model = Dogovor
        fields = [
            'number', 'date_of_conclusion', 'payment_form', 
            'maternity_capital', 'credit', 'abiturient', 'roditel_zakazchik'
        ]
        
        labels = {
            'number': 'Номер договора',
            'date_of_conclusion': 'Дата заключения договора',
            'payment_form': 'Форма оплаты',
            'maternity_capital': 'Оплата по материнскому капиталу (да/нет)',
            'credit': 'Образовательный кредит (да/нет)',
            'abiturient': 'Абитуриент (студент)',
            'roditel_zakazchik': 'ФИО родителя (заказчика)',
        }
        widgets = {
            'abiturient': autocomplete.ModelSelect2(
                url='abiturient-autocomplete',
                attrs={
                    'data-placeholder': 'Начните вводить ФИО студента...',
                    'data-minimum-input-length': 2,
                }
            ),
            'roditel_zakazchik': autocomplete.ModelSelect2(
                url='roditel-autocomplete',
                forward=['abiturient'],
                attrs={
                    'data-placeholder': 'Выберите родителя...', 
                    'data-minimum-input-length': 0
                }
            ),
            'date_of_conclusion': forms.DateInput(
                format='%Y-%m-%d', 
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Напр. 123/24'}),
            'payment_form': forms.Select(attrs={'class': 'form-select'}),
            'maternity_capital': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'credit': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['abiturient', 'roditel_zakazchik', 'maternity_capital', 'credit']:
                if isinstance(field.widget, (forms.TextInput, forms.DateInput, forms.Textarea, forms.EmailInput)):
                    field.widget.attrs.update({'class': 'form-control'})
                elif isinstance(field.widget, forms.Select):
                    field.widget.attrs.update({'class': 'form-select'})


class StudentEnrollForm(forms.ModelForm):
    class Meta:
        model = Abiturient
        fields = ['student_group', 'enrollment_date']
        labels = {
            'student_group': 'Номер группы',
            'enrollment_date': 'Дата зачисления',
        }
        widgets = {
            'student_group': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Например: ПОВ-24'
            }),
            'enrollment_date': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control'
            }),
        }