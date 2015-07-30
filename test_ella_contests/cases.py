from datetime import timedelta

from django.utils.timezone import now
from django.test import TestCase

from ella.utils.test_helpers import create_basic_categories

from ella_contests.models import Question, Contest, Choice


def create_obj(model, data, default_data=None):
    default_data = default_data or {}
    final_data = default_data.copy()
    final_data.update(data)
    obj = model.objects.create(**final_data)
    return obj


def create_question(test_case, data=None, default_data=None, q_ind=1):
    data = data or {}
    default_data = default_data or dict(
        contest=test_case.contest,
        order=1,
        text='question %d?' % q_ind,
        is_required=True
    )
    return create_obj(Question, data, default_data)


def create_choice(test_case, data=None, default_data=None, q_ind=1, ch_ind=1):
    data = data or {}
    default_data = default_data or dict(
        order=1,
        choice='choice %d:%d?' % (q_ind, ch_ind),
        is_correct=False,
        inserted_by_user=False
    )
    return create_obj(Choice, data, default_data)


class ContestTestCase(TestCase):

    def create_contest(self, title, slug, **kwargs):
        now_date = now()
        defaults = dict(
            description=u'First Contest',
            category=self.category_nested,
            publish_from=now_date,
            published=True,

            text=u'Some contest text. \n',
            text_results=u'Some contest result text. \n',
            active_from=now_date,
            active_till=now_date + timedelta(days=30)
        )
        lookup = defaults.copy()
        lookup.update({'title': title, 'slug': slug})
        lookup.update(kwargs)
        return Contest.objects.create(**lookup)

    def setUp(self):
        super(ContestTestCase, self).setUp()
        create_basic_categories(self)

        self.contest = self.create_contest(
            title=u'First Contest',
            slug=u'first-contest'
        )
        self.contest_question_less = self.create_contest(
            title=u'Second Contest',
            slug=u'second-contest'
        )
        self.questions = []
        self.choices = []
        for x in range(1, 4):
            q = create_question(
                self,
                data=dict(
                    order=x,
                    is_required=False if x == 3 else True
                ),
                q_ind=x
            )
            self.questions.append(q)
            for i in range(1, 4):
                c = create_choice(
                    self,
                    data=dict(
                        question=q,
                        order=i,
                        is_correct=True if i == 3 else False,
                        inserted_by_user=True if x == 2 and i == 3 else False
                    ),
                    q_ind=x,
                    ch_ind=i
                )
                self.choices.append(c)
