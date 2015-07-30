from nose import tools

from django.forms.models import inlineformset_factory

from .cases import ContestTestCase, create_question, create_choice

from ella_contests.models import Choice, Question
from ella_contests.forms import ChoiceForm, ChoiceInlineFormset


class TestChiceForms(ContestTestCase):
    def setUp(self):
        super(TestChiceForms, self).setUp()

    def test_creation_success_for_choice_set_not_correct(self):
        question = self.questions[0]
        data = {
            'question': question.pk,
            'choice': 'kolo',
            'is_correct': False,
            'order': 4
        }
        f = ChoiceForm(data)
        tools.assert_true(f.is_valid())
        tools.assert_equals(Choice.objects.filter(question=question).count(), 3)
        f.save()
        tools.assert_equals(Choice.objects.filter(question=question).count(), 4)

    def test_form_invalid_if_correct_choice_already_exists(self):
        question = self.questions[0]
        data = {
            'question': question.pk,
            'choice': 'kolo',
            'is_correct': True,
            'order': 4
        }
        f = ChoiceForm(data)
        tools.assert_false(f.is_valid())
        tools.assert_in('__all__', f.errors)

    def test_creation_success_if_correct_choice_does_not_exist(self):
        question = create_question(
            self,
            data=dict(
                order=4,
            ),
            q_ind=4
        )
        create_choice(
            self,
            data=dict(
                question=question,
                order=1,
                is_correct=False,
            ),
            q_ind=4,
        )
        data = {
            'question': question.pk,
            'choice': 'kolo',
            'is_correct': True,
            'order': 2
        }
        f = ChoiceForm(data)
        tools.assert_true(f.is_valid())
        tools.assert_equals(Choice.objects.filter(question=question).count(), 1)
        f.save()
        tools.assert_equals(Choice.objects.filter(question=question).count(), 2)

    def test_update_text_success_for_correct_choice(self):
        question = self.questions[0]
        choice = question.choice_set.get(is_correct=True)
        data = {
            'question': choice.question_id,
            'choice': '%s-hi' % choice.choice,
            'is_correct': choice.is_correct,
            'order': choice.order
        }
        f = ChoiceForm(data, instance=choice)
        tools.assert_true(f.is_valid())
        tools.assert_equals(Choice.objects.filter(question=question).count(), 3)
        f.save()
        tools.assert_equals(Choice.objects.filter(question=question).count(), 3)
        tools.assert_equals(Choice.objects.filter(question=question, is_correct=True).count(), 1)

    def test_update_is_correct_success_for_correct_choice(self):
        question = self.questions[0]
        choice = question.choice_set.get(is_correct=True)
        data = {
            'question': choice.question_id,
            'choice': choice.choice,
            'is_correct': not choice.is_correct,
            'order': choice.order
        }
        f = ChoiceForm(data, instance=choice)
        tools.assert_true(f.is_valid())
        tools.assert_equals(Choice.objects.filter(question=question).count(), 3)
        f.save()
        tools.assert_equals(Choice.objects.filter(question=question).count(), 3)
        tools.assert_equals(Choice.objects.filter(question=question, is_correct=True).count(), 0)

    def test_update_is_correct_failed_for_incorrect_choice(self):
        question = self.questions[0]
        choice = question.choice_set.exclude(is_correct=True)[0]
        data = {
            'question': choice.question_id,
            'choice': choice.choice,
            'is_correct': not choice.is_correct,
            'order': choice.order
        }
        f = ChoiceForm(data, instance=choice)
        tools.assert_false(f.is_valid())
        tools.assert_in('__all__', f.errors)
        tools.assert_equals(Choice.objects.filter(question=question).count(), 3)


