from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from ella.core.admin import PublishableAdmin, ListingInlineAdmin, RelatedInlineAdmin

from ella_contests.models import Contestant, Answer, Choice, Contest, Question


class QuestionInlineAdmin(admin.TabularInline):
    model = Question
    raw_id_fields = ('photo',)
    extra = 1


class ContestAdmin(PublishableAdmin):
    ordering = ('-publish_from',)
    raw_id_fields = ('photo', 'source', 'authors')
    fieldsets = (
        (_("Article heading"), {'fields': ('title', 'slug')}),
        (_("Article contents"), {'fields': ('description', 'text', 'text_results')}),
        (_("Metadata"), {'fields': ('category', 'authors', 'source', 'photo')}),
        (_("Publication"), {'fields': (('publish_from', 'publish_to'), 'published', 'static')}),
        (_("Active"), {'fields': ('active_from', 'active_till')}),
    )
    list_display = PublishableAdmin.list_display + ('active_from', 'state', 'contestants_count',)
    inlines = [ListingInlineAdmin, RelatedInlineAdmin, QuestionInlineAdmin]

    def contestants_count(self, obj):
        if obj.is_not_yet_active:
            return 0
        else:
            return obj.contestant_set.count()
    contestants_count.short_description = _('count of contestants')

    def state(self, obj):
        if obj.is_not_yet_active:
            return u"%s" % _('Is not yet active')
        elif obj.is_closed:
            return u"%s" % _('Is closed')
        else:
            return u"%s" % _('Is active now')
    state.short_description = _('State')


admin.site.register(Contest, ContestAdmin)
admin.site.register(Choice)
admin.site.register(Contestant)
admin.site.register(Question)
admin.site.register(Answer)
