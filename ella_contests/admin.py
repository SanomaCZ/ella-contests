from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from ella.core.admin import PublishableAdmin, ListingInlineAdmin, RelatedInlineAdmin

from ella_contests.models import Contestant, Answer, Choice, Contest, Question


class QuestionInlineAdmin(admin.TabularInline):
    model = Question
    raw_id_fields = ('photo',)
    extra = 1
    #fieldsets = ((None, {'fields': ('category', 'publish_from', 'publish_to', 'commercial',)}),)


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
    inlines = [ListingInlineAdmin, RelatedInlineAdmin, QuestionInlineAdmin]


admin.site.register(Contest, ContestAdmin)
admin.site.register(Choice)
admin.site.register(Contestant)
admin.site.register(Question)
admin.site.register(Answer)
