from typing import AnyStr, List, Optional, Union
import string
import six
import os
import re

STOPWORDS = None
SEPARATORS = [',', ';', ':', '!', '?', '.', ]
WHITESPACES_NO_SPACE = string.whitespace.replace(' ', '')


def beautify_string(s, stopwords_config='./stopwords.cfg'):
    # type: (AnyStr, Optional[Union[AnyStr, List[AnyStr]]]) -> AnyStr
    """
    Applies `beatification` operations for a `field` string.
        - removes invalid whitespaces
        - removes redundant spaces
        - capitalizes words except `stopwords`
        - lowers words found in `stopwords`
        - capitalizes the first word
    """
    global STOPWORDS
    for c in WHITESPACES_NO_SPACE:
        if c in s:
            s = s.replace(c, ' ')
    while '  ' in s:
        s = s.replace('  ', ' ')
    if STOPWORDS is None and isinstance(stopwords_config, six.string_types) and os.path.isfile(stopwords_config):
        with open(stopwords_config, 'r') as f:
            STOPWORDS = f.readlines()
    if isinstance(stopwords_config, list):
        STOPWORDS = stopwords_config
    if STOPWORDS:
        word_sep_list = re.split('(\W+)', s)
        s = ''.join([w.capitalize() if w not in STOPWORDS else w.lower() for w in word_sep_list])
    return s.capitalize()
