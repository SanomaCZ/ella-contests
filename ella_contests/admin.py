from __future__ import unicode_literals

import csv
import itertools
from datetime import datetime

from django.contrib import admin
from django.http import HttpResponse
from django.conf.urls import patterns, url
from django.utils.safestring import mark_safe
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

from ella.core.cache import cache_this, get_cached_object_or_404
from ella.core.admin import PublishableAdmin, ListingInlineAdmin, RelatedInlineAdmin

from ella_contests.utils import encode_item
from ella_contests.models import Contestant, Answer, Choice, Contest, Question
from ella_contests.forms import ChoiceForm, ChoiceInlineFormset


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
    actions = PublishableAdmin.actions + ['results_to_csv_action']

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
        extra_urls = patterns(
            '',
            url(
                r'^(\d+)/results-export/$',
                self.admin_site.admin_view(self.results_export_view),
                name='ella-contests-contest-results-export'
            ),
        )
        return extra_urls + urls

    def results_export_view(self, request, contest_pk, extra_context=None):
        contest = get_cached_object_or_404(Contest, pk=contest_pk)
        return self.results_to_csv(request, contest)

    def results_to_csv(self, request, contest):
        contest_slug = slugify(contest.title)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=%s_%s.csv' % (
            contest_slug[:50],
            datetime.now().strftime("%y_%m_%d_%H_%M")
        )
        all_required_questions = contest.question_set.filter(is_required=True).count()
        writer = csv.writer(response)
        head = [
            encode_item(_('First name')),
            encode_item(_('Last name')),
            encode_item(_('email')),
            encode_item(_('Phone number')),
            encode_item(_('Address')),
            encode_item(_('Created')),
            encode_item(_('Count of right answers')),
            encode_item(_('Count of all possible right answers')),
        ]
        all_questions = contest.questions
        try:
            head = itertools.chain(head, [encode_item("q %s (%s)" % (q.order, q.choice_set.get(is_correct=True).order)) for q in all_questions])
        except Choice.DoesNotExist:
            self.message_user(request, _("I can not export data becouse of any questions has not set choice as correct"))
        else:
            writer.writerow(list(head))
            for obj in contest.contestant_set.all():
                row = [
                    encode_item(obj.name),
                    encode_item(obj.surname),
                    encode_item(obj.email),
                    encode_item(obj.phone_number),
                    encode_item(obj.address),
                    encode_item(obj.created.strftime("%d.%m.%Y %H:%M:%S")),
                    encode_item(obj.my_right_answers.count()),
                    encode_item(all_required_questions),
                ]
                answers_dict = dict([(a.choice.question_id, (a.answer, a.choice)) for a in obj.answer_set.all()])
                answers = []
                for q in all_questions:
                    try:
                        a, ch = answers_dict[q.pk]
                    except KeyError:
                        answers.append(encode_item(""))
                    else:
                        if ch.inserted_by_user:
                            answers.append(encode_item(a))
                        else:
                            answers.append(encode_item(ch.order))
                row = itertools.chain(row, answers)
                writer.writerow(list(row))
            return response

    def results_to_csv_action(self, request, queryset):

        if queryset.count() != 1:
            self.message_user(request, _("I can not return results for multiple contests at once"))
        else:
            return self.results_to_csv(request, queryset[0])

    results_to_csv_action.short_description = _("Results")

    def results_export(self, obj):
        return mark_safe(
            """
                <a href='%(url)s'>%(csv)s</a>
            """ % {
                'url': reverse('admin:ella-contests-contest-results-export', args=(obj.id,)),
                'csv': _('csv'),
            }
        )
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
