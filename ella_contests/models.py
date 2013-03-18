from django.db import models, IntegrityError
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
#from django.utils.safestring import mark_safe
#from django.contrib.auth.models import User

from ella.core.models import Publishable
from ella.photos.models import Photo
from ella.core.cache import CachedForeignKey, cache_this
from ella.core.custom_urls import resolver

from ella_contests.conf import contests_settings

try:
    from django.utils.timezone import now
except ImportError:
    from datetime import datetime
    now = datetime.now


class Contest(Publishable):
    text = models.TextField(_('Text'))
    text_results = models.TextField(_('Text with results'))
    active_from = models.DateTimeField(_('Active from'), blank=True, null=True)
    active_till = models.DateTimeField(_('Active till'), blank=True, null=True)

    class Meta:
        verbose_name = _('Contest')
        verbose_name_plural = _('Contests')
        ordering = ('-active_from',)

    @property
    @cache_this(lambda q: contests_settings.QUESTIONS_CACHE_KEY_PATTERN % q.pk)
    def questions(self):
        return list(Question.objects.filter(contest=self).order_by('order'))

    def __getitem__(self, key):
        return self.questions[key]

    @property
    def questions_count(self):
        return len(self.questions)

    @property
    def right_choices(self):
        qqs = Question.objects.filter(contest=self, is_required=True)
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


class Question(models.Model):
    contest = CachedForeignKey(Contest, related_name='question_qs')
    order = models.PositiveIntegerField()
    photo = CachedForeignKey(Photo, blank=True, null=True, on_delete=models.SET_NULL)
    text = models.TextField()
    is_required = models.BooleanField(_('Is required'), default=True)

    def __unicode__(self):
        return u'%s - %s %d' % (self.contest if self.contest_id else 'Contest',
                                _('Question'),
                                self.order)

    class Meta:
        verbose_name = _('Question')
        verbose_name_plural = _('Questions')
        unique_together = (('contest', 'order', ),)

    @property
    @cache_this(lambda q: contests_settings.CHOICES_CACHE_KEY_PATTERN % q.pk)
    def choices(self):
        return list(Choice.objects.filter(question=self))

    def get_absolute_url(self):
        return resolver.reverse(self.contest, 'ella-contests-contests-detail', question_number=self.position)

    @property
    def position(self):
        if not hasattr(self, '_position'):
            self._position = self.contest.question_qs.filter(order__lte=self.order).count()
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


class Choice(models.Model):
    question = CachedForeignKey(Question, verbose_name=_('Question'))
    choice = models.TextField(_('Choice text'))
    is_correct = models.BooleanField(_('Is correct'), default=False)
    inserted_by_user = models.BooleanField(_('Answare inserted by user'), default=False)

    def __unicode__(self):
        return u'%s: choice pk(%d)' % (self.question if self.question_id else 'Choice', self.pk)

    class Meta:
        verbose_name = _('Choice')
        verbose_name_plural = _('Choices')

    def clean(self):
        #check that correct is only one choice per question
        if self.question_id and self.is_correct:
            try:
                if not self.pk:
                    if self.__class__.objects.get(question=self.question, is_correct=True).pk != self.pk:
                        raise ValidationError(_("Only one correct choice is allowed per question"))
                else:
                    self.__class__.objects.exclude(pk=self.pk).get(question=self.question, is_correct=True)
                    raise ValidationError(_("Only one correct choice is allowed per question"))
            except Choice.DoesNotExist:
                pass

    def save(self, *args, **kwargs):
        try:
            self.clean()
        except ValidationError, e:
            raise IntegrityError(e.messages)

        super(Choice, self).save(*args, **kwargs)


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
    phone_number = models.CharField(_('Phone number'), max_length=20, blank=True)
    address = models.CharField(_('Address'), max_length=200, blank=True)
    #FIXME: should be null=True, blank True ?
    count_guess = models.IntegerField(_('Count guess'))
    winner = models.BooleanField(_('Winner'), default=False)
    created = models.DateTimeField(editable=False)

    class Meta:
        verbose_name = _('Contestant')
        verbose_name_plural = _('Contestants')
        unique_together = (('contest', 'email',),)
        ordering = ('-created',)

    def __unicode__(self):
        return u'%s %s' % (self.surname, self.name)

    def save(self, **kwargs):
        if not self.id:
            self.created = now()
        super(Contestant, self).save(**kwargs)

    @property
    def my_right_answers(self):
        return self.contest.right_answers.filter(contestant=self)

    def get_my_text_answers(self):
        return Answer.objects.filter(choice__question__contest=self.contest,
                                     contestant=self).exclude(choice__inserted_by_user=False)


class Answer(models.Model):
    contestant = CachedForeignKey(Contestant, verbose_name=_('Contestant'))
    choice = CachedForeignKey(Choice, verbose_name=_('Choice'))
    answer = models.TextField(_('Answer text'), blank=True)

    def __unicode__(self):
        return u'%s: %s' % (self.contestant if self.contestant_id else 'Contestant',
                            self.choice if self.choice_id else 'Choice',)

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
