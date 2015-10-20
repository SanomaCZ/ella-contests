from django.utils import six
from django.utils.encoding import force_text


def encode_item(item):
    item = force_text(item)
    if six.PY2:
        item = item.encode("utf-8", "replace")
    return item
