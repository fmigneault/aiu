from aiu.clean import beautify_string
from typing import Any, AnyStr, Dict, List, Optional, Union
from PIL import Image, ImageFile
from slugify import slugify
from eyed3.id3.tag import Tag
import eyed3
import logging
import datetime
import six

LoggerType = logging.Logger


class FormatInfo(object):
    """Format information container for parsing and input/output of metadata config files."""

    __slots__ = ["_name", "_ext"]

    def __init__(self, name, extensions):
        # type: (AnyStr, Union[AnyStr, List[AnyStr]]) -> None
        """
        :param name: identifier of the format type.
        :param extensions: supported extension(s) corresponding to this format. First one is the `default`.
        """
        self._name = name
        self._ext = [extensions] if isinstance(extensions, six.string_types) else list(extensions)

    def __str__(self):
        return self.name

    @property
    def name(self):
        return self._name

    @property
    def extensions(self):
        return self._ext

    def matches(self, extension):
        return extension in self._ext


class BaseField(object):
    __slots__ = ["_raw", "_value", "_field"]

    def __init__(self, field=None, *_, **__):
        if isinstance(field, property):
            self._field = field.fget.__name__
        else:
            self._field = field

    # def __new__(cls, field=None):
    #     obj = super().__new__()
    #     if isinstance(field, property):
    #         obj._field = field.fget.__name__
    #     else:
    #         obj._field = field
    #     return obj

    def __eq__(self, other):
        if isinstance(other, BaseField):
            return self._value == other._value
        if isinstance(other, type(self._value)):
            return self._value == other
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __get__(self, instance, owner):
        return self._value

    @property
    def raw(self):
        """Represents the initial value provided on initialization, before any *possible* modification."""
        return self._raw

    @property
    def value(self):
        """Represents the stored value updated as required by various conditions of the class."""
        return self._value or self.raw

    @property
    def field(self):
        """Name of the real ID3 tag to update using :mod:`eyeD3` package."""
        return self._field


class Duration(BaseField, datetime.timedelta):
    """Audio duration representation.

    Instantiation examples::

        Duration("1:23")
        Duration("1:23:45")
        Duration(minutes=1, seconds=23)
        Duration(hours=1, minutes=23, seconds=45)
        Duration(datetime.timedelta(hours=1, minutes=23, seconds=45))
        Duration(5025)  # int == 1*3600 + 23*60 + 45 seconds
    """
    def __new__(cls, duration=None, **kwargs):
        if isinstance(duration, six.string_types):
            time_parts = duration.replace("-", ":").replace("/", ":").split(":")
            h, m, s = [None] + time_parts if len(time_parts) == 2 else time_parts
            h = int(h) if h is not None else 0
            m = int(m) if m is not None else 0
            s = int(s) if s is not None else 0
            for kw in ["hours", "minutes", "seconds"]:
                kwargs.pop(kw, None)
            d = super(Duration, cls).__new__(cls, hours=h, minutes=m, seconds=s, **kwargs)
            d._raw = duration
            return d
        elif isinstance(duration, int):
            d = Duration(datetime.timedelta(seconds=duration), **kwargs)
            d._raw = duration
            return d
        elif duration is None:
            h = kwargs.pop("hours", 0)
            m = kwargs.pop("minutes", 0)
            s = kwargs.pop("seconds", 0)
            d = super(Duration, cls).__new__(cls, hours=h, minutes=m, seconds=s, **kwargs)
            d._raw = kwargs
            return d
        elif isinstance(duration, datetime.timedelta):
            h, r = divmod(duration.total_seconds(), 3600)
            m, s = divmod(r, 60)
            for kw in ["hours", "minutes", "seconds"]:
                kwargs.pop(kw, None)
            d = Duration(hours=h, minutes=m, seconds=s, **kwargs)
            d._raw = duration
            return d
        raise ValueError("invalid value [{!s}] for [{}]".format(duration, cls.__name__))

    def __add__(self, other):
        return super(Duration, self).__add__(other)

    def __str__(self):
        """
        Display the time as `MM:SS` if less than 1H or `<H>:MM:SS` otherwise,
        where `<H>` is a N digit number representing the total amount of hours.
        """
        s = super(Duration, self).__str__()
        return s if self._sec >= 3600 else s[2:]

    @property
    def value(self):
        return str(self)

    @property
    def _sec(self):
        return super(Duration, self).seconds

    @property
    def hours(self):
        # type: (...) -> int
        """Hours part of the duration."""
        return self._sec // 3600

    @property
    def minutes(self):
        # type: (...) -> int
        """Minutes part of the duration."""
        return self._sec % 3600 // 60

    @property
    def seconds(self):
        # type: (...) -> int
        """Seconds part of the duration."""
        return self._sec % 3600 % 60


