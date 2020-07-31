from os import environ, path

from analyst.utils import get_config_from_env

BASE_DIR = path.dirname(path.dirname(path.abspath(__file__)))

FIXTURE_PATH = path.join(BASE_DIR, "tests", "fixtures")

SECRET_KEY = environ.get("DJANGO_SECRET_KEY")

DEBUG = environ.get("DEBUG") == "true"

ALLOWED_HOSTS = ["*"]

CORS_ORIGIN_ALLOW_ALL = True

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

if DEBUG:
    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": lambda x: True
    }

INTERNAL_IPS = ['127.0.0.1']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'debug_toolbar',
    'rest_framework',
    'analyst',
    'django_filters',
    'corsheaders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'analyst.urls'

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

REST_FRAMEWORK = {
    # 'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    # 'PAGE_SIZE': 100,
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.OrderingFilter',
        'rest_framework.filters.SearchFilter',
    ),
    'ORDERING_PARAM': 'pk'
}

WSGI_APPLICATION = 'analyst.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': environ.get("PGHOST"),
        'PORT': environ.get("PGPORT", 5432),
        'NAME': environ.get("PGDATABASE"),
        'USER': environ.get("PGUSER"),
        'PASSWORD': environ.get("PGPASSWORD"),
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            # 'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            # 'format': '{levelname} {message}',
            'format': '{levelname:8s} {asctime} {module} {message}',
            'style': '{',
        },
        'none': {
            # 'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            # 'format': '{levelname} {message}',
            'format': '{message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default'
        },
        'shell': {
            'class': 'logging.StreamHandler',
            'formatter': 'none'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'analyst': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'adapters': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'portfolio': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'analysis': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'portfolio.management.commands.scrap': {
            'handlers': ['shell'],
            'level': 'INFO',
            'propagate': False,
        }
    },
}

SCRAPPER_CONFIG = {
    "indice": {
        "include": {
            "name": [
                "SmallCap 2000",
            ],
            "country": [
                "France",
                # "United Kingdom",
                # "Germany",
                # "United States"
            ]
        },
        "exclude": {
            # "name": [
            #    "Nasdaq",
            #    "Dow 30",
            #    "S&P 500"
        }
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_ROOT = 'static'

STATIC_URL = '/static/'

ALPHA_VANTAGE_CONFIG = get_config_from_env("ALPHA_VANTAGE")

INFLUXDB_CONFIG = get_config_from_env("INFLUXDB")

INVESTING_CONFIG = get_config_from_env("INVESTING")

REDIS_CONFIG = get_config_from_env("REDIS")
