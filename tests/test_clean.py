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


def test_beautify_string_multi_spaces():
    test_string = "This  is    a test  "
    expect_string = "This Is a Test"
    Config.STOPWORDS_RENAME = ["a"]
    result = beautify_string(test_string)
    assert result == expect_string


@pytest.mark.parametrize(
    "whitespace",
    "\t\n\r\v\f",
)
def test_beautify_string_whitespaces(whitespace):
    test_string = f"This is{whitespace}a test."
    expect_string = "This Is a Test."
    Config.STOPWORDS_RENAME = ["a"]
    result = beautify_string(test_string)
    assert result == expect_string


@pytest.mark.parametrize(
    ["test_string", "expect_string"],
    [
        (
            "This IS A TEsT. This IS A TEsT! This IS A TEsT?",
            "This Is a Test. This Is a Test! This Is a Test?",
        ),
    ]
)
def test_beautify_string_punctuation(test_string, expect_string):
    Config.STOPWORDS_RENAME = ["a"]
    result = beautify_string(test_string)
    assert result == expect_string