Date = datetime.date


# interfaces order important, inherit `BaseField` implementations before sub-type implementations
class StrField(BaseField, str):
    def __new__(cls, value, allow_none=True, beautify=False, *_, **__):
        # type: (StrField, Union[AnyStr, None], Optional[bool], Optional[bool], Any, Any) -> StrField
        field = super(StrField, cls).__new__(cls, value, *_, **__)
        field._allow_none = allow_none
        field._beautify = beautify
        field.__set__(field, value)
        return field

    def __str__(self):
        # type: (...) -> AnyStr
        return self._value if self._value else ""

    def __repr__(self):
        return str(self._value)

    def __set__(self, instance, value):
        # type: (StrField, Union[None, AnyStr]) -> None
        if not (isinstance(value, six.string_types) or (self._allow_none and value is None)):
            raise ValueError("invalid value [{!s}] for [{}]".format(value, type(self).__name__))
        self._raw = value
        if self._beautify and isinstance(value, six.string_types):
            # noinspection PyTypeChecker
            value = beautify_string(value)
        self._value = value


# interfaces order important, inherit `BaseField` implementations before sub-type implementations
class IntField(int, BaseField):
    _value = None
    _is_none = True

    def __new__(cls, value, allow_none=True, *_, **__):
        # type: (IntField, Union[AnyStr, None], Optional[bool], Any, Any) -> IntField
        field = super(IntField, cls).__new__(cls, value or 0, *_, **__)
        field._allow_none = allow_none
        field.__set__(field, value)
        return field

    def __str__(self, digit_count=None):
        # type: (Optional[int]) -> AnyStr
        if self._is_none:
            return ""
        int_str = super(IntField, self).__str__()
        return int_str.zfill(digit_count) if digit_count else int_str

    def __eq__(self, other):
        # type: (...) -> bool
        return self.__get__(self, self) == other

    def __ne__(self, other):
        # type: (...) -> bool
        return not self.__eq__(other)

    def __get__(self, instance, owner):
        # type: (...) -> Union[AnyStr, None]
        return None if self._is_none else self._value

    def __set__(self, instance, value):
        self._raw = value
        self._is_none = value is None
        if isinstance(value, six.string_types):
            try:
                value = int(value)
            except ValueError as ex:
                raise ValueError(str(ex).replace("int()", "{}()".format(type(self).__name__)))
        if not (isinstance(value, int) or (self._allow_none and self._is_none)):
            raise ValueError("invalid value [{!s}] for [{}]".format(value, type(self).__name__))
        self._value = value

    @property
    def value(self):
        return None if self._is_none else int(self)


CoverFileRaw = Union[Image.Image]
CoverFileAny = Union[AnyStr, CoverFileRaw]


class CoverFile(BaseField):
    __slots__ = ["_cover", "_name"]

    def __init__(self, image, *_, **__):
        # type: (CoverFileAny, Any, Any) -> None
        super(CoverFile, self).__init__(*_, **__)
        self._raw = image
        if isinstance(image, six.string_types):
            self._cover = ImageFile.ImageFile(image)
            self._name = slugify(image)
        elif isinstance(image, Image.Image):
            self._cover = image
            self._name = "cover.jpg"
        else:
            raise ValueError("invalid value [{!s}] for [{}]".format(image, type(self).__name__))

    def __str__(self):
        return self._name


