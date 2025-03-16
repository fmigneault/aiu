import pytest

from aiu.clean import beautify_string
from aiu.config import Config


@pytest.mark.parametrize(
    ["test_string", "expect_string", "word_formatter", "stop_word_formatter", "first_word_formatter"],
    [
        ("This IS A TEsT", "this is a test", str.lower, str.lower, str.lower),
        ("This IS A TEsT", "this Is a Test", str.capitalize, str.lower, str.lower),
        ("This IS A TEsT", "This Is a Test", str.capitalize, str.lower, str.capitalize),
    ]
)
def test_beautify_string(test_string, expect_string, word_formatter, stop_word_formatter, first_word_formatter):
    Config.STOPWORDS_RENAME = ["a"]
    result = beautify_string(test_string, word_formatter, stop_word_formatter, first_word_formatter)
    assert result == expect_string
