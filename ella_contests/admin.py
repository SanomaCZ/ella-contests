from __future__ import unicode_literals

from datetime import datetime

from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.conf.urls import url
from django.utils.safestring import mark_safe
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

from ella.core.cache import cache_this, get_cached_object_or_404
from ella.core.admin import PublishableAdmin, ListingInlineAdmin, RelatedInlineAdmin

from ella_contests.models import Contestant, Answer, Choice, Contest, Question
from ella_contests.forms import ChoiceForm, ChoiceInlineFormset
from ella_contests.exporters import ExportDataContainer, export_to_csv, export_to_xls


class QuestionInlineAdmin(admin.TabularInline):
    model = Question
    raw_id_fields = ('photo',)
    extra = 1


class ChoiceInlineAdmin(admin.TabularInline):
    model = Choice
    extra = 1
    formset = ChoiceInlineFormset


class ContestAdmin(PublishableAdmin):
    ordering = ('-publish_from',)
    raw_id_fields = ('photo', 'source', 'authors')
    fieldsets = (
        (_("Article heading"), {'fields': ('title', 'slug')}),
        (_("Article contents"), {'fields': ('description', 'text', 'text_results', 'text_announcement')}),
        (_("Metadata"), {'fields': ('category', 'authors', 'source', 'photo')}),
        (_("Publication"), {'fields': (('publish_from', 'publish_to'), 'published', 'static')}),
        (_("Active"), {'fields': ('active_from', 'active_till')}),
    )
    list_display = PublishableAdmin.list_display + (
        'active_from', 'state',
        'questions_count', 'contestants_count',
        'contestants_correct_answers_count',
        'contestants_all_correct_answers_count',
        'results_export',
    )
    inlines = [ListingInlineAdmin, RelatedInlineAdmin, QuestionInlineAdmin]
    export_data_container_class = ExportDataContainer
    export_types = {
        'csv': (_('csv'), export_to_csv),
        'xls': (_('xls'), export_to_xls),
    }

    def contestants_count(self, obj):
        if obj.is_not_yet_active:
            return 0
        else:
            return obj.contestant_set.count()
    contestants_count.short_description = _('count of contestants')

    def questions_count(self, obj):
        return obj.questions_count
    questions_count.short_description = _('count of questions')

    @cache_this(lambda adm, c: "ella_contests_admin_all_correct_answers_count_%s" % c.pk,
                timeout=60 * 60)
    def contestants_all_correct_answers_count(self, obj):
        all_required_questions = obj.question_set.filter(is_required=True).count()
        return obj.get_contestants_with_correct_answer().filter(answers_count=all_required_questions).count()
    contestants_all_correct_answers_count.short_description = _('contestants (all correct answers)')

    @cache_this(lambda adm, c: "ella_contests_admin_correct_answers_count_%s" % c.pk,
                timeout=60 * 60)
    def contestants_correct_answers_count(self, obj):
        return obj.get_contestants_with_correct_answer().count()
    contestants_correct_answers_count.short_description = _('contestants (at least one correct answer)')

    def state(self, obj):
        if obj.is_not_yet_active:
            return "%s" % _('Is not yet active')
        elif obj.is_closed:
            return "%s" % _('Is closed')
        else:
            return "%s" % _('Is active now')
    state.short_description = _('State')

    def get_urls(self):
        urls = super(ContestAdmin, self).get_urls()
        extra_urls = [
            url(
                r'^(\d+)/results-export/all/$',
                self.admin_site.admin_view(self.results_export_view),
                name='ella-contests-contest-results-export'
            ),
            url(
                r'^(\d+)/results-export/all-correct/$',
                self.admin_site.admin_view(self.correct_results_export_view),
                name='ella-contests-contest-correct-results-export'
            )
        ]
        return extra_urls + urls

    def correct_results_export_view(self, *args, **kwargs):
        kwargs['all_correct'] = True
        return self.results_export_view(*args, **kwargs)

    def results_export_view(self, request, contest_pk, extra_context=None, all_correct=False):
        contest = get_cached_object_or_404(Contest, pk=contest_pk)
        return self.results_export_response(request, contest, all_correct=all_correct)

    def results_export_response(self, request, contest, all_correct=False):
        contest_slug = slugify(contest.title)
        file_name = "%s_%s" % (
            contest_slug[:50],
            datetime.now().strftime("%y_%m_%d_%H_%M")
        )

        if request.GET.get('type') not in self.export_types:
            self.message_user(request, _("Unknown format for export"), level=messages.WARNING)
            return HttpResponseRedirect(reverse("admin:ella_contests_contest_changelist"))

        export_name, export_func = self.export_types[request.GET.get('type')]

        try:
            response = export_func(contest, all_correct, file_name, data_container_class=self.export_data_container_class)
        except self.export_data_container_class.IncorrectHeadData:
            self.message_user(request, _("I can not export data becouse of any questions has not set choice as correct"), level=messages.WARNING)
            return HttpResponseRedirect(reverse("admin:ella_contests_contest_changelist"))

        return response

    def get_safe_url(self, obj, url_name, export_title, export_type):
        return mark_safe(
            """
                <a href='%(url)s?type=%(export_type)s'>%(export_title)s</a>
            """ % {
                'url': reverse('admin:%s' % url_name, args=(obj.id,)),
                'export_title': export_title,
                'export_type': export_type,
            }
        )

    def results_export(self, obj):
        def get_links(obj, url_name, export_types):
            return "".join([self.get_safe_url(obj, url_name, name_and_func[0], t) for t, name_and_func in export_types.items()])

        items = [
            "%s: %s" % (_('All'), get_links(obj, "ella-contests-contest-results-export", self.export_types)),
            "%s: %s" % (_('All correct answers'), get_links(obj, "ella-contests-contest-correct-results-export", self.export_types))
        ]
        return mark_safe("<br /><br />".join(items))
    results_export.allow_tags = True
    results_export.short_description = _('Results export')


class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'is_correct', 'inserted_by_user')
    list_filter = ('question__contest__title', 'is_correct', 'inserted_by_user')
    search_fields = ('question__contest__title', 'question__text',)
    raw_id_fields = ('question',)
    form = ChoiceForm


class QuestionAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'is_required', 'has_set_correct_choice')
    list_filter = ('contest__title', 'is_required',)
    search_fields = ('contest__title',)
    raw_id_fields = ('contest', 'photo',)
    inlines = [ChoiceInlineAdmin]

    def has_set_correct_choice(self, obj):
        if Choice.objects.filter(question=obj, is_correct=True).exists():
            return True
        else:
            return False
    has_set_correct_choice.short_description = _('Has set correct choice')
    has_set_correct_choice.boolean = True


class ContestantAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'email', 'created')
    list_filter = ('contest__title',)
    search_fields = ('contest__title',)
    raw_id_fields = ('contest', 'user',)


class AnswerAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'answer',)
    search_fields = ('contestant__name', 'contestant__surname',)
    raw_id_fields = ('contestant', 'choice',)


admin.site.register(Contest, ContestAdmin)
admin.site.register(Choice, ChoiceAdmin)
admin.site.register(Contestant, ContestantAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer, AnswerAdmin)
