import csv
import itertools

from django.utils.functional import cached_property
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.utils.translation import ugettext_lazy as _

from .models import Choice
from .utils import encode_item


class IncorrectData(Exception):
    pass


class ExportDataContainer(object):
    IncorrectHeadData = IncorrectData

    def __init__(self, contest, all_correct=False, encode_item_func=None):
        self.contest = contest
        self.all_correct = all_correct
        self.encode_item_func = encode_item_func or self.blank_encode_item_func

    @cached_property
    def all_required_questions(self):
        return self.contest.question_set.filter(is_required=True).count()

    @cached_property
    def all_questions(self):
        return self.contest.questions

    def blank_encode_item_func(self, item):
        '''
        return item without changes
        '''
        return item

    def get_constant_head_data(self):
        data = [
            _('First name'),
            _('Last name'),
            _('email'),
            _('Phone number'),
            _('Address'),
            _('Created'),
            _('Count of right answers'),
            _('Count of all possible right answers'),
        ]
        return [self.encode_item_func(i) for i in data]

    def get_head_data(self):
        try:
            head = itertools.chain(
                self.get_constant_head_data(),
                [
                    self.encode_item_func("q %s (%s)" % (q.order, q.choice_set.get(is_correct=True).order))
                    for q in self.all_questions
                ]
            )
        except Choice.DoesNotExist:
            raise self.IncorrectData

        return head

    def get_constant_row_data(self, obj, right_answers_count):
        data = [
            obj.name,
            obj.surname,
            obj.email,
            obj.phone_number,
            obj.address,
            obj.created.strftime("%d.%m.%Y %H:%M:%S"),
            right_answers_count,
            self.all_required_questions,
        ]
        return [self.encode_item_func(i) for i in data]

    def get_row_data(self, obj, right_answers_count):
        answers_dict = dict([(a.choice.question_id, (a.answer, a.choice)) for a in obj.answer_set.all()])
        answers = []
        for q in self.all_questions:
            try:
                a, ch = answers_dict[q.pk]
            except KeyError:
                answers.append(self.encode_item_func(""))
            else:
                if ch.inserted_by_user:
                    answers.append(self.encode_item_func(a))
                else:
                    answers.append(self.encode_item_func(ch.order))

        return itertools.chain(self.get_constant_row_data(obj, right_answers_count), answers)

    def get_rows_data(self):
        for obj in self.contest.contestant_set.all():
            right_answers_count = obj.my_right_answers.count()
            if self.all_correct and right_answers_count != self.all_required_questions:
                continue
            yield self.get_row_data(obj, right_answers_count)


def export_to_csv(contest, all_correct, file_name, data_container_class=None):
    data_container_class = data_container_class or ExportDataContainer
    export_container = data_container_class(contest, all_correct, encode_item)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=%s.csv' % file_name

    writer = csv.writer(response)
    writer.writerow(list(export_container.get_head_data()))

    for row in export_container.get_rows_data():
        writer.writerow(list(row))

    return response


def export_to_xls(contest, all_correct, file_name, data_container_class=None, template_name=None, charset='utf-8'):
    template_name = template_name or 'admin/ella_contests/answers-excel.html'

    data_container_class = data_container_class or ExportDataContainer
    export_container = data_container_class(contest, all_correct, encode_item)

    context = {
        'head': export_container.get_head_data(),
        'rows': export_container.get_rows_data(),
    }

    response = render_to_response(
        template_name,
        context,
    )

    response['Content-Disposition'] = 'attachment; filename=%s.xls' % file_name
    response['Content-Type'] = 'application/vnd.ms-excel;charset=%s' % charset
    return response
