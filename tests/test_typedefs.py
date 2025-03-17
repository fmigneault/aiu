import copy
import datetime

from aiu.typedefs import Duration


def test_duration_deepcopy():
    duration = Duration("1:23:45")
    duration_copy = copy.deepcopy(duration)
    assert duration == duration_copy
    assert duration is not duration_copy


def test_duration_from_str():
    duration = Duration("1:23")
    assert duration.seconds == 23
    assert duration.minutes == 1
    assert duration.hours == 0

    duration = Duration("1:23:45")
    assert duration.seconds == 45
    assert duration.minutes == 23
    assert duration.hours == 1


def test_duration_from_kwargs():
    duration = Duration(minutes=1, seconds=23)
    assert duration.seconds == 23
    assert duration.minutes == 1
    assert duration.hours == 0

    duration = Duration(hours=1, minutes=23, seconds=45)
    assert duration.seconds == 45
    assert duration.minutes == 23
    assert duration.hours == 1


def test_duration_from_dt():
    duration = Duration(datetime.timedelta(minutes=1, seconds=23))
    assert duration.seconds == 23
    assert duration.minutes == 1
    assert duration.hours == 0

    duration = Duration(datetime.timedelta(hours=1, minutes=23, seconds=45))
    assert duration.seconds == 45
    assert duration.minutes == 23
    assert duration.hours == 1


def test_duration_from_int():
    duration = Duration(5025)  # int == 1*3600 + 23*60 + 45 seconds
    assert duration.seconds == 45
    assert duration.minutes == 23
    assert duration.hours == 1
