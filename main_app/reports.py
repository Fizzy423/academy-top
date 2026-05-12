# main_app/reports.py

import os
import pandas as pd  # Исправляем ошибку "pd не определено"
from django.conf import settings
from django.shortcuts import render  
from django.http import HttpResponse
from django.template.loader import get_template
from django.utils import timezone
from django.db.models import Count    
from xhtml2pdf import pisa
from io import BytesIO
from .models import Abiturient, Dogovor 
from django.contrib.staticfiles import finders
from django.conf import settings

# Импорты для прямой регистрации шрифтов
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

os.environ['TEMP'] = settings.TMP_DIR
os.environ['TMP'] = settings.TMP_DIR
os.environ['TMPDIR'] = settings.TMP_DIR

def register_fonts():
    """Регистрируем шрифты так, чтобы xhtml2pdf их точно увидел"""
    try:
        # Пытаемся найти файлы шрифтов
        regular_path = finders.find('fonts/DejaVuSans.ttf')
        bold_path = finders.find('fonts/DejaVuSans-Bold.ttf')
        
        if regular_path:
            # Важно: используем абсолютный путь и нормализуем его
            reg_path = os.path.abspath(regular_path)
            pdfmetrics.registerFont(TTFont('DejaVuSans', reg_path))
            print(f"--- ШРИФТ ЗАРЕГИСТРИРОВАН: {reg_path}")
            
        if bold_path:
            bold_path_abs = os.path.abspath(bold_path)
            pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', bold_path_abs))
    except Exception as e:
        print(f"--- Ошибка регистрации шрифтов: {e}")

# Запуск регистрации
register_fonts()

def link_callback(uri, rel):
    """
    Конвертирует относительные пути (static/media) в абсолютные пути на диске.
    """
    import os
    from django.conf import settings
    from django.contrib.staticfiles import finders

    # Если uri — это путь к статике (начинается с /static/)
    if uri.startswith(settings.STATIC_URL):
        path = uri.replace(settings.STATIC_URL, "")
        find_result = finders.find(path)
        if find_result:
            if isinstance(find_result, (list, tuple)):
                result = find_result[0]
            else:
                result = find_result
            return os.path.abspath(result)
            
    # Если uri — это медиа (картинки пользователя)
    elif uri.startswith(settings.MEDIA_URL):
        path = uri.replace(settings.MEDIA_URL, "")
        result = os.path.join(settings.MEDIA_ROOT, path)
        return os.path.abspath(result)

    return uri

def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    
    pdf = pisa.pisaDocument(
        BytesIO(html.encode("utf-8")), # Кодируем строку в байты utf-8
        result, 
        encoding='utf-8',              # Указываем генератору кодировку
        link_callback=link_callback
    )
    
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return HttpResponse(f"Ошибка: {pdf.err}", status=400)

def abiturient_report_pdf(request):
    abiturients = Abiturient.objects.select_related('specialnost').all()
    context = {
        'abiturients': abiturients,
        'total_count': abiturients.count(),
        'by_class': {
            '9': abiturients.filter(class_of_entry='9').count(),
            '11': abiturients.filter(class_of_entry='11').count(),
        },
        'generated_date': timezone.now(),
    }
    return render_to_pdf('main_app/reports/abiturient_report.html', context)

def dogovor_report_excel(request):
    """Отчет в Excel (тут была ошибка с pd)"""
    dogovors = Dogovor.objects.select_related('abiturient', 'roditel_zakazchik').all()
    data = []
    for d in dogovors:
        data.append({
            'Номер договора': d.number,
            'Дата заключения': d.date_of_conclusion,
            'Абитуриент': d.abiturient.fio if d.abiturient else '',
            'Форма оплаты': d.get_payment_form_display(),
            'Материнский капитал': 'Да' if d.maternity_capital else 'Нет',
            'Кредит': 'Да' if d.credit else 'Нет',
            'Родитель-заказчик': d.roditel_zakazchik.fio if d.roditel_zakazchik else '',
        })
    
    df = pd.DataFrame(data) 
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="dogovors_report.xlsx"'
    df.to_excel(response, index=False, sheet_name='Договоры')
    return response

def dashboard_report(request):
    context = {
        'total_abiturients': Abiturient.objects.count(),
        'total_students': Abiturient.objects.filter(status='student').count(),
        'total_dogovors': Dogovor.objects.count(),
        'by_specialnost': Abiturient.objects.values('specialnost__name').annotate(count=Count('id')),
        'by_payment_form': Dogovor.objects.values('payment_form').annotate(count=Count('id')),
        'monthly_stats': Dogovor.objects.filter(
            date_of_conclusion__year=timezone.now().year
        ).values('date_of_conclusion__month').annotate(count=Count('id')),
    }
    return render(request, 'main_app/reports/dashboard_report.html', context)