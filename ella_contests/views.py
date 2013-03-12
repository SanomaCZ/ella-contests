from django.db import transaction
from django.http import Http404
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.views.generic import FormView

from ella.core.views import get_templates_from_publishable
from ella.core.custom_urls import resolver


class QuestionForm(object):
    pass


class ContestantForm(object):
    pass


class ContestBaseView(FormView):
    template_name = 'form.html'

    @property
    def contest(self):
        if not hasattr(self, '_contest'):
            self._contest = self.context['object']
        return self._contest

    @property
    def question_number(self):
        return self.kwargs.get('question_number', 1) - 1

    @property
    def question(self):
        if not hasattr(self, '_question'):
            try:
                self._question = self.contest[self.question_number]
            except IndexError:
                raise Http404(_("There is no such question in this contest."))
        return self._question

    @property
    def next_question(self):
        if not hasattr(self, '_next_question'):
            self._next_question = self.question.next
        return self._next_question

    def get_template_names(self):
        return get_templates_from_publishable(self.template_name, self.contest)

    @method_decorator(csrf_protect)
    @method_decorator(transaction.commit_on_success)
    def dispatch(self, context, *args, **kwargs):
        self.context = context
        return super(ContestBaseView, self).dispatch(*args, **kwargs)


class ContestDetailView(ContestBaseView):
    form_class = QuestionForm

    def get_form_class(self):
        return self.form_class(self.question)

    def get_initial(self):
        #TODO: get data from cookie if there are
        return self.initial.copy()

    def get_success_url(self):
        if self.next_question:
            return self.next_question.get_absolute_url()
        return resolver.reverse(self.contest, 'ella-contests-contests-contestant')

    def form_valid(self, form):
        if not self.contest.is_active:
            return self.form_invalid(form)
        #TODO: save data from form to cookie or in form? -> form.save()
        return super(ContestDetailView, self).form_valid(form)


def contest_result(request, context):
    return render_to_response(
        get_templates_from_publishable('result.html', context['object']),
        context,
        context_instance=RequestContext(request)
    )


def contest_conditions(request, context):
    return render_to_response(
        get_templates_from_publishable('conditions.html', context['object']),
        context,
        context_instance=RequestContext(request)
    )


contest_detail = ContestDetailView.as_view()
