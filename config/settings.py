"""Configuración del proyecto de demostración del módulo Terceros (AAMO).

Es un extracto mínimo: en AAMO real la base de datos es PostgreSQL (Supabase)
y las áreas se sirven por subdominio. Aquí se usa SQLite para que el módulo
pueda ejecutarse sin instalar nada más.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'clave-solo-para-desarrollo-local')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']

INSTALLED_APPS = [
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'terceros',
]

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.request',
        'django.contrib.messages.context_processors.messages',
    ]},
}]

# La conexión se define aquí (equivalente a la URL de conexión de JDBC).
# Para PostgreSQL basta cambiar ENGINE y los datos de acceso por variables de entorno.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_TZ = True
STATIC_URL = 'static/'
