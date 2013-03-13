from django.db import transaction
from django.http import Http404, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.views.generic import FormView

from ella.core.views import get_templates_from_publishable
from ella.core.custom_urls import resolver

from ella_contests.forms import QuestionForm, ContestantForm
from ella_contests.storages import storage


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

    def get_context_data(self, **kwargs):
        data = super(ContestBaseView, self).get_context_data(**kwargs)
        data.update(self.context)
        return data


class ContestDetailView(ContestBaseView):
    form_class = QuestionForm

    def get_form_class(self):
        return self.form_class(self.question)

    def get_initial(self):
        data = storage.get_data(self.contest, self.question_number, self.request)
        #FIXME: data may be None but what form needed?
        return data

    def get_success_url(self):
        if self.next_question:
            return self.next_question.get_absolute_url()
        return resolver.reverse(self.contest, 'ella-contests-contests-contestant')

    def form_valid(self, form):
        if not self.contest.is_active:
            return self.form_invalid(form)
        #TODO: save data from form to cookie or in form? -> form.save()
        response = super(ContestDetailView, self).form_valid(form)
        storage.set_data(self.contest, self.question_number, self.form.cleaned_data, response)
        storage.set_last_step(self.contest, self.question_number, response)
        return response

    @method_decorator(csrf_protect)
    @method_decorator(transaction.commit_on_success)
    def dispatch(self, request, context, *args, **kwargs):
        self.context = context
        #TODO: add check if user can see this step else redirect
        last_step = storage.get_last_step(self.contest, request)
        if last_step is None:
            url = resolver.reverse(self.contest, 'ella-contests-contests-detail', choice=1)
            return HttpResponseRedirect(url)
        if self.question_number != last_step + 1:
            if self.next_question:
                url = resolver.reverse(self.contest, 'ella-contests-contests-detail', choice=self.next_question.position)
            else:
                url = resolver.reverse(self.contest, 'ella-contests-contests-contestant')
            return HttpResponseRedirect(url)
        return super(ContestBaseView, self).dispatch(request, *args, **kwargs)


class ContestContestantView(ContestBaseView):
    template_name = 'contestant.html'
    form_class = ContestantForm
    question_form_class = QuestionForm

    def get_initial(self):
        initial_data = super(ContestContestantView, self).get_initial()
        if self.request.user.is_authenticated():
            initial_data.update({
                'name': self.request.user.first_name,
                'surname': self.request.user.last_name,
                'email': self.request.user.email,
            })
        return initial_data

    def get_form_kwargs(self):
        kwargs = super(ContestContestantView, self).get_form_kwargs()
        kwargs.update({'view_instance': self})
        return kwargs

    def get_context_data(self, **kwargs):
        data = super(ContestContestantView, self).get_context_data(**kwargs)
        data.update({
            'questions_data_invalid': getattr(self, 'questions_data_invalid', False)
        })
        return data

    def get_success_url(self):
        return resolver.reverse(self.contest, 'ella-contests-contests-result')

    def form_valid(self, form):
        if not self.contest.is_active:
            return self.form_invalid(form)
        #TODO: save data from form to cookie or in form? -> form.save()
        form.save()
        return super(ContestContestantView, self).form_valid(form)

    @method_decorator(csrf_protect)
    @method_decorator(transaction.commit_on_success)
    def dispatch(self, request, context, *args, **kwargs):
        self.context = context
        last_step = storage.get_last_step(self.contest, request)
        if last_step is None:
            url = resolver.reverse(self.contest, 'ella-contests-contests-detail', choice=1)
            return HttpResponseRedirect(url)
        if self.contest.questions_count != last_step:
            url = resolver.reverse(self.contest, 'ella-contests-contests-detail', choice=last_step + 1)
            return HttpResponseRedirect(url)
        return super(ContestBaseView, self).dispatch(request, *args, **kwargs)


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
contest_contestant = ContestContestantView.as_view()
