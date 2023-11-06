import pytest

from aiu.updater import filter_shared_items


@pytest.mark.parametrize(
    ["samples", "expect"],
    [
        (
            [
                ["test", "test", "test", "other", "value"],
                ["test", "test", "test", "something", "else"],
                ["test", "test", "test", "another"],
            ],
            [
                ["other", "value"],
                ["something", "else"],
                ["another"],
            ]
        ),
        (
                [
                    ["test", "test", "test", "other", "value"],
                    ["test", "test", "something", "else"],
                    ["test", "test", "test", "another"],
                ],
                [
                    ["test", "other", "value"],
                    ["something", "else"],
                    ["test", "another"],
                ]
        ),
        (
                [
                    ["test", "no", "other", "value"],
                    ["test", "test", "something", "else"],
                    ["test", "test", "test", "another"],
                ],
                [
                    ["no", "other", "value"],
                    ["test", "something", "else"],
                    ["test", "test", "another"],
                ]
        ),
        (
                [
                    ["no", "other", "value"],
                    ["test", "test", "something", "else"],
                    ["test", "test", "test", "another"],
                ],
                [
                    ["no", "other", "value"],
                    ["test", "test", "something", "else"],
                    ["test", "test", "test", "another"],
                ]
        )
    ]
)
def test_filter_shared(samples, expect):
    result = filter_shared_items(samples)
    assert result == expect
