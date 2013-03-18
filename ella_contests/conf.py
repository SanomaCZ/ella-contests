from django.conf import settings
from ella.utils.settings import Settings


RENDER_CHOICES = True

AUTH_USER_MODEL = getattr(settings, "AUTH_USER_MODEL", "auth.User")

QUESTIONS_CACHE_KEY_PATTERN = 'ella_contests_contest_questions:%s'
CHOICES_CACHE_KEY_PATTERN = 'ella_contests_contest_choices:%s'

COOKIE_DOMAIN = settings.SESSION_COOKIE_DOMAIN
COOKIE_MAX_AGE = 86400 * 31

FORM_STEPS_STORAGE = 'ella_contests.storages.CookieStorage'

contests_settings = Settings('ella_contests.conf', 'CONTESTS')
