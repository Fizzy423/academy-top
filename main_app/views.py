# main_app/views.py
# main_app/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, DeleteView, CreateView, UpdateView
from django.views.decorators.http import require_POST, require_GET
from django_filters.views import FilterView
import django_filters
from django.forms import inlineformset_factory
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse 
from django import forms
from dal_select2.views import Select2QuerySetView 
from django.utils import timezone
from django.db import models
from docxtpl import DocxTemplate
import os
from django.conf import settings
from django.core.exceptions import PermissionDenied

# Импорты моделей
from .models import (
    Abiturient, Dogovor, Document, Roditel, Specialnost,
    Zdorovie, AbiturientRoditel, News
)
# Импорты форм
from .forms import (
    AbiturientForm, RoditelForm, DocumentForm,
    DogovorForm, CustomAuthForm, ZdorovieForm,
    StudentEnrollForm  
)

# -----------------------------
# Вспомогательные функции и миксины
# -----------------------------
def is_staff_check(user):
    """Проверка, является ли пользователь сотрудником."""
    return user.is_authenticated and user.is_staff

class StaffRequiredMixin(UserPassesTestMixin):
    """Миксин для ограничения доступа только для персонала."""
    def test_func(self):
        return is_staff_check(self.request.user)

# Миксин для проверки прав менеджера (если нужно)
def is_manager_check(user):
    return user.groups.filter(name='Менеджер').exists()

# -----------------------------
# Формсеты
# -----------------------------
DocumentFormSet = inlineformset_factory(
    Abiturient,
    Document,
    form=DocumentForm,
    extra=1,
    can_delete=True
)

# ------------
# Авторизация
# ------------
class CustomLoginView(LoginView):
    template_name = 'main_app/login.html'
    authentication_form = CustomAuthForm

    def form_invalid(self, form):
        messages.error(self.request, "Неверный логин или пароль.")
        return super().form_invalid(form)

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "Вы вышли из системы.")
    return redirect('login')

