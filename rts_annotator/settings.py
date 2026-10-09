from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
import os

import parameters
setting_file = os.path.join(BASE_DIR,'setting.ini')

SECRET_KEY = parameters.get_string_parameters(setting_file,'secret_key')
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = parameters.get_bool_parameters(setting_file,'DEBUG')

host_name = parameters.get_string_parameters(setting_file,'host_name')
ALLOWED_HOSTS = ['127.0.0.1',
                 'localhost',
                 '192.168.23.56',
                 host_name]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'annotator',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'rts_annotator.urls'

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

WSGI_APPLICATION = 'rts_annotator.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 数据集路径（geo_meta.json / pixel_polygons.json / {year}_label.png 都已统一放在这里的各cell文件夹下）
# DATA_ROOT = '/hdd10Tb/chenyf/super-data'
DATA_ROOT = os.path.expanduser(parameters.get_string_parameters(setting_file,'DATA_ROOT'))

# 登录配置
LOGIN_URL = '/login/'
ALLOWED_EMAILS_FILE = BASE_DIR / 'allowed_emails.json'

# SAM2 模型路径
# SAM2_CHECKPOINT = '/hdd10Tb/chenyf/sam2_checkpoints/sam2.1_hiera_large.pt'
# SAM2_CONFIG = 'configs/sam2.1/sam2.1_hiera_l.yaml'
SAM2_CHECKPOINT = os.path.expanduser(parameters.get_string_parameters(setting_file,'SAM2_CHECKPOINT'))
# SAM2_CONFIG = os.path.expanduser(parameters.get_string_parameters(setting_file,'SAM2_CONFIG'))
SAM2_CONFIG = parameters.get_string_parameters(setting_file,'SAM2_CONFIG')
