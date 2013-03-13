from django.db import models, connection
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.conf import settings
from django.utils.safestring import mark_safe
#from django.contrib.auth.models import User

from ella.core.models import Publishable
from ella.photos.models import Photo
from ella.core.cache import CachedForeignKey, cache_this, get_cached_object
from ella.core.custom_urls import resolver


try:
    from django.utils.timezone import now
except ImportError:
    from datetime import datetime
    now = datetime.now

AUTH_USER_MODEL = getattr(settings, "AUTH_USER_MODEL", "auth.User")

QUESTIONS_CACHE_KEY_PATTERN = 'ella_contests_contest_questions:%s'
CHOICES_CACHE_KEY_PATTERN = 'ella_contests_contest_choices:%s'


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
    @cache_this(lambda q: QUESTIONS_CACHE_KEY_PATTERN % q.pk)
    def questions(self):
        return list(Question.objects.filter(contest=self).order_by('order'))

    def __getitem__(self, key):
        return self.questions[key]

    @property
    def questions_count(self):
        return len(self.questions)

    @property
    def right_choices(self):
        return '|'.join(
            '%d:%s' % (
                q.id,
                ','.join(str(c.id) for c in sorted(q.choices, key=lambda ch: ch.id) if c.points > 0)
            ) for q in sorted(self.questions, key=lambda q: q.id)
        )

    def get_correct_answers(self):
        """
        Returns queryset of contestants with correct answers on the current
        contest
        """
        count = Contestant.objects.filter(contest=self).count()
        return (Contestant.objects.filter(contest=self).filter(choices=self.right_choices)
            .extra(select={'count_guess_difference': 'ABS(%s - %d)' %
                (connection.ops.quote_name('count_guess'), count)})
            .order_by('count_guess_difference'))

    @property
    def current_text(self):
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
    contest = CachedForeignKey(Contest)
    order = models.PositiveIntegerField()
    photo = CachedForeignKey(Photo, blank=True, null=True, on_delete=models.SET_NULL)
    text = models.TextField()
    use_answer = models.BooleanField(_('Use answer instead choices '), default=False)

    choices_data = models.TextField()

    class Meta:
        verbose_name = _('Question')
        verbose_name_plural = _('Questions')
        unique_together = (('contest', 'order', ),)

    @property
    @cache_this(lambda q: CHOICES_CACHE_KEY_PATTERN % q.pk)
    def choices(self):
        return list(Choice.objects.filter(question=self))

    def get_absolute_url(self):
        return resolver.reverse(self.contest, 'ella-contests-contests-detail', choice=self.position)

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
        if self.position < self.contest.questions_count():
            return self.contest[self.position]
        else:
            return None


class Choice(models.Model):
    question = CachedForeignKey(Question, verbose_name=_('Question'))
    choice = models.TextField(_('Choice text'))
    points = models.IntegerField(_('Points'), default=1, blank=True, null=True)

    def __unicode__(self):
        #TODO: use render in widget instead unicode
        return mark_safe(u'%s' % self.choice)

    class Meta:
        verbose_name = _('Choice')
        verbose_name_plural = _('Choices')


class Contestant(models.Model):
    """
    Contestant info.
    """
    contest = CachedForeignKey(Contest, verbose_name=_('Contest'))
    user = CachedForeignKey(AUTH_USER_MODEL, null=True, blank=True, verbose_name=_('User'))
    name = models.CharField(_('First name'), max_length=50)
    surname = models.CharField(_('Last name'), max_length=50)
    email = models.EmailField(_('email'))
    phone_number = models.CharField(_('Phone number'), max_length=20, blank=True)
    address = models.CharField(_('Address'), max_length=200, blank=True)
    choices = models.TextField(_('Choices'), blank=True)
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
    def points(self):
        """
        Parse choices represented as a string
        and returns reached points count
        """
        points = 0
        if self.choices:
            for q in self.choices.split('|'):
                vs = q.split(':')
                for v in vs[1].split(','):
                    points += get_cached_object(Choice, pk=v).points
        return points


class Answer(models.Model):
    question = CachedForeignKey(Question, verbose_name=_('Question'))
    contestant = CachedForeignKey(Contestant, verbose_name=_('Contestant'))
    answer = models.TextField(_('Answer text'), blank=True)

    class Meta:
        verbose_name = _('Answer')
        verbose_name_plural = _('Answers')
        unique_together = (('contestant', 'question',),)


@receiver(post_delete, sender=Question)
@receiver(post_save, sender=Question)
def invalidate_question_cache(sender, instance, **kwargs):
    if getattr(instance, 'contest_id', None):
        cache.delete(QUESTIONS_CACHE_KEY_PATTERN % instance.contest_id)


@receiver(post_delete, sender=Choice)
@receiver(post_save, sender=Choice)
def invalidate_choices_cache(sender, instance, **kwargs):
    if getattr(instance, 'question_id', None):
        cache.delete(CHOICES_CACHE_KEY_PATTERN % instance.question_id)
