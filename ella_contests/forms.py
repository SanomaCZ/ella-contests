from django import forms
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
    #TODO: use own Choice field that control
    #if objects exits as ModelChoiceField in to_python method
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
        #TODO: get logic for count choices
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
        email = self.cleaned_data.get('email', None)
        if email and Contestant.objects.filter(email=email, contest=self.contest).count() > 0:
            raise forms.ValidationError(_("Your email is not unique, you probably competed"))
        if not self._questions_valid():
            raise forms.ValidationError(_("Some of the questions are filled incorrect"))
        return self.cleaned_data
