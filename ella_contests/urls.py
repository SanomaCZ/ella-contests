from django.conf.urls.defaults import patterns, url
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _

from ella_contests.views import (
                                 contest_result,
                                 contest_conditions,
                                 contest_contestant,
                                 contest_detail,
                                 )


urlpatterns = patterns('',
    url('^%s/$' % slugify(_('contestant')), contest_contestant, name='ella-contests-contests-contestant'),
    url('^%s/$' % slugify(_('result')), contest_result, name='ella-contests-contests-result'),
    url('^%s/$' % slugify(_('conditions')), contest_conditions, name='ella-contests-contests-conditions'),
    url(r'^%s/(?P<question_number>\d+)$' % slugify(_('question')), contest_detail, name='ella-contests-contests-detail')
)
