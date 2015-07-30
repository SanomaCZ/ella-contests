from django import forms
from django.forms.models import BaseInlineFormSet
from django.utils.translation import ugettext_lazy as _
from django import template

from ella.core.cache import get_cached_object

from ella_contests.storages import storage
from ella_contests.models import Contestant, Answer, Choice
from ella_contests.fields import ContestChoiceField

from ella_contests.conf import contests_settings


def QuestionForm(question):
    def use_render(text):
        if contests_settings.RENDER_CHOICES:
            template_name = 'render-contests-choice'
            return template.Template(text, name=template_name).render(template.Context({}))
        return text
    choice_field = ContestChoiceField(
        choices=[(c.pk, use_render(c.choice), c.inserted_by_user) for c in question.choices],
        required=True if question.is_required else False
    )

    class _QuestionForm(forms.Form):
        """
        Question form with all its choices
        """
        choice = choice_field

    return _QuestionForm


class ContestantForm(forms.ModelForm):

    class Meta:
        model = Contestant
        exclude = ('contest', 'user', 'winner', 'created')

    def __init__(self, view_instance, *args, **kwargs):
        self.view_instance = view_instance
        self.contest = view_instance.contest
        self.request = view_instance.request
        super(ContestantForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        contestant = super(ContestantForm, self).save(commit=False)
        contestant.contest = self.contest
        if self.request.user.is_authenticated():
            contestant.user = self.request.user
        if commit:
            contestant.save()
            for q, f in self.qforms:
                ch_pk = f.cleaned_data['choice']
                if ch_pk:
                    if isinstance(ch_pk, (tuple, list)):
                        ch_pk, ans = ch_pk
                        if not q.is_required and not ans.strip():
                            continue
                        data = dict(contestant=contestant,
                                    choice=get_cached_object(Choice, pk=ch_pk),
                                    answer=ans.strip())
                    else:
                        data = dict(contestant=contestant,
                                    choice=get_cached_object(Choice, pk=ch_pk))
                    Answer.objects.create(**data)
        return contestant

    def _questions_valid(self):
        qforms = []
        forms_are_valid = True
        for question in self.contest.questions:
            data = storage.get_data(self.contest, question.pk, self.request)
            form = QuestionForm(question)(data)
            if data is None or not form.is_valid():
                forms_are_valid = False
            qforms.append((question, form))
        self.qforms = qforms
        # set var for context use to template say that questions integrity fail
        self.view_instance.questions_data_invalid = not forms_are_valid
        return forms_are_valid

    def clean(self):
        email = self.cleaned_data.get('email', None)
        if email and Contestant.objects.filter(email=email, contest=self.contest).count() > 0:
            raise forms.ValidationError(_("Your email is not unique, you probably competed"))
        if not self._questions_valid():
            raise forms.ValidationError(_("Some of the questions are filled incorrect"))
        return self.cleaned_data


class ChoiceForm(forms.ModelForm):

    class Meta:
        model = Choice
        fields = '__all__'

    def clean(self):
        cls = self._meta.model
        cleaned_data = super(ChoiceForm, self).clean()
        question = cleaned_data.get('question', None)
        is_correct = cleaned_data.get('is_correct', None)
        if question and is_correct:
            try:
                if not self.instance:
                    if cls.objects.get(question=question, is_correct=True):
                        raise forms.ValidationError(_("Only one correct choice is allowed per question"))
                else:
                    cls.objects.exclude(pk=self.instance.pk).get(question=question, is_correct=True)
                    raise forms.ValidationError(_("Only one correct choice is allowed per question"))
            except Choice.DoesNotExist:
                pass

        return cleaned_data


class ChoiceInlineFormset(BaseInlineFormSet):
    def clean(self):
        super(ChoiceInlineFormset, self).clean()
        if any(self.errors):
            return
        correct_answers = tuple(
            f.cleaned_data['is_correct']
            for f in self.forms
            if 'is_correct' in f.cleaned_data and f.cleaned_data['is_correct'] is True
        )
        if len(correct_answers) != 1:
            raise forms.ValidationError(_("You must specify one correct choice per question"))
