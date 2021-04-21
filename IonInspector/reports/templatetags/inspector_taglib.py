import re

from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

LEGAL_ID = re.compile("[a-zA-Z][-\w:.]*")
ILLEGAL_PREFIX = re.compile("^[^a-zA-Z]")
ILLEGAL_CHAR = re.compile("[^-:\w]")


@register.filter
@stringfilter
def hrefify(value):
    """
    Map from input string that may not necessarily be restricted to valid characters for HTML id
    attributed, to an output string that ony consists of characters legal in that context and does
    not utilize the legal but ambiguous period '.'.

    Period ('.') avoidance is provided by replacement with underscore ('_').  Users are advised to
    avoid naming schemes where the only difference between two unique names entirely due to
    transpositions of '.' for '_' and vice-versa.  Any collection of unique names will suffer
    non-unique collisions between the two mapped names when the inputs are distinct only by virtue
    of one or more transpositions between '.' and '_'.

    A similar caution exists when mapping names whose uniqueness is dependent solely on basis of an equal
    number of characters that are not all invalid HTML ID characters.  Invalid HTML id characters and periods
    are both mapped to underscores here.

    This function also must satisfy the leading character restriction placed on HTNL ids.  If the
    first character of a name produced by underscore mapping alone would violate this requirement about
    on initial characters, it will also prefix a single 'x' to the transformed string.

    Note: This function does not remove leading or trailing whitespace, nor does it consolidate multiple
    whitespace characters.  Please apply such transformations through earlier filters explicitly if
    such whitespace is not part of you identity semantics.
    """
    if value is None:
        return None
    if type(value) != str:
        value = str(value)
    if len(value) == 0:
        return "x"
    tokens = ILLEGAL_CHAR.split(value)
    if len(tokens[0]) == 0:
        tokens[0] = "x"
    elif ILLEGAL_PREFIX.match(tokens[0]):
        tokens[0] = "x" + tokens[0]
    return "_".join(tokens)
