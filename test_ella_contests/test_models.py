from datetime import datetime, timedelta
from nose import tools
from mock import patch

from django.core.exceptions import ValidationError
from django.db import IntegrityError

from .cases import ContestTestCase

from ella_contests.models import Question, Contestant, Answer


class MockedDatetime(datetime):
    pass


class TestContest(ContestTestCase):
    def setUp(self):
        super(TestContest, self).setUp()

    def test_questions_count(self):
        tools.assert_equals(self.contest.questions_count, 3)

    def test_questions_list(self):
        tools.assert_equals(self.contest.questions, self.questions)
        tools.assert_equals(self.contest.questions[0], self.questions[0])
        tools.assert_equals(self.contest.questions[1], self.questions[1])
        tools.assert_equals(self.contest.questions[2], self.questions[2])

    @patch('django.utils.timezone.datetime')
    def test_contest_time_states(self, mock_datetime):
        mock_datetime.now = lambda: datetime.now()
        tools.assert_equals(self.contest.is_active, True)
        tools.assert_equals(self.contest.is_closed, False)
        tools.assert_equals(self.contest.is_not_yet_active, False)
        tools.assert_equals(self.contest.content, self.contest.text)

        mock_datetime.now = lambda: datetime.now() - timedelta(days=1)
        tools.assert_equals(self.contest.is_active, False)
        tools.assert_equals(self.contest.is_closed, False)
        tools.assert_equals(self.contest.is_not_yet_active, True)
        tools.assert_equals(self.contest.content, self.contest.text)

        mock_datetime.now = lambda: datetime.now() + timedelta(days=30)
        tools.assert_equals(self.contest.is_active, False)
        tools.assert_equals(self.contest.is_closed, True)
        tools.assert_equals(self.contest.is_not_yet_active, False)
        tools.assert_equals(self.contest.content, self.contest.text_results)

    def test_contest_right_choices(self):
        tools.assert_equals(len(self.contest.right_choices), 2)
        tools.assert_equals(list(self.contest.right_choices), [self.choices[2], self.choices[5]])


class TestQuestion(ContestTestCase):
    def setUp(self):
        super(TestQuestion, self).setUp()
        self.question = Question.objects.get(order=1)

    def test_choices_count(self):
        tools.assert_equals(len(self.question.choices), 3)

    def test_choices_list(self):
        tools.assert_equals(self.question.choices, self.choices[:3])

    def test_get_absolute_url(self):
        tools.assert_equals(self.question.get_absolute_url(), self.contest.get_absolute_url() + 'question/1/')

    def test_previous_questions(self):
        tools.assert_equals(self.question.prev, None)
        tools.assert_equals(self.questions[1].prev, self.question)
        tools.assert_equals(self.questions[2].prev, self.questions[1])

    def test_next_questions(self):
        tools.assert_equals(self.question.next, self.questions[1])
        tools.assert_equals(self.questions[1].next, self.questions[2])
        tools.assert_equals(self.questions[2].next, None)

    def test_question_position(self):
        tools.assert_equals(self.question.position, 1)
        tools.assert_equals(self.questions[1].position, 2)
        tools.assert_equals(self.questions[2].position, 3)

    def test_save_method_unique_order_question_per_contest(self):
        self.question.order = 2
        tools.assert_raises(IntegrityError, self.question.save)


class TestChoice(ContestTestCase):
    def setUp(self):
        super(TestChoice, self).setUp()
        self.choice = self.choices[1]

    def test_clean_method_unique_correct_choice_per_question(self):
        self.choices[2].is_correct = True
        tools.assert_equals(self.choice.clean(), None)
        self.choice.is_correct = True
        tools.assert_raises(ValidationError, self.choice.clean)

    def test_save_method_unique_correct_choice_per_question(self):
        self.choice.is_correct = True
        tools.assert_raises(IntegrityError, self.choice.save)

    def test_save_method_unique_order_choice_per_question(self):
        self.choice.order = 1
        tools.assert_raises(IntegrityError, self.choice.save)


class TestContestant(ContestTestCase):

    def setUp(self):
        super(TestContestant, self).setUp()
        self.contestant = Contestant.objects.create(
            contest=self.contest,
            name=u'Joe',
            surname=u'Good',
            email=u'joe@joe.cz',
            phone_number='777777777',
            address=u'XX street 123'
        )
        self.contestant2 = Contestant.objects.create(
            contest=self.contest,
            name=u'Mike',
            surname=u'Good',
            email=u'mike@mike.cz',
            phone_number='777777555',
            address=u'YY street 321'
        )
        self.answers = [
            Answer.objects.create(contestant=self.contestant, choice=self.choices[2]),
            Answer.objects.create(contestant=self.contestant, choice=self.choices[5], answer=u"hi"),
            Answer.objects.create(contestant=self.contestant, choice=self.choices[8]),

            Answer.objects.create(contestant=self.contestant2, choice=self.choices[1]),
            Answer.objects.create(contestant=self.contestant2, choice=self.choices[6]),
            Answer.objects.create(contestant=self.contestant2, choice=self.choices[7]),
        ]

    def test_contest_right_answers(self):
        tools.assert_equals(self.contest.right_answers.count(), 2)
        tools.assert_equals(list(self.contest.right_answers), self.answers[:2])
        self.answers[3].choice = self.choices[2]
        self.answers[3].save()
        tools.assert_equals(self.contest.right_answers.count(), 3)
        tools.assert_equals(set(self.contest.right_answers), set(self.answers[:2] + [self.answers[3]]))

    def test_contestants_with_at_least_one_correct_answer(self):
        tools.assert_equals(self.contest.get_contestants_with_correct_answer().count(), 1)
        self.answers[3].choice = self.choices[2]
        self.answers[3].save()
        tools.assert_equals(self.contest.get_contestants_with_correct_answer().count(), 2)

    def test_contestant_right_answers(self):
        tools.assert_equals(self.contestant.my_right_answers.count(), 2)
        tools.assert_equals(self.contestant2.my_right_answers.count(), 0)

    def test_contestant_text_answers(self):
        tools.assert_equals(self.contestant.get_my_text_answers().count(), 1)
        tools.assert_equals(self.contestant2.get_my_text_answers().count(), 0)

    def test_save_method_unique_email_per_contest(self):
        self.contestant2.email = self.contestant.email
        tools.assert_raises(IntegrityError, self.contestant2.save)
