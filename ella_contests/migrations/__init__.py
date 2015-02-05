"""
Django migrations for ella_contests app
This package does not contain South migrations.  South migrations can be found
in the ``south_migrations`` package.
"""

SOUTH_ERROR_MESSAGE = """\n
For South support, customize the SOUTH_MIGRATION_MODULES setting like so (or use South >= 1.0):
    SOUTH_MIGRATION_MODULES = {
        'ella_contests': 'ella_contests.south_migrations',
    }
"""

try:
    from django.db import migrations
except ImportError:
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured(SOUTH_ERROR_MESSAGE)
