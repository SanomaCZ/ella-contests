from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _

from ella.core.custom_urls import resolver

from ella_contests.urls import urlpatterns
from ella_contests.models import Contest


# register custom url patterns
#resolver.register(urlpatterns, prefix=slugify(_('results')), model=Contest)
