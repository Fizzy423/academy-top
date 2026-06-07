from django.contrib import admin
from .models import (
    Abiturient, Roditel, Specialnost, Zdorovie,
    AbiturientRoditel, Document, Dogovor,
)


class AbiturientRoditelInline(admin.TabularInline):
    """Inline редактирование связей между абитуриентом и родителями."""
    model = AbiturientRoditel
    extra = 1
    autocomplete_fields = ['roditel']


@admin.register(Abiturient)
class AbiturientAdmin(admin.ModelAdmin):
    list_display = ('fio', 'date_of_birth', 'class_of_entry', 'phone', 'email', 'specialnost', 'is_guardianship')
    search_fields = ('fio', 'phone', 'email')
    list_filter = ('class_of_entry', 'specialnost', 'is_guardianship')
    ordering = ('fio',)
    list_per_page = 25
    inlines = [AbiturientRoditelInline]
    autocomplete_fields = ['specialnost']
    list_select_related = ('specialnost',)


@admin.register(Roditel)
class RoditelAdmin(admin.ModelAdmin):
    list_display = ('fio', 'phone', 'email', 'workplace')
    search_fields = ('fio', 'phone', 'email', 'workplace')
    ordering = ('fio',)
    list_per_page = 25


@admin.register(Specialnost)
class SpecialnostAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)
    list_per_page = 25


@admin.register(Zdorovie)
class ZdorovieAdmin(admin.ModelAdmin):
    list_display = ('abiturient', 'diseases', 'disability', 'restrictions')
    search_fields = ('abiturient__fio', 'diseases', 'restrictions')
    list_filter = ('disability',)
    list_per_page = 25
    list_select_related = ('abiturient',)


@admin.register(AbiturientRoditel)
class AbiturientRoditelAdmin(admin.ModelAdmin):
    list_display = ('abiturient', 'roditel', 'relation_type')
    list_filter = ('relation_type',)
    search_fields = ('abiturient__fio', 'roditel__fio', 'relation_type')
    list_per_page = 25
    autocomplete_fields = ['abiturient', 'roditel']
    list_select_related = ('abiturient', 'roditel')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('type', 'available', 'abiturient', 'description')
    list_filter = ('type', 'available')
    search_fields = ('type', 'abiturient__fio', 'description')
    list_per_page = 25
    autocomplete_fields = ['abiturient']
    list_select_related = ('abiturient',)


@admin.register(Dogovor)
class DogovorAdmin(admin.ModelAdmin):
    list_display = ('number', 'date_of_conclusion', 'payment_form', 'is_paid', 'abiturient', 'roditel_zakazchik')
    list_filter = ('payment_form', 'date_of_conclusion', 'maternity_capital', 'credit', 'is_paid') # <--- добавили is_paid
    search_fields = ('number', 'abiturient__fio', 'roditel_zakazchik__fio')
    list_per_page = 25
    autocomplete_fields = ['abiturient', 'roditel_zakazchik']
    list_select_related = ('abiturient', 'roditel_zakazchik')