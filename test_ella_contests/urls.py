from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import admin
from django.conf.urls import url, include

from ella.utils.installedapps import call_modules

call_modules(auto_discover=('register', 'admin',))

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^', include('ella.core.urls')),
] + staticfiles_urlpatterns()