AudioTagDict = Dict[AnyStr, Union[AnyStr, int]]
AudioFile = eyed3.core.AudioFile
AudioFileAny = Union[AnyStr, AudioFile]
AudioField = Union[None, int, StrField, Date, Duration, CoverFile]


class AudioInfo(dict):
    """
    Represents an audio file information container, each field corresponding to some details as represented
    in a configuration file row.
    """
    __slots__ = ["_beautify"]

    def __init__(self, title, **kwargs):
        super(AudioInfo, self).__init__()
        self._beautify = kwargs.pop("beautify", True)
        self.title = title or kwargs.pop("title", None)
        for kw in kwargs:
            self.__setattr__(kw, kwargs[kw])

    def __str__(self):
        cls_str = type(self).__name__
        trk_str = "{}. ".format(self.track) if self.track else ""
        dur_str = " - {}".format(self.duration) if self.duration else ""
        return "{}({}{}{})".format(cls_str, trk_str, self.title, dur_str)

    @property
    def __dict__(self):
        return dict(self)   # need to do this because of __slots__

    @property
    def value(self):
        """Literal Python value representation for all audio info fields."""
        return {k: v.value for k, v in self.items()}

    def _get_title(self):
        return self["title"]

    def _set_title(self, title):
        # type: (AnyStr) -> None
        self["title"] = StrField(title, allow_none=False, beautify=self._beautify, field=Tag.title)

    title = property(_get_title, _set_title)

    def _get_artist(self):
        return self["artist"]

    def _set_artist(self, artist):
        # type: (AnyStr) -> None
        self["artist"] = StrField(artist, allow_none=False, beautify=self._beautify, field=Tag.artist)

    artist = property(_get_artist, _set_artist)

    def _get_track(self):
        return self["track"]

    def _set_track(self, track):
        self["track"] = IntField(track, field=Tag.track_num)

    track = property(_get_track, _set_track)

    def _get_cover(self):
        # type: (...) -> Union[CoverFile, None]
        return self["cover"]

    def _set_cover(self, cover):
        # type: (CoverFileAny) -> None
        self["cover"] = CoverFile(cover)
        # FIXME: which field and how to set it?
        #   eyeD3.id3.Tag.images, eyeD3.id3.frames.ImageFrame (many types possible)

    cover = property(_get_cover, _set_cover)

    def _get_duration(self):
        # type: (...) -> Union[Duration, None]
        return self["duration"]

    def _set_duration(self, duration):
        # type: (Union[AnyStr, Duration]) -> None
        self["duration"] = Duration(duration)

    duration = property(_get_duration, _set_duration)

    def _get_file(self):
        # type: (...) -> Optional[AnyStr]
        return self.get("file", None)

    def _set_file(self, file):
        # type: (Optional[AnyStr]) -> None
        self["file"] = StrField(file, allow_none=True)

    file = property(_get_file, _set_file)


class AudioConfig(list):
    """
    Represents a set of :class:`AudioInfo`, similarly to each row of a configuration file each representing
    and audio file definition and fields.
    """
    def __init__(self, raw_config=None):
        # type: (Union[AudioInfo, List[AudioInfo], Dict[AnyStr, AudioField], List[Dict[AnyStr, AudioField]]]) -> None
        if not raw_config:
            config = {}
        else:
            if not isinstance(raw_config, (list, set)):
                raw_config = [raw_config]
            if not all(isinstance(c, dict) for c in raw_config):
                raise TypeError("Invalid audio information must be dict-like.")
            config = [AudioInfo(**cfg) for cfg in raw_config]
        super(AudioConfig, self).__init__(config)

    @property
    def value(self):
        """Literal Python value representation for all audio info entries."""
        return [ai.value for ai in self]