class TestChiceFormSet(ContestTestCase):
    def setUp(self):
        super(TestChiceFormSet, self).setUp()
        self.formset = inlineformset_factory(Question, Choice, fields='__all__', formset=ChoiceInlineFormset)

    def test_creation_success_for_one_correct_choice(self):
        question = create_question(
            self,
            data=dict(
                order=4,
            ),
            q_ind=4
        )
        data = {
            'choice_set-TOTAL_FORMS': 3,
            'choice_set-INITIAL_FORMS': 0,
            'choice_set-0-question': question.pk,
            'choice_set-0-choice': 'kolo 1',
            'choice_set-0-is_correct': False,
            'choice_set-0-order': 1,
            'choice_set-1-question': question.pk,
            'choice_set-1-choice': 'kolo 2',
            'choice_set-1-is_correct': True,
            'choice_set-1-order': 2,
            'choice_set-2-question': question.pk,
            'choice_set-2-choice': 'kolo 3',
            'choice_set-2-is_correct': False,
            'choice_set-2-order': 3,
        }
        f = self.formset(data, instance=question)
        tools.assert_true(f.is_valid())
        tools.assert_equals(Choice.objects.filter(question=question).count(), 0)
        f.save()
        tools.assert_equals(Choice.objects.filter(question=question).count(), 3)
        tools.assert_equals(Choice.objects.filter(question=question, is_correct=True).count(), 1)

    def test_formset_invalid_if_more_correct_choices(self):
        question = create_question(
            self,
            data=dict(
                order=4,
            ),
            q_ind=4
        )
        data = {
            'choice_set-TOTAL_FORMS': 3,
            'choice_set-INITIAL_FORMS': 0,
            'choice_set-0-question': question.pk,
            'choice_set-0-choice': 'kolo 1',
            'choice_set-0-is_correct': True,
            'choice_set-0-order': 1,
            'choice_set-1-question': question.pk,
            'choice_set-1-choice': 'kolo 2',
            'choice_set-1-is_correct': True,
            'choice_set-1-order': 2,
            'choice_set-2-question': question.pk,
            'choice_set-2-choice': 'kolo 3',
            'choice_set-2-is_correct': False,
            'choice_set-2-order': 3,
        }
        f = self.formset(data, instance=question)
        tools.assert_false(f.is_valid())
        tools.assert_in(unicode('You must specify one correct choice per question'), f.non_form_errors())
        tools.assert_equals(Choice.objects.filter(question=question).count(), 0)

    def test_formset_invalid_if_no_correct_choice(self):
        question = create_question(
            self,
            data=dict(
                order=4,
            ),
            q_ind=4
        )
        data = {
            'choice_set-TOTAL_FORMS': 3,
            'choice_set-INITIAL_FORMS': 0,
            'choice_set-0-question': question.pk,
            'choice_set-0-choice': 'kolo 1',
            'choice_set-0-is_correct': False,
            'choice_set-0-order': 1,
            'choice_set-1-question': question.pk,
            'choice_set-1-choice': 'kolo 2',
            'choice_set-1-is_correct': False,
            'choice_set-1-order': 2,
            'choice_set-2-question': question.pk,
            'choice_set-2-choice': 'kolo 3',
            'choice_set-2-is_correct': False,
            'choice_set-2-order': 3,
        }
        f = self.formset(data, instance=question)
        tools.assert_false(f.is_valid())
        tools.assert_in(unicode('You must specify one correct choice per question'), f.non_form_errors())
        tools.assert_equals(Choice.objects.filter(question=question).count(), 0)

    def test_update_success_for_one_correct_choice(self):
        question = self.questions[0]

        data = {
            'choice_set-TOTAL_FORMS': 3,
            'choice_set-INITIAL_FORMS': 3,
        }
        has_correct = False
        for ind, ch in enumerate(question.choice_set.all()):
            data.update({
                'choice_set-%s-id' % ind: ch.pk,
                'choice_set-%s-question' % ind: ch.question_id,
                'choice_set-%s-choice' % ind: ch.choice,
                'choice_set-%s-order' % ind: ch.order,
            })
            if ch.is_correct:
                is_correct = False
            else:
                is_correct = not has_correct
                has_correct = True
            data['choice_set-%s-is_correct' % ind] = is_correct

        f = self.formset(data, instance=question)
        tools.assert_true(f.is_valid())
        tools.assert_equals(Choice.objects.filter(question=question).count(), 3)
        tools.assert_equals(Choice.objects.filter(question=question, is_correct=True).count(), 1)
        f.save()
        tools.assert_equals(Choice.objects.filter(question=question).count(), 3)
        tools.assert_equals(Choice.objects.filter(question=question, is_correct=True).count(), 1)

    def test_update_success_for_changed_text(self):
        question = self.questions[0]

        data = {
            'choice_set-TOTAL_FORMS': 3,
            'choice_set-INITIAL_FORMS': 3,
        }

        for ind, ch in enumerate(question.choice_set.all()):
            data.update({
                'choice_set-%s-id' % ind: ch.pk,
                'choice_set-%s-question' % ind: ch.question_id,
                'choice_set-%s-choice' % ind: '%s-hi' % ch.choice,
                'choice_set-%s-order' % ind: ch.order,
                'choice_set-%s-is_correct' % ind: ch.is_correct
            })

        f = self.formset(data, instance=question)
        tools.assert_true(f.is_valid())
        tools.assert_equals(Choice.objects.filter(question=question).count(), 3)
        tools.assert_equals(Choice.objects.filter(question=question, is_correct=True).count(), 1)
        f.save()
        tools.assert_equals(Choice.objects.filter(question=question).count(), 3)
        tools.assert_equals(Choice.objects.filter(question=question, is_correct=True).count(), 1)

    def test_update_failed_for_no_correct_choice(self):
        question = self.questions[0]

        data = {
            'choice_set-TOTAL_FORMS': 3,
            'choice_set-INITIAL_FORMS': 3,
        }

        for ind, ch in enumerate(question.choice_set.all()):
            data.update({
                'choice_set-%s-id' % ind: ch.pk,
                'choice_set-%s-question' % ind: ch.question_id,
                'choice_set-%s-choice' % ind: ch.choice,
                'choice_set-%s-order' % ind: ch.order,
                'choice_set-%s-is_correct' % ind: False
            })

        f = self.formset(data, instance=question)
        tools.assert_false(f.is_valid())
        tools.assert_in(unicode('You must specify one correct choice per question'), f.non_form_errors())
        tools.assert_equals(Choice.objects.filter(question=question).count(), 3)
        tools.assert_equals(Choice.objects.filter(question=question, is_correct=True).count(), 1)

    def test_update_failed_for_more_correct_choices(self):
        question = self.questions[0]

        data = {
            'choice_set-TOTAL_FORMS': 3,
            'choice_set-INITIAL_FORMS': 3,
        }

        for ind, ch in enumerate(question.choice_set.all()):
            data.update({
                'choice_set-%s-id' % ind: ch.pk,
                'choice_set-%s-question' % ind: ch.question_id,
                'choice_set-%s-choice' % ind: ch.choice,
                'choice_set-%s-order' % ind: ch.order,
                'choice_set-%s-is_correct' % ind: True
            })

        f = self.formset(data, instance=question)
        tools.assert_false(f.is_valid())
        tools.assert_in(unicode('You must specify one correct choice per question'), f.non_form_errors())
        tools.assert_equals(Choice.objects.filter(question=question).count(), 3)
        tools.assert_equals(Choice.objects.filter(question=question, is_correct=True).count(), 1)
