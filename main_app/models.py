# main_app/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
# Импортируем наши валидаторы
from validators import validate_file_extension, validate_file_size 

# ---- ОПРЕДЕЛЕНИЯ МОДЕЛЕЙ ----

class News(models.Model):
    content = models.TextField(verbose_name="Содержание")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return self.content[:50]

    class Meta:
        verbose_name = "Новость"
        verbose_name_plural = "Новости"
        ordering = ['-created_at'] 


class Roditel(models.Model):
    fio = models.CharField(max_length=255, verbose_name="ФИО родителя")
    workplace = models.CharField(max_length=255, blank=True, null=True, verbose_name="Место работы")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name="Адрес") 
    email = models.EmailField(blank=True, null=True, verbose_name="Email")

    def __str__(self):
        return self.fio

    class Meta:
        verbose_name = "Родитель"
        verbose_name_plural = "Родители"


class Specialnost(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Название специальности")
    code = models.CharField(max_length=50, unique=True, null=True, blank=True, verbose_name="Код специальности")
    description = models.TextField(blank=True, verbose_name="Описание")

    def __str__(self):
        return f"{self.code if self.code else 'Без кода'} - {self.name}" 

    class Meta:
        verbose_name = "Специальность"
        verbose_name_plural = "Специальности"


class Abiturient(models.Model):
    CLASS_CHOICES = [
        ('9', '9 класс'),
        ('11', '11 класс'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь", blank=True, null=True)
    fio = models.CharField(max_length=255, verbose_name="ФИО")
    date_of_birth = models.DateField(verbose_name="Дата рождения")
    class_of_entry = models.CharField(max_length=2, choices=CLASS_CHOICES, verbose_name="Класс поступления")
    specialnost = models.ForeignKey(Specialnost, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Специальность")
    hobby = models.CharField(max_length=255, blank=True, verbose_name="Хобби")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    address = models.CharField(max_length=255, verbose_name="Адрес")
    email = models.EmailField(verbose_name="Электронная почта")
    is_guardianship = models.BooleanField(default=False, verbose_name="Опекунство или сирота")

    parents = models.ManyToManyField(Roditel, through='AbiturientRoditel', related_name='abiturients', verbose_name="Родители")

    def __str__(self):
        return self.fio

    class Meta:
        verbose_name = "Абитуриент"
        verbose_name_plural = "Абитуриенты"
        ordering = ['fio']


class Zdorovie(models.Model):
    diseases = models.TextField(blank=True, verbose_name="Заболевания")
    disability = models.BooleanField(default=False, verbose_name="Инвалидность")
    restrictions = models.TextField(blank=True, verbose_name="Ограничения для занятий физкультурой")
    additional_info = models.TextField(blank=True, verbose_name="Дополнительная информация")

    abiturient = models.OneToOneField(
        Abiturient,
        on_delete=models.CASCADE,
        related_name='health_info', 
        null=True,
        blank=True,
        verbose_name="Абитуриент"
    )

    def __str__(self):
        return f"Здоровье ({self.abiturient.fio if self.abiturient else 'Нет абитуриента'})"

    class Meta:
        verbose_name = "Здоровье"
        verbose_name_plural = "Здоровье"


class AbiturientRoditel(models.Model):
    abiturient = models.ForeignKey(Abiturient, on_delete=models.CASCADE, verbose_name="Абитуриент")
    roditel = models.ForeignKey(Roditel, on_delete=models.CASCADE, verbose_name="Родитель")
    relation_type = models.CharField(max_length=100, blank=True, verbose_name="Тип родства")

    class Meta:
        unique_together = ('abiturient', 'roditel')
        verbose_name = "Связь абитуриента и родителя"
        verbose_name_plural = "Связи абитуриентов и родителей"

    def __str__(self):
        abiturient_fio = self.abiturient.fio if self.abiturient else 'Неизвестный абитуриент'
        roditel_fio = self.roditel.fio if self.roditel else 'Неизвестный родитель'
        return f"{abiturient_fio} - {roditel_fio} ({self.relation_type})"


class Document(models.Model):
    DOCUMENT_TYPES = [
          ('package', 'Полный пакет документов (одним файлом)')
    ]

    abiturient = models.ForeignKey(Abiturient, on_delete=models.CASCADE, related_name='documents', verbose_name="Абитуриент")
    type = models.CharField(max_length=50, choices=DOCUMENT_TYPES, verbose_name="Тип документа")
    available = models.BooleanField(default=False, verbose_name="Доступен")
    
    # ПРИМЕНЯЕМ ВАЛИДАТОРЫ ЗДЕСЬ:
    scan = models.FileField(
        upload_to='documents/', 
        blank=True, 
        null=True, 
        verbose_name="Скан документа",
        validators=[validate_file_extension, validate_file_size] # Добавлено
    )
    
    description = models.TextField(blank=True, verbose_name="Описание документа")
    upload_date = models.DateTimeField(default=timezone.now, verbose_name="Дата загрузки")

    def __str__(self):
        return f"{self.get_type_display()} для {self.abiturient.fio if self.abiturient else 'Неизвестного абитуриента'}"

    class Meta:
        verbose_name = "Документ"
        verbose_name_plural = "Документы"


class Dogovor(models.Model):
    PAYMENT_FORMS = [
    ('monthly', 'Помесячно'),
    ('semester', 'По семестрам'),
    ('yearly', 'За год'),
]

    number = models.CharField(max_length=50, unique=True, verbose_name="Номер договора")
    date_of_conclusion = models.DateField(default=timezone.now, verbose_name="Дата заключения")
    payment_form = models.CharField(max_length=10, choices=PAYMENT_FORMS, default='contract', verbose_name="Форма оплаты")
    maternity_capital = models.BooleanField(default=False, verbose_name="Материнский капитал")
    credit = models.BooleanField(default=False, verbose_name="Кредит")

    abiturient = models.ForeignKey(Abiturient, on_delete=models.CASCADE, related_name='dogovors', verbose_name="Абитуриент")
    roditel_zakazchik = models.ForeignKey(Roditel, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Родитель-заказчик")

    def __str__(self):
        return f"Договор №{self.number} ({self.abiturient.fio if self.abiturient else 'Неизвестный абитуриент'})"
    

    class Meta:
        verbose_name = "Договор"
        verbose_name_plural = "Договоры"