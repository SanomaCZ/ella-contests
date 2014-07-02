from itertools import chain

from django import forms
from django.forms import widgets as fwidgets
from django.utils.safestring import mark_safe
from django.utils.encoding import force_unicode


class WidgetContainer(object):

    def __init__(self, *widgets):
        self.widgets = widgets

    def __unicode__(self):
        return mark_safe(u" ".join(force_unicode(w) for w in self.widgets))


class RadioFieldRenderer(fwidgets.RadioFieldRenderer):
    """
    An object used by RadioSelect to enable customization of radio widgets.
    """
    text_name_pattern = "%s_text_%s"

    def _get_widgets(self, choice, i):
        widgets = []
        # check if choice has set inserted_by_user to True
        if choice[2]:
            value = self.value if isinstance(self.value, (tuple, list)) else (self.value, "")
            text_name = self.text_name_pattern % (self.name, choice[0])
            r_attrs = self.attrs.copy()
            if 'id' not in r_attrs.keys():
                r_attrs['id'] = 'id_%s' % text_name
            rw = fwidgets.RadioInput(self.name, value[0], r_attrs, choice, i)
            widgets.append(rw)
            attrs = dict(onfocus='javascript:document.getElementById("%s_%s").checked = true;return false;' % (rw.attrs['id'],
                                                                                                               rw.index))
            widgets.append(fwidgets.TextInput().render(name=text_name, value=value[1], attrs=attrs))
        else:
            widgets.append(fwidgets.RadioInput(self.name, self.value, self.attrs.copy(), choice, i))
        return widgets

    def __iter__(self):
        for i, choice in enumerate(self.choices):
            yield WidgetContainer(*self._get_widgets(choice, i))

    def __getitem__(self, idx):
        choice = self.choices[idx]  # Let the IndexError propogate
        return WidgetContainer(*self._get_widgets(choice, idx))


class ContestRadioSelect(forms.RadioSelect):
    renderer = RadioFieldRenderer

    def get_renderer(self, name, value, attrs=None, choices=()):
        """Returns an instance of the renderer."""
        is_tuple = isinstance(value, (tuple, list))
        if is_tuple:
            value, text = value
        if value is None:
            value = ''
        value = force_unicode(value)  # Normalize to string.
        final_attrs = self.build_attrs(attrs)
        choices = list(chain(self.choices, choices))
        if is_tuple:
            if text is None:
                text = ''
            text = force_unicode(text)  # Normalize to string.
            value = (value, text)
        return self.renderer(name, value, final_attrs, choices)

    def value_from_datadict(self, data, files, name):
        """
        Given a dictionary of data and this widget's name, returns the value
        of this widget. Returns None if it's not provided.
        """
        value = data.get(name, None)
        if value is not None:
            text_name = RadioFieldRenderer.text_name_pattern % (name, value)
            text_value = data.get(text_name, None)
            if text_value is not None:
                value = (value, text_value)
        return value
