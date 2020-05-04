from typing import AnyStr, List, Optional, Union
import aiu
import string
import six
import os
import re

SEPARATORS = frozenset([',', ';', ':', '!', '?', '.', ])
PUNCTUATIONS = frozenset(['.', '!', '?'])
WHITESPACES_NO_SPACE = string.whitespace.replace(' ', '')


def load_config(maybe_config, wanted_config, is_map):
    if maybe_config is None and isinstance(wanted_config, six.string_types) and os.path.isfile(wanted_config):
        try:
            with open(wanted_config, 'r') as f:
                lines = [w.strip() for w in f.readlines()]
                if is_map:
                    lines = [line.split(':') for line in lines]
                    maybe_config = {k.strip().lower(): w.strip() for k, w in lines}
                else:
                    maybe_config
        except Exception:
            raise ValueError("Invalid configuration file could not be parsed:\n  file: [{!s}]\n  map?: [{}]".format(
                wanted_config, is_map
            ))
    if isinstance(wanted_config, (list, dict)):
        maybe_config = wanted_config
    return maybe_config


def beautify_string(s, stopwords_config=aiu.DEFAULT_STOPWORDS_CONFIG, exceptions_config=aiu.DEFAULT_EXCEPTIONS_CONFIG):
    # type: (AnyStr, aiu.StopwordsType, aiu.ExceptionsType) -> AnyStr
    """
    Applies `beatification` operations for a `field` string.
        - removes invalid whitespaces
        - removes redundant spaces
        - capitalizes words except `stopwords`
        - lowercase of words found in `stopwords`
        - literal replacement of case-insensitive match of `exceptions` by their explicit value
        - capitalizes the first word of each sentence
    """
    aiu.STOPWORDS = load_config(aiu.STOPWORDS, stopwords_config, is_map=False)
    aiu.EXCEPTIONS = load_config(aiu.EXCEPTIONS, exceptions_config, is_map=True)
    for c in WHITESPACES_NO_SPACE:
        if c in s:
            s = s.replace(c, ' ')
    while '  ' in s:
        s = s.replace('  ', ' ')
    if aiu.STOPWORDS:
        word_sep_list = re.split(r'(\W+)', s)
        s = ''.join(w.capitalize() if w not in aiu.STOPWORDS else w.lower() for w in word_sep_list)
    words = s.split(' ', maxsplit=1)
    words = words[0].capitalize() + (' ' + words[1] if len(words) > 1 else '')
    for punctuation in PUNCTUATIONS:
        parts = words.split(punctuation)
        for p in range(1, len(parts)):
            if parts[p]:
                if parts[p][0] == ' ':
                    parts[p] = ' ' + parts[p][1].upper() + parts[p][2:]
                else:
                    parts[p] = parts[p][0].upper() + parts[p][1:]
        words = punctuation.join(parts)
    if aiu.EXCEPTIONS:
        for k, w in aiu.EXCEPTIONS.items():
            if k.lower() in words:
                words = words.replace(k.lower(), w)
    return words
