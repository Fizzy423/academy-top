import os
from django.core.exceptions import ValidationError

def validate_file_extension(value):
    """Проверяет, что расширение файла входит в список разрешенных"""
    ext = os.path.splitext(value.name)[1]  
    valid_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.png', '.jpeg']
    if not ext.lower() in valid_extensions:
        raise ValidationError(f'❌ Недопустимый тип файла. Разрешены только: {", ".join(valid_extensions)}')

def validate_file_size(value):
    """Ограничивает размер файла до 5 МБ"""
    limit = 5 * 1024 * 1024 
    if value.size > limit:
        raise ValidationError('❌ Файл слишком большой. Максимальный размер — 5 МБ.')