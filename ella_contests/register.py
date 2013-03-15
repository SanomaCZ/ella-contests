from ella.core.custom_urls import resolver

from ella_contests.urls import urlpatterns
from ella_contests.views import contest_detail
from ella_contests.models import Contest


# register custom url patterns
resolver.register(urlpatterns, model=Contest)
#resolver.register_custom_detail(Contest, contest_detail)
