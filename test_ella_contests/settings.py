from os.path import join, dirname, abspath

DEBUG = True
TEMPLATE_DEBUG = DEBUG
PROJECT_ROOT = abspath(dirname(__file__))

ROOT_URLCONF = 'test_ella_contests.urls'
STATIC_URL = '/static/'
MEDIA_URL = '/media/'


TEMPLATE_CONTEXT_PROCESSORS = (
    'django.template.context_processors.debug',
    'django.template.context_processors.media',
    'django.template.context_processors.static',
    'django.contrib.auth.context_processors.auth',
)

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    join(PROJECT_ROOT, 'templates'),
)

TEMPLATE_OPTIONS = {
    'context_processors': TEMPLATE_CONTEXT_PROCESSORS,
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # 'APP_DIRS': True,
        'DIRS': TEMPLATE_DIRS,
        'OPTIONS': TEMPLATE_OPTIONS
    },
]

SECRET_KEY = 'very-secret'

SITE_ID = 1

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.redirects',
    'django.contrib.admin',

    'ella.core',
    'ella.photos',
    'ella.articles',

    'ella_contests',
)

TEST_RUNNER = 'django.test.runner.DiscoverRunner'
