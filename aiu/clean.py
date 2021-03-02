import aiu
import re
import string

SEPARATORS = frozenset([',', ';', ':', '!', '?', '.', ])
PUNCTUATIONS = frozenset(['.', '!', '?'])
WHITESPACES_NO_SPACE = string.whitespace.replace(' ', '')


def beautify_string(s):
    # type: (str) -> str
    """
    Applies `beatification` operations for a `field` string.
        - removes invalid whitespaces
        - removes redundant spaces
        - capitalizes words except `stopwords`
        - lowercase of words found in `stopwords`
        - literal replacement of case-insensitive match of `exceptions` by their explicit value
        - capitalizes the first word of each sentence
    """
    for c in WHITESPACES_NO_SPACE:
        if c in s:
            s = s.replace(c, ' ')
    while '  ' in s:
        s = s.replace('  ', ' ')
    if aiu.Config.STOPWORDS:
        word_sep_list = re.split(r'(\W+)', s)
        s = ''.join(w.capitalize() if w not in aiu.Config.STOPWORDS else w.lower() for w in word_sep_list)
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
    if aiu.Config.EXCEPTIONS:
        for k, w in aiu.Config.EXCEPTIONS.items():
            if k.lower() in words:
                words = words.replace(k.lower(), w)
    return words
