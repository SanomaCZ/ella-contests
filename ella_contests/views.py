from django.http import Http404, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.views.generic import FormView
from django.utils.translation import ugettext as _

from ella.core.views import get_templates_from_publishable
from ella.core.custom_urls import resolver

from ella_contests.forms import QuestionForm, ContestantForm
from ella_contests.storages import storage
from ella_contests.utils import transaction


class ContestBaseView(FormView):
    template_name = None
    ajax_template_name = None

    @property
    def contest(self):
        if not hasattr(self, '_contest'):
            self._contest = self.context['object']
        return self._contest

    @property
    def current_page(self):
        return int(self.kwargs.get('question_number', 1))

    @property
    def question_number(self):
        return self.current_page - 1

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
        template_name = self.template_name
        if self.request.is_ajax():
            template_name = self.ajax_template_name
        return get_templates_from_publishable(template_name, self.contest)

    def get_context_data(self, **kwargs):
        data = super(ContestBaseView, self).get_context_data(**kwargs)
        data.update(self.context)
        return data


class ContestDetailFormView(ContestBaseView):
    template_name = 'form.html'
    ajax_template_name = 'form_async.html'

    def get_form_class(self):
        return QuestionForm(self.question)

    def get_initial(self):
        data = storage.get_data(self.contest, self.question.pk, self.request)
        return data

    def get_success_url(self):
        if self.next_question:
            return self.next_question.get_absolute_url()
        return resolver.reverse(self.contest, 'ella-contests-contests-contestant')

    def form_valid(self, form):
        if not self.contest.is_active:
            return self.form_invalid(form)
        response = super(ContestDetailFormView, self).form_valid(form)
        storage.set_data(self.contest, self.question.pk, form.cleaned_data, response)
        storage.set_last_step(self.contest, self.current_page, response)
        return response

    def get_context_data(self, **kwargs):
        data = super(ContestDetailFormView, self).get_context_data(**kwargs)
        data.update({
            'current_page': self.current_page,
            'question': self.question,
            'question_number': self.question_number,
        })
        return data

    @method_decorator(csrf_protect)
    @method_decorator(transaction.atomic)
    def dispatch(self, request, context, *args, **kwargs):
        self.context = context
        self.kwargs = kwargs
        #check if user can see this step else redirect
        last_step = storage.get_last_step(self.contest, request)
        if last_step is None:
            if self.current_page == 1:
                return super(ContestDetailFormView, self).dispatch(request, *args, **kwargs)
            url = resolver.reverse(self.contest, 'ella-contests-contests-detail', question_number=1)
            return HttpResponseRedirect(url)
        if self.current_page != last_step + 1:
            if self.next_question:
                url = resolver.reverse(self.contest, 'ella-contests-contests-detail',
                                       question_number=self.next_question.position)
            else:
                url = resolver.reverse(self.contest, 'ella-contests-contests-contestant')
            return HttpResponseRedirect(url)
        return super(ContestDetailFormView, self).dispatch(request, *args, **kwargs)


class ContestContestantView(ContestBaseView):
    template_name = 'contestant.html'
    ajax_template_name = 'contestant_async.html'
    form_class = ContestantForm

    @property
    def question_form_class(self):
        return QuestionForm

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

    def form_invalid(self, form):
        response = super(ContestContestantView, self).form_invalid(form)
        if getattr(self, 'questions_data_invalid', False):
            storage.remove_last_step(self.contest, response)
        return response

    def form_valid(self, form):
        if not self.contest.is_active:
            return self.form_invalid(form)
        form.save()
        response = super(ContestContestantView, self).form_valid(form)
        storage.remove_all_data(self.contest, response)
        return response

    @method_decorator(csrf_protect)
    @method_decorator(transaction.atomic)
    def dispatch(self, request, context, *args, **kwargs):
        self.context = context
        self.kwargs = kwargs
        last_step = storage.get_last_step(self.contest, request)
        if last_step is None:
            url = resolver.reverse(self.contest, 'ella-contests-contests-detail', question_number=1)
            return HttpResponseRedirect(url)
        if self.contest.questions_count != last_step:
            url = resolver.reverse(self.contest, 'ella-contests-contests-detail', question_number=last_step + 1)
            return HttpResponseRedirect(url)
        return super(ContestContestantView, self).dispatch(request, *args, **kwargs)


def contest_result(request, context):
    template_name = 'result.html'
    if request.is_ajax():
        template_name = 'result_async.html'
    return render_to_response(
        get_templates_from_publishable(template_name, context['object']),
        context,
        context_instance=RequestContext(request)
    )


def contest_conditions(request, context):
    template_name = 'conditions.html'
    if request.is_ajax():
        template_name = 'conditions_async.html'
    return render_to_response(
        get_templates_from_publishable(template_name, context['object']),
        context,
        context_instance=RequestContext(request)
    )


contest_detail = ContestDetailFormView.as_view()
contest_contestant = ContestContestantView.as_view()
