from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-your-secret-key-here'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_spectacular',
    'api',
    'ml',
    'models',
    'middleware',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'middleware.exception_middleware.ExceptionMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'core.wsgi.application'

# Simplified database configuration using SQLite
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'mcs09'),
        'USER': os.environ.get('USER'),
        'PASSWORD': os.environ.get('PASS'),
        'HOST': os.environ.get('ENDPOINT'),
        'PORT': '3306',
    }
}

# Model directory
MODEL_DIR = os.path.join(BASE_DIR, 'models')

# Rest Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # Optional for browsable API
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
        'rest_framework.permissions.AllowAny'
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
    ],
        'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '20/minute',  # Limit anonymous users
        'user': '100/minute',  # Limit authenticated users
        'login': '5/minute',  # Custom throttle for login attempts
    },
    # Add this for Swagger
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# Spectacular settings for Swagger
SPECTACULAR_SETTINGS = {
    'TITLE': 'Django SHAP API',
    'DESCRIPTION': 'API for making predictions and getting SHAP explanations',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'CONTACT': {'name': 'krooldonutz'},
    'CREATED': '2025-03-03',
}

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'level': 'WARNING',  # Only warnings and above for console
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',  # Use rotating file handler
            'filename': 'django-debug.log',
            'formatter': 'verbose',
            'level': 'INFO',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 3,      # Keep 3 backup files
        },
    },
    'loggers': {
        '': {  # Root logger
            'handlers': ['console', 'file'],
            'level': 'WARNING',  # Higher level for root logger
            'propagate': True,
        },
        'django': {  # Django logger
            'handlers': ['file'],
            'level': 'WARNING',  # Only warnings and above
            'propagate': False,
        },
        'django.request': {  # Request logger for errors
            'handlers': ['console', 'file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'your_app_name': {  # Your specific app logs
            'handlers': ['console', 'file'],
            'level': 'INFO',  # More detailed for your app specifically
            'propagate': False,
        },
    },
}
AUTH_USER_MODEL = 'models.User'