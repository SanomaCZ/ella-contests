from django.test import TestCase

from ella.utils.test_helpers import create_basic_categories
from ella.utils.timezone import now

from ella_contests.models import Question, Contest, Choice


class ContestTestCase(TestCase):
    def setUp(self):
        super(ContestTestCase, self).setUp()
        create_basic_categories(self)
        now_date = now()
        self.contest = Contest.objects.create(
                title=u'First Contest',
                slug=u'first-contest',
                description=u'First Contest',
                category=self.category_nested,
                publish_from=now_date,
                published=True,

                text=u'Some contest text. \n',
                text_results=u'Some contest result text. \n',
                active_from=now_date
        )
        self.questions = []
        for x in range(1, 4):
            q = Question.objects.create(
                contest=self.contest,
                order=x,
                text='question %d?' % x,
            )
            self.questions.append(q)
            for i in range(1, 4):
                Choice.objects.create(
                    question=q,
                    order=i,
                    choice='choice %d:%d?' % (x, i),
                    is_correct=True if i == 3 else False
                )
