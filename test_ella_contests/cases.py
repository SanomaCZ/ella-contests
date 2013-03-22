from datetime import datetime, timedelta
from django.test import TestCase

from ella.utils.test_helpers import create_basic_categories

from ella_contests.models import Question, Contest, Choice


class ContestTestCase(TestCase):
    def setUp(self):
        super(ContestTestCase, self).setUp()
        create_basic_categories(self)
        now_date = datetime.now()
        self.contest = Contest.objects.create(
                title=u'First Contest',
                slug=u'first-contest',
                description=u'First Contest',
                category=self.category_nested,
                publish_from=now_date,
                published=True,

                text=u'Some contest text. \n',
                text_results=u'Some contest result text. \n',
                active_from=now_date,
                active_till=now_date + timedelta(days=30)
        )
        self.questions = []
        self.choices = []
        for x in range(1, 4):
            q = Question.objects.create(
                contest=self.contest,
                order=x,
                text='question %d?' % x,
                is_required=False if x == 3 else True
            )
            self.questions.append(q)
            for i in range(1, 4):
                c = Choice.objects.create(
                    question=q,
                    order=i,
                    choice='choice %d:%d?' % (x, i),
                    is_correct=True if i == 3 else False,
                    inserted_by_user=True if x == 2 and i == 3 else False
                )
                self.choices.append(c)
