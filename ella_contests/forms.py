from django import forms
from django.utils.translation import ugettext_lazy as _

from ella_contests.storages import storage
from ella_contests.models import Contestant, Answer


def QuestionForm(question):
    if question.use_answer:
        choice_field = forms.CharField(max_length=200,
                                       widget=forms.Textarea,
                                       required=False)
    else:
        #TODO: use own Choice field that control
        #if objects exits as ModelChoiceField in to_python method
        choice_field = forms.ChoiceField(
                choices=[(c.pk, c) for c in question.choices],
                widget=forms.RadioSelect,
                required=True
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
        exclude = ('contest', 'user', 'choices', 'winner', 'created')

    def __init__(self, view_instance, *args, **kwargs):
        self.view_instance = view_instance
        self.contest = view_instance.contest
        self.request = view_instance.request
        super(ContestantForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        #TODO: get logic for count choices
        answers, choices = self._prepare_answers_for_save(self.qforms)
        contestant = super(ContestantForm, self).save(commit=False)
        contestant.contest = self.contest
        contestant.choices = choices
        if self.request.user.is_authenticated():
            contestant.user = self.request.user
        if commit:
            contestant.save()
            for q, a in answers:
                Answer.objects.create(question=q, contestant=contestant, answer=a)
        return contestant

    def _prepare_answers_for_save(self, qforms):
        answers = []
        choices = []
        for question, f in sorted(qforms, key=lambda q: q[0].id):
            if question.use_answer:
                answers.append((question, f.cleaned_data['choice']))
            else:
                choices.append('%d:%s' % (question.id, f.cleaned_data['choice']))

        choices = '|'.join(choices)
        return answers, choices

    def _questions_valid(self):
        qforms = []
        forms_are_valid = True
        for i, question in enumerate(self.contest.questions, start=1):
            data = storage.get_data(self.contest, i, self.request)
            form = QuestionForm(question)(data)
            if data is None or not form.is_valid():
                forms_are_valid = False
            qforms.append((question, form))
        self.qforms = qforms
        #set var for context use to template say that questions integrity fail
        self.view_instance.questions_data_invalid = not forms_are_valid
        return forms_are_valid

    def clean(self):
        email = self.cleaned_data['email']
        if Contestant.objects.filter(email=email, contest=self.contest).count() > 0:
            raise forms.ValidationError(_("Your email is not unique, you probably competed"))
        if not self._questions_valid():
            raise forms.ValidationError(_("Some of the questions are filled incorrect"))
        return self.cleaned_data
