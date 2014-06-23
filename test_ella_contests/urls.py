from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import admin

try:
    from django.conf.urls import patterns, url, include
except ImportError:  # Django < 1.4
    from django.conf.urls.defaults import patterns, url, include

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^', include('ella.core.urls')),
) + staticfiles_urlpatterns()
