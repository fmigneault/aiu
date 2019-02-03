from typing import AnyStr, List, Optional, Union
import aiu
import string
import six
import os
import re

SEPARATORS = [',', ';', ':', '!', '?', '.', ]
WHITESPACES_NO_SPACE = string.whitespace.replace(' ', '')


def beautify_string(s, stopwords_config=aiu.DEFAULT_STOPWORDS_CONFIG):
    # type: (AnyStr, Optional[Union[AnyStr, List[AnyStr]]]) -> AnyStr
    """
    Applies `beatification` operations for a `field` string.
        - removes invalid whitespaces
        - removes redundant spaces
        - capitalizes words except `stopwords`
        - lowers words found in `stopwords`
        - capitalizes the first word
    """
    for c in WHITESPACES_NO_SPACE:
        if c in s:
            s = s.replace(c, ' ')
    while '  ' in s:
        s = s.replace('  ', ' ')
    if aiu.STOPWORDS is None and isinstance(stopwords_config, six.string_types) and os.path.isfile(stopwords_config):
        with open(stopwords_config, 'r') as f:
            aiu.STOPWORDS = [w.strip() for w in f.readlines()]
    if isinstance(stopwords_config, list):
        aiu.STOPWORDS = stopwords_config
    if aiu.STOPWORDS:
        word_sep_list = re.split('(\W+)', s)
        s = ''.join([w.capitalize() if w not in aiu.STOPWORDS else w.lower() for w in word_sep_list])
    words = s.split(' ', maxsplit=1)
    words = words[0].capitalize() + (' ' + words[1] if len(words) > 1 else '')
    return words
