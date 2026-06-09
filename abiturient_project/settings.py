import os
from pathlib import Path
from dotenv import load_dotenv  

# --- 0. ЗАГРУЗКА ОКРУЖЕНИЯ ---
load_dotenv()

# Путь к проекту
BASE_DIR = Path(__file__).resolve().parent.parent

# --- 1. ОСНОВНЫЕ НАСТРОЙКИ БЕЗОПАСНОСТИ ---
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-local-dev-key-you-should-change-it'
    else:
        raise ValueError("DJANGO_SECRET_KEY must be set in production!")

# Чтение хостов из окружения
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')

# Автоматически добавляем локальные хосты и адреса туннеля для удобства тестирования
if '*' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.extend([
        'localhost', 
        '127.0.0.1', 
        '.xtunnel.ru', 
        '.tunnel4.com',
        '.fxtun.ru'
    ])

# Доверенные источники для работы CSRF (необходимо для отправки форм и входа через xTunnel)
CSRF_TRUSTED_ORIGINS = [
    'https://*.xtunnel.ru',
    'https://*.fxtun.ru',
    'https://*.tunnel4.com',  
    'http://localhost:5031',
    'http://127.0.0.1:5031',
]

# --- 2. ПРИЛОЖЕНИЯ ---
INSTALLED_APPS = [
    'dal',            
    'dal_select2',     
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Сторонние библиотеки
    'crispy_forms',
    'crispy_bootstrap5',
    'django_filters',
    'guardian',
    'widget_tweaks',

    'main_app',
]

# --- 3. MIDDLEWARE ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'abiturient_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'abiturient_project.wsgi.application'

# --- 4. БАЗА ДАННЫХ (PostgreSQL) ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),  
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'client_encoding': 'UTF8',
        }
    }
}

# --- 5. ПАРОЛИ И АВТОРИЗАЦИЯ ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
)

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

# --- 6. ЛОКАЛИЗАЦИЯ ---
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# --- 7. СТАТИКА И МЕДИА ---
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760 

# --- 8. НАСТРОЙКИ БЕЗОПАСНОСТИ ДЛЯ ПРОДАКШЕНА ---
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    X_FRAME_OPTIONS = 'DENY'
    
    # Позволяет Django корректно определять HTTPS-протокол за прокси-сервером туннеля
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# --- 9. ДОПОЛНИТЕЛЬНО ---
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- 10. ВРЕМЕННЫЕ ДИРЕКТОРИИ ---
TMP_DIR = str(BASE_DIR / 'tmp')
if not os.path.exists(TMP_DIR):
    os.makedirs(TMP_DIR)