# ---------------------------
# Специальности (Администрирование)
# ---------------------------
class SpecialnostUpdateView(StaffRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        # Только суперпользователь может редактировать специальности
        return self.request.user.is_superuser
    
    def handle_no_permission(self):
        raise PermissionDenied("У вас нет прав на редактирование специальностей.")

# ---------------------------
# Главная панель (Dashboard)
# ---------------------------
@login_required
@user_passes_test(is_staff_check)
def dashboard(request):
    context = {
        'abiturient_count': Abiturient.objects.count(),
        'student_count': Abiturient.objects.filter(status='student').count(),
        'dogovor_count': Dogovor.objects.count(),
        'recent_abiturients': Abiturient.objects.all().order_by('-pk')[:3],
        'recent_dogovors': Dogovor.objects.all().order_by('-pk')[:3],
        'recent_students': Abiturient.objects.filter(status='student').order_by('-enrollment_date')[:3],
        'has_any_search_data': Abiturient.objects.exists() or Dogovor.objects.exists(), 
    }
    return render(request, 'main_app/dashboard.html', context)

# -----------------------------
# Абитуриенты и студенты
# -----------------------------
class AbiturientFilter(django_filters.FilterSet):
    fio = django_filters.CharFilter(lookup_expr='icontains', label='ФИО')
    status = django_filters.ChoiceFilter(choices=Abiturient.STATUS_CHOICES, label='Статус')
    
    class Meta:
        model = Abiturient
        fields = ['fio', 'class_of_entry', 'specialnost', 'status']

class AbiturientListView(LoginRequiredMixin, StaffRequiredMixin, FilterView):
    model = Abiturient
    paginate_by = 10
    filterset_class = AbiturientFilter
    template_name = 'main_app/abiturient_list.html'
    context_object_name = 'abiturients'

class StudentListView(AbiturientListView):
    template_name = 'main_app/student_list.html' 
    context_object_name = 'students'

    def get_queryset(self):
        return Abiturient.objects.filter(status='student')

class AbiturientDetailView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    model = Abiturient
    template_name = 'main_app/abiturient_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['health_info'] = getattr(self.object, 'health_info', None)
        context['documents'] = self.object.documents.all()
        context['dogovors'] = self.object.dogovors.all()
        parent_relations = AbiturientRoditel.objects.filter(abiturient=self.object).select_related('roditel')
        context['mother_info'] = next((r.roditel for r in parent_relations if r.relation_type.lower() == 'мать'), None)
        context['father_info'] = next((r.roditel for r in parent_relations if r.relation_type.lower() == 'отец'), None)
        return context

# -----------------------------
# Создание и редактирование абитуриентов
# -----------------------------
class AbiturientFormViewMixin(LoginRequiredMixin, StaffRequiredMixin):
    form_class = AbiturientForm
    template_name = 'main_app/abiturient_form.html'
    success_url = reverse_lazy('abiturient_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = getattr(self, 'object', None)
        
        mother_inst = father_inst = None
        if obj:
            m_rel = AbiturientRoditel.objects.filter(abiturient=obj, relation_type__iexact='мать').first()
            f_rel = AbiturientRoditel.objects.filter(abiturient=obj, relation_type__iexact='отец').first()
            if m_rel: mother_inst = m_rel.roditel
            if f_rel: father_inst = f_rel.roditel

        if self.request.method == 'POST':
            context['mother_form'] = RoditelForm(self.request.POST, prefix='mother', instance=mother_inst)
            context['father_form'] = RoditelForm(self.request.POST, prefix='father', instance=father_inst)
            context['health_form'] = ZdorovieForm(self.request.POST, prefix='health', instance=getattr(obj, 'health_info', None))
            context['formset'] = DocumentFormSet(self.request.POST, self.request.FILES, instance=obj)
        else:
            context['mother_form'] = RoditelForm(prefix='mother', instance=mother_inst)
            context['father_form'] = RoditelForm(prefix='father', instance=father_inst)
            context['health_form'] = ZdorovieForm(prefix='health', instance=getattr(obj, 'health_info', None))
            context['formset'] = DocumentFormSet(instance=obj)
        
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object() if 'pk' in kwargs else None
        context = self.get_context_data()
        form = self.get_form()
        m_form = context['mother_form']
        f_form = context['father_form']
        h_form = context['health_form']
        formset = context['formset']

        if all([form.is_valid(), m_form.is_valid(), f_form.is_valid(), h_form.is_valid(), formset.is_valid()]):
            with transaction.atomic():
                abiturient = form.save(commit=False)
                
                if not abiturient.reg_number:
                    last_number = Abiturient.objects.aggregate(models.Max('reg_number'))['reg_number__max'] or 0
                    abiturient.reg_number = last_number + 1
                
                abiturient.save()

                for r_form, r_type in [(m_form, 'мать'), (f_form, 'отец')]:
                    if r_form.cleaned_data.get('fio') or r_form.cleaned_data.get('phone'):
                        parent = r_form.save()
                        AbiturientRoditel.objects.update_or_create(
                            abiturient=abiturient, relation_type=r_type, defaults={'roditel': parent}
                        )
                health = h_form.save(commit=False)
                health.abiturient = abiturient
                health.save()
                formset.instance = abiturient
                formset.save()

            messages.success(request, "Данные успешно сохранены!")
            return redirect(self.success_url)
        return self.render_to_response(self.get_context_data(form=form))

class AbiturientCreateView(AbiturientFormViewMixin, CreateView):
    model = Abiturient

class AbiturientUpdateView(AbiturientFormViewMixin, UpdateView):
    model = Abiturient

class AbiturientDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = Abiturient
    template_name = 'main_app/abiturient_confirm_delete.html'
    success_url = reverse_lazy('abiturient_list')

# ---------
# Договоры
# ---------
class DogovorListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = Dogovor
    template_name = 'main_app/dogovor_list.html'
    context_object_name = 'dogovors'
    paginate_by = 10

class DogovorDetailView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    model = Dogovor
    template_name = 'main_app/dogovor_detail.html'

class DogovorCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = Dogovor
    form_class = DogovorForm
    template_name = 'main_app/dogovor_form.html'
    
    def get_initial(self):
        initial = super().get_initial()
        abiturient_id = self.request.GET.get('abiturient') or self.kwargs.get('abiturient_id')
        if abiturient_id: 
            initial['abiturient'] = get_object_or_404(Abiturient, pk=abiturient_id)
        return initial

    def form_valid(self, form):

        self.object = form.save(commit=False)
        abiturient = self.object.abiturient
        
        if abiturient.specialnost and not abiturient.specialnost.has_places():
            messages.error(self.request, f"Ошибка: На специальности '{abiturient.specialnost.name}' не осталось свободных мест!")
            return self.form_invalid(form)

        self.object.save()
        
        if abiturient.status == 'abiturient':
            abiturient.status = 'student'
            abiturient.enrollment_date = timezone.now().date()
            abiturient.save()
            messages.success(self.request, f"Договор сохранен! {abiturient.fio} автоматически зачислен(а) в студенты.")
        else:
            messages.success(self.request, "Договор успешно добавлен.")
            
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy('abiturient_detail', kwargs={'pk': self.object.abiturient.pk})

class DogovorUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    model = Dogovor
    form_class = DogovorForm
    template_name = 'main_app/dogovor_form.html'
    
    def get_success_url(self):
        return reverse_lazy('abiturient_detail', kwargs={'pk': self.object.abiturient.pk})

class DogovorDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model = Dogovor
    template_name = 'main_app/dogovor_confirm_delete.html'
    success_url = reverse_lazy('dogovor_list')

# --------------------
# Зачисление студента
# --------------------
@login_required
@user_passes_test(is_staff_check)
def enroll_student(request, pk):
    abiturient = get_object_or_404(Abiturient, pk=pk)
    
    if request.method == 'POST':
        form = StudentEnrollForm(request.POST, instance=abiturient)
        if form.is_valid():
            student = form.save(commit=False)
            student.status = 'student'
            if not student.enrollment_date:
                student.enrollment_date = timezone.now().date()
            student.save()
            messages.success(request, f"{student.fio} официально зачислен в группу {student.student_group}!")
            return redirect('abiturient_detail', pk=pk)
    
    return redirect('abiturient_detail', pk=pk)

# --------------------
# Документы и Новости
# --------------------
class DocumentCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = Document
    form_class = DocumentForm
    template_name = 'main_app/document_form.html'
    
    def get_success_url(self): 
        return reverse_lazy('abiturient_list')

@login_required
def get_news(request):
    """Информация о новостях (доступна всем авторизованным)."""
    news = News.objects.first()
    return JsonResponse({'success': True, 'content': news.content if news else ""})

@login_required
@require_POST
def save_news(request):
    """Сохранение новостей (только для персонала)."""
    if not request.user.is_staff: 
        return JsonResponse({'success': False}, status=403)
    content = request.POST.get('content', '').strip()
    news, _ = News.objects.get_or_create(pk=1)
    news.content = content
    news.save()
    return JsonResponse({'success': True})

# -----------------------
# Поиск (Строго защищен)
# -----------------------
@login_required
@require_GET
def search_students(request):
    if not request.user.is_staff:
        return JsonResponse({'results': [], 'error': 'Forbidden'}, status=403)
    
    q = request.GET.get('q', '').strip()
    results = []
    if q:
        abits = Abiturient.objects.filter(
            Q(fio__icontains=q) | Q(phone__icontains=q)
        ).exclude(status='expelled')[:5]
        for a in abits:
            results.append({
                'id': a.id, 
                'fio': a.fio, 
                'phone': a.phone, 
                'status': a.get_status_display(),
                'type': 'abiturient'
            })
        dogs = Dogovor.objects.filter(Q(number__icontains=q) | Q(abiturient__fio__icontains=q))[:5]
        for d in dogs:
            results.append({
                'id': d.id, 
                'number': d.number, 
                'abiturient_fio': d.abiturient.fio if d.abiturient else '', 
                'type': 'dogovor'
            })
    return JsonResponse({'results': results})

@login_required
def search_students_legacy(request):
    return search_students(request)

# -----------------------------
# Autocomplete (DAL) - Только для персонала
# -----------------------------
class AbiturientAutocomplete(LoginRequiredMixin, StaffRequiredMixin, Select2QuerySetView):
    def get_queryset(self):
        qs = Abiturient.objects.all().order_by('fio') 
        if self.q: 
            qs = qs.filter(fio__icontains=self.q)
        return qs

class RoditelAutocomplete(LoginRequiredMixin, StaffRequiredMixin, Select2QuerySetView):
    def get_queryset(self):
        qs = Roditel.objects.all()
        forwarded = self.forwarded.get('abiturient', None)
        if forwarded: 
            qs = qs.filter(abiturientroditel__abiturient_id=forwarded)
        if self.q: 
            qs = qs.filter(fio__icontains=self.q)
        return qs

class SpecialnostAutocomplete(LoginRequiredMixin, StaffRequiredMixin, Select2QuerySetView):
    def get_queryset(self):
        qs = Specialnost.objects.all()
        if self.q: 
            qs = qs.filter(Q(name__icontains=self.q) | Q(code__icontains=self.q))
        return qs

# -----------------------------
# AJAX-инфо (Только для персонала)
# -----------------------------
@login_required
@require_GET
def get_parents_by_abiturient_ajax(request, abiturient_id):
    if not request.user.is_staff: 
        return JsonResponse({'parents': []}, status=403)
    relations = AbiturientRoditel.objects.filter(abiturient_id=abiturient_id).select_related('roditel')
    parents = [{'id': r.roditel.id, 'fio': r.roditel.fio} for r in relations]
    return JsonResponse({'parents': parents})

@login_required
def get_abit_info_ajax(request, abit_id):
    if not request.user.is_staff: 
        return JsonResponse({'error': 'Forbidden'}, status=403)
    abit = get_object_or_404(Abiturient, pk=abit_id)
    spec_code = abit.specialnost.code if abit.specialnost and abit.specialnost.code else "00"
    return JsonResponse({
        'spec_code': spec_code,
        'abit_id': abit.id,
        'status': abit.status,
        'status_display': abit.get_status_display()
    })


# =============================================================
# Генерация договора
# =============================================================

# Сроки обучения: ключ = (код специальности, класс поступления)
# Значение = (продолжительность, период обучения)
# Если добавишь новую специальность — просто допиши строку сюда
STUDY_DURATIONS = {
    ('09.02.07', '9'):  ('3 года 10 месяцев', 'с 01.09.2026 по 30.06.2030'),
    ('09.02.07', '11'): ('2 года 10 месяцев', 'с 01.09.2026 по 30.06.2029'),
    ('54.02.01', '9'):  ('3 года 10 месяцев', 'с 01.09.2026 по 30.06.2030'),
    ('54.02.01', '11'): ('1 год 10 месяцев',  'с 01.09.2026 по 30.06.2028'),
}

# Названия форм оплаты для договора
PAYMENT_FORM_LABELS = {
    'monthly':  '10 частей в учебном году',
    'semester': '2 части в учебном году',
    'yearly':   '1 часть в учебном году',
}

# Размер первого платежа по форме оплаты
FIRST_PAYMENT = {
    'monthly':  '77 000',
    'semester': '182 875',
    'yearly':   '346 500',
}


@login_required
@user_passes_test(is_staff_check)
def download_dogovor_docx(request, pk):
    dogovor = get_object_or_404(Dogovor, pk=pk)
    abit = dogovor.abiturient

    template_path = os.path.join(
        settings.BASE_DIR, 'main_app', 'templates',
        'templates_doc', 'dogovor_blagov_template.docx'
    )

    doc = DocxTemplate(template_path)

    # --- Специальность ---
    spec = abit.specialnost
    specialty_code = spec.code if spec else '___'
    specialty_name = spec.name if spec else '___________'

    # --- Срок обучения (зависит от специальности и класса поступления) ---
    key = (specialty_code, abit.class_of_entry)
    study_duration, study_period = STUDY_DURATIONS.get(
        key, ('___ лет ___ месяцев', 'с __.__.20__ по __.__.20__')
    )

    # --- Заказчик (родитель или сам абитуриент если нет родителя) ---
    zakazchik = dogovor.roditel_zakazchik
    customer_fio   = zakazchik.fio     if zakazchik else '____________'
    customer_addr  = zakazchik.address if zakazchik else abit.address
    customer_phone = zakazchik.phone   if zakazchik else abit.phone
    customer_email = zakazchik.email   if zakazchik else abit.email

    # --- Форма оплаты и первый платёж ---
    payment_form_label = PAYMENT_FORM_LABELS.get(dogovor.payment_form, dogovor.get_payment_form_display())
    first_sum = FIRST_PAYMENT.get(dogovor.payment_form, '___')

    context = {
        'dogovor_number':  dogovor.number,
        'currentdate':     dogovor.date_of_conclusion.strftime('%d.%m.%Y'),

        # Специальность и сроки — подставляются автоматически из карточки абитуриента
        'specialty_code':  specialty_code,
        'specialty_name':  specialty_name,
        'study_duration':  study_duration,
        'study_period':    study_period,

        # Обучающийся
        'listener':        abit.fio,
        'datebirth':       abit.date_of_birth.strftime('%d.%m.%Y'),

        # Заказчик
        'customer_fio':    customer_fio,
        'address':         customer_addr  or '____________',
        'mobphone':        customer_phone or '____________',
        'email':           customer_email or '____________',

        # Паспортные данные впишут вручную после печати
        'cpasport':        '________________',
        'cpassissued':     '________________',

        # Оплата
        'payment_form':    payment_form_label,
        'discount_sum':    '___',  # менеджер вписывает вручную
        'first_sum':       first_sum,
    }

    doc.render(context)

    filename = f'Dogovor_{dogovor.number}_{abit.fio.split()[0]}.docx'
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    doc.save(response)
    return response