from django import forms
from django.utils.encoding import smart_unicode
from django.core import validators

from ella_contests.widgets import ContestRadioSelect


class ContestChoiceField(forms.ChoiceField):
    widget = ContestRadioSelect

    def to_python(self, value):
        "Returns a Unicode object."
        if isinstance(value, (tuple, list)):
            value, text = value
            if value in validators.EMPTY_VALUES:
                return (u'', smart_unicode(text))
            return (smart_unicode(value), smart_unicode(text))
        else:
            if value in validators.EMPTY_VALUES:
                return u''
            return smart_unicode(value)

    def validate(self, value):
        """
        Validates that the input is in self.choices.
        """
        if isinstance(value, (tuple, list)):
            value, text = value
        super(forms.ChoiceField, self).validate(value)
        if value and not self.valid_value(value):
            raise forms.ValidationError(self.error_messages['invalid_choice'] % {'value': value})

    def valid_value(self, value):
        "Check to see if the provided value is a valid choice"
        for k, v, t in self.choices:
            if value == smart_unicode(k):
                return True
        return False
