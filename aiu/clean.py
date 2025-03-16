import re
import string
from typing import TYPE_CHECKING

from aiu.config import Config

if TYPE_CHECKING:
    from typing import Optional, Protocol

    class StringFormatter(Protocol):
        def __call__(self, s):
            # type: (str) -> str
            ...

SEPARATORS = frozenset([',', ';', ':', '!', '?', '.', ])
PUNCTUATIONS = frozenset(['.', '!', '?'])
WHITESPACES_NO_SPACE = string.whitespace.replace(' ', '')


def beautify_string(
    s,                              # type: str
    word_formatter=str.capitalize,  # type: Optional[StringFormatter]
    stop_word_formatter=str.lower,  # type: Optional[StringFormatter]
    first_word_formatter=None,      # type: Optional[StringFormatter]
):                                  # type: (...) -> str
    """
    Applies `beatification` operations for a `field` string.
        - removes invalid whitespaces
        - removes redundant spaces
        - applies the words formatter except for `stopwords` if specified (``None`` to skip, default: capitalize)
        - applies `stopwords` formatter if specified (``None`` to skip, default: lowercase)
        - applies the first word formatter of each sentence (default: same as word formatter)
        - literal replacement of case-insensitive match of `exceptions` by their explicit value
    """
    word_formatter = word_formatter or str
    stop_word_formatter = stop_word_formatter or str
    first_word_formatter = first_word_formatter or word_formatter
    for c in WHITESPACES_NO_SPACE:
        if c in s:
            s = s.replace(c, ' ')
    while '  ' in s:
        s = s.replace('  ', ' ')
    if Config.STOPWORDS_RENAME is not None:
        word_sep_list = re.split(r'(\W+)', s)
        s = ''.join(
            word_formatter(w)
            if w.lower() not in Config.STOPWORDS_RENAME
            else stop_word_formatter(w)
            for w in word_sep_list
        )
    words = s.split(' ', maxsplit=1)
    words = first_word_formatter(words[0]) + (' ' + words[1] if len(words) > 1 else '')
    for punctuation in PUNCTUATIONS:
        parts = words.split(punctuation)
        for p in range(1, len(parts)):
            if parts[p]:
                if parts[p][0] == ' ':
                    parts[p] = ' ' + word_formatter(parts[p][1:])
                else:
                    parts[p] = word_formatter(parts)
        words = punctuation.join(parts)
    if Config.EXCEPTIONS_RENAME is not None:
        for k, w in Config.EXCEPTIONS_RENAME.items():
            if k.lower() in words:
                words = words.replace(k.lower(), w)
    return words
