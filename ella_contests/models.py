from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

from ella.core.models import Publishable
from ella.photos.models import Photo
from ella.core.cache import CachedForeignKey, cache_this
from ella.core.custom_urls import resolver

from ella_contests.conf import contests_settings

from ella.utils.timezone import now


class Contest(Publishable):
    text = models.TextField(_('Text'))
    text_results = models.TextField(_('Text with results'), blank=True)
    text_announcement = models.TextField(_('Text with announcement'), blank=True)
    active_from = models.DateTimeField(_('Active from'), blank=True, null=True)
    active_till = models.DateTimeField(_('Active till'), blank=True, null=True)

    class Meta:
        verbose_name = _('Contest')
        verbose_name_plural = _('Contests')
        ordering = ('-active_from',)

    @property
    @cache_this(lambda q: contests_settings.QUESTIONS_CACHE_KEY_PATTERN % q.pk)
    def questions(self):
        return list(self.question_set.order_by('order'))

    def __getitem__(self, key):
        return self.questions[key]

    @property
    def questions_count(self):
        return len(self.questions)

    @property
    def right_choices(self):
        qqs = self.question_set.filter(is_required=True).only('pk')
        return Choice.objects.filter(question__id__in=qqs, is_correct=True)

    @property
    def right_answers(self):
        return Answer.objects.filter(choice__id__in=self.right_choices).exclude(answer="",
                                                                                choice__inserted_by_user=True)

    def get_contestants_with_correct_answer(self):
        """
        Returns queryset of contestants with correct answers on the current
        contest
        """
        qs = Contestant.objects.filter(answer__id__in=self.right_answers)\
            .annotate(answers_count=models.Count('answer')).order_by('-answers_count', 'created')
        return qs

    @property
    def content(self):
        """
        Objects text content depends on its current life-cycle stage
        """
        if self.is_closed:
            return self.text_results
        else:
            return self.text

    @property
    def is_not_yet_active(self):
        if self.active_from and self.active_from > now():
            return True
        return False

    @property
    def is_closed(self):
        """
        Returns True if the object is in the closed life-cycle stage.
        Otherwise returns False
        """
        if self.active_till and self.active_till < now():
            return True
        return False

    @property
    def is_active(self):
        """
        Returns True if the object is in the active life-cycle stage.
        Otherwise returns False
        """
        if not self.is_closed and not self.is_not_yet_active:
            return True
        return False


@python_2_unicode_compatible
class Question(models.Model):
    contest = CachedForeignKey(Contest, verbose_name=_('Contest'))
    order = models.PositiveIntegerField(_('Order'), db_index=True)
    photo = CachedForeignKey(Photo, blank=True, null=True, verbose_name=_('Photo'),
                             on_delete=models.SET_NULL)
    text = models.TextField()
    is_required = models.BooleanField(_('Is required'), default=True, db_index=True)

    def __str__(self):
        return '%s - %s %d' % (
            self.contest if self.contest_id else 'Contest',
            _('Question'),
            self.order
        )

    class Meta:
        verbose_name = _('Question')
        verbose_name_plural = _('Questions')
        ordering = ('order',)
        unique_together = (('contest', 'order', ),)

    @property
    @cache_this(lambda q: contests_settings.CHOICES_CACHE_KEY_PATTERN % q.pk)
    def choices(self):
        return list(self.choice_set.order_by('order'))

    def get_absolute_url(self):
        return resolver.reverse(self.contest, 'ella-contests-contests-detail', question_number=self.position)

    @property
    def position(self):
        if not hasattr(self, '_position'):
            self._position = self.contest.question_set.filter(order__lte=self.order).count()
        return self._position

    @property
    def prev(self):
        if self.position > 1:
            return self.contest[self.position - 2]
        else:
            return None

    @property
    def next(self):
        if self.position < self.contest.questions_count:
            return self.contest[self.position]
        else:
            return None


@python_2_unicode_compatible
class Choice(models.Model):
    question = CachedForeignKey(Question, verbose_name=_('Question'))
    choice = models.TextField(_('Choice text'))
    order = models.PositiveIntegerField(_('Order'), db_index=True)
    is_correct = models.BooleanField(_('Is correct'), default=False, db_index=True)
    inserted_by_user = models.BooleanField(_('Answare inserted by user'), default=False)

    def __str__(self):
        return '%s: choice (%d)' % (self.question if self.question_id else 'Choice', self.order)

    class Meta:
        verbose_name = _('Choice')
        verbose_name_plural = _('Choices')
        ordering = ('order',)
        unique_together = (('question', 'order', ),)


@python_2_unicode_compatible
class Contestant(models.Model):
    """
    Contestant info.
    """
    contest = CachedForeignKey(Contest, verbose_name=_('Contest'))
    user = CachedForeignKey(contests_settings.AUTH_USER_MODEL,
                            null=True, blank=True, verbose_name=_('User'))
    name = models.CharField(_('First name'), max_length=50)
    surname = models.CharField(_('Last name'), max_length=50)
    email = models.EmailField(_('email'))
    address = models.CharField(_('Address'), max_length=200)
    phone_number = models.CharField(_('Phone number'), max_length=20, blank=True)
    winner = models.BooleanField(_('Winner'), default=False)
    created = models.DateTimeField(_('Created'), editable=False)

    class Meta:
        verbose_name = _('Contestant')
        verbose_name_plural = _('Contestants')
        unique_together = (('contest', 'email',),)
        ordering = ('-created',)

    def __str__(self):
        return '%s %s' % (self.surname, self.name)

    def save(self, **kwargs):
        if not self.id:
            self.created = now()
        super(Contestant, self).save(**kwargs)

    @property
    def my_right_answers(self):
        return self.contest.right_answers.filter(contestant=self)

    def get_my_text_answers(self):
        return self.answer_set.exclude(choice__inserted_by_user=False)


@python_2_unicode_compatible
class Answer(models.Model):
    contestant = CachedForeignKey(Contestant, verbose_name=_('Contestant'))
    choice = CachedForeignKey(Choice, verbose_name=_('Choice'))
    answer = models.TextField(_('Answer text'), blank=True)

    def __str__(self):
        return '%s: %s' % (
            self.contestant if self.contestant_id else 'Contestant',
            self.choice if self.choice_id else 'Choice',
        )

    class Meta:
        verbose_name = _('Answer')
        verbose_name_plural = _('Answers')
        unique_together = (('contestant', 'choice',),)


@receiver(post_delete, sender=Question)
@receiver(post_save, sender=Question)
def invalidate_question_cache(sender, instance, **kwargs):
    if getattr(instance, 'contest_id', None):
        cache.delete(contests_settings.QUESTIONS_CACHE_KEY_PATTERN % instance.contest_id)


@receiver(post_delete, sender=Choice)
@receiver(post_save, sender=Choice)
def invalidate_choices_cache(sender, instance, **kwargs):
    if getattr(instance, 'question_id', None):
        cache.delete(contests_settings.CHOICES_CACHE_KEY_PATTERN % instance.question_id)
