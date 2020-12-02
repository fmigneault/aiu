from aiu.typedefs import Duration
import datetime


def test_duration_from_str():
    d = Duration("1:23")
    assert d.seconds == 23
    assert d.minutes == 1
    assert d.hours == 0

    d = Duration("1:23:45")
    assert d.seconds == 45
    assert d.minutes == 23
    assert d.hours == 1


def test_duration_from_kwargs():
    d = Duration(minutes=1, seconds=23)
    assert d.seconds == 23
    assert d.minutes == 1
    assert d.hours == 0

    d = Duration(hours=1, minutes=23, seconds=45)
    assert d.seconds == 45
    assert d.minutes == 23
    assert d.hours == 1


def test_duration_from_dt():
    d = Duration(datetime.timedelta(minutes=1, seconds=23))
    assert d.seconds == 23
    assert d.minutes == 1
    assert d.hours == 0

    d = Duration(datetime.timedelta(hours=1, minutes=23, seconds=45))
    assert d.seconds == 45
    assert d.minutes == 23
    assert d.hours == 1


def test_duration_from_int():
    d = Duration(5025)  # int == 1*3600 + 23*60 + 45 seconds
    assert d.seconds == 45
    assert d.minutes == 23
    assert d.hours == 1
