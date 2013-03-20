import csv
import itertools
from datetime import datetime

from django.contrib import admin
from django.http import HttpResponse
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _

from ella.core.cache import cache_this
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
    list_display = PublishableAdmin.list_display + (
                                                    'active_from', 'state',
                                                    'questions_count', 'contestants_count',
                                                    'contestants_correct_answers_count',
                                                    'contestants_all_correct_answers_count',
                                                    )
    inlines = [ListingInlineAdmin, RelatedInlineAdmin, QuestionInlineAdmin]
    actions = PublishableAdmin.actions + ['results_to_csv']

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
        all_required_questions = Question.objects.filter(contest=obj, is_required=True).count()
        return obj.get_contestants_with_correct_answer().filter(answers_count=all_required_questions).count()
    contestants_all_correct_answers_count.short_description = _('contestants (all correct answers)')

    @cache_this(lambda adm, c: "ella_contests_admin_correct_answers_count_%s" % c.pk,
                timeout=60 * 60)
    def contestants_correct_answers_count(self, obj):
        return obj.get_contestants_with_correct_answer().count()
    contestants_correct_answers_count.short_description = _('contestants (at least one correct answer)')

    def state(self, obj):
        if obj.is_not_yet_active:
            return u"%s" % _('Is not yet active')
        elif obj.is_closed:
            return u"%s" % _('Is closed')
        else:
            return u"%s" % _('Is active now')
    state.short_description = _('State')

    def results_to_csv(self, request, queryset):
        def encode_item(item):
            return unicode(item).encode("utf-8", "replace")

        if queryset.count() != 1:
            self.message_user(request, _("I can not return results for multiple contests at once"))
        else:
            obj = queryset[0]
            obj_slug = slugify(obj.title)
            qs = Contestant.objects.filter(contest=obj)
            response = HttpResponse(mimetype='text/csv')
            response['Content-Disposition'] = 'attachment; filename=%s_%s.csv' % (obj_slug[:50],
                                                                                  datetime.now().strftime("%y_%m_%d_%H_%M"))
            all_required_questions = Question.objects.filter(contest=obj, is_required=True).count()
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
            all_questions = obj.questions
            head = itertools.chain(head, [encode_item("q %s (%s)" % (q.order, q.choice_set.get(is_correct=True).order)) for q in all_questions])
            writer.writerow(list(head))
            for obj in qs:
                row = [
                       encode_item(obj.name),
                       encode_item(obj.surname),
                       encode_item(obj.email),
                       encode_item(obj.phone_number),
                       encode_item(obj.address),
                       encode_item(obj.created),
                       encode_item(obj.my_right_answers.count()),
                       encode_item(all_required_questions),
                       ]
                answers_dict = dict([(a.choice.question_id, (a.answer, a.choice)) for a in obj.answer_set.all()])
                answers = []
                for q in all_questions:
                    try:
                        a, ch = answers_dict[q.pk]
                    except KeyError:
                        answers.append(encode_item(u""))
                    else:
                        if ch.inserted_by_user:
                            answers.append(encode_item(a))
                        else:
                            answers.append(encode_item(ch.order))
                row = itertools.chain(row, answers)
                writer.writerow(list(row))
            return response
    results_to_csv.short_description = _("Results")


class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'is_correct', 'inserted_by_user')
    list_filter = ('question__contest__title', 'is_correct', 'inserted_by_user')
    search_fields = ('question__contest__title', 'question__text',)
    raw_id_fields = ('question',)


class QuestionAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'is_required', 'has_set_correct_choice')
    list_filter = ('contest__title', 'is_required',)
    search_fields = ('contest__title',)
    raw_id_fields = ('contest', 'photo',)

    def has_set_correct_choice(self, obj):
        if Choice.objects.filter(question=obj, is_correct=True).exists():
            return u"%s" % _('Yes')
        else:
            return u"%s" % _('No')
    has_set_correct_choice.short_description = _('Has set correct choice')


class ContestantAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'email', 'created', 'count_guess')
    list_filter = ('contest__title',)
    search_fields = ('contest__title',)
    raw_id_fields = ('contest', 'user',)


class AnswerAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'answer',)
    search_fields = ('contestant__name', 'contestant__surname',)
    raw_id_fields = ('contestant', 'choice',)


admin.site.register(Contest, ContestAdmin)
admin.site.register(Choice, ChoiceAdmin)
admin.site.register(Contestant, ContestantAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer, AnswerAdmin)
