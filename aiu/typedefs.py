"""
Audio field and container type definitions.
"""

import datetime
import logging
import os
import shutil
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    Type,
    Union,
)
from typing_extensions import TypeAlias

import eyed3
from eyed3.id3.tag import Tag
from PIL import Image

from aiu import tags as t
from aiu.clean import beautify_string

LoggerType = logging.Logger

if TYPE_CHECKING:
    # pylint: disable=invalid-name

    from io import FileIO

    Number = Union[int, float]
    ValueType = Union[str, Number, bool]
    AnyValue = Optional[ValueType]
    _JSON: TypeAlias = "JSON"
    JsonObjectItem = Dict[str, _JSON]
    JsonListItem = List[_JSON]
    JsonItem = Union[AnyValue, _JSON]
    JSON = Union[Dict[str, JsonItem], List[JsonItem]]


class FormatInfo(object):
    """
    Format information container for parsing and input/output of metadata config files.
    """

    __slots__ = ["_name", "_ext"]

    def __init__(self, name, extensions):
        # type: (str, Union[str, List[str]]) -> None
        """
        :param name: identifier of the format type.
        :param extensions: supported extension(s) corresponding to this format. First one is the `default`.
        """
        self._name = name
        self._ext = [extensions] if isinstance(extensions, str) else list(extensions)

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
    """
    General functionalities and properties for audio file metadata fields.
    """
    _raw = None
    _value = None
    _field = None

    def __init__(self, *_, field=None, **__):
        if isinstance(field, property):
            self._field = field.fget.__name__
        else:
            self._field = field

    def __eq__(self, other):
        if isinstance(other, BaseField):
            return self._value == other._value  # pylint: disable=protected-member
        if isinstance(other, type(self._value)):
            return self._value == other
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __get__(self, instance, owner):
        return self._value

    @property
    def raw(self):
        """
        Represents the initial value provided on initialization, before any *possible* modification.
        """
        return self._raw

    @property
    def value(self):
        """
        Represents the stored value updated as required by various conditions of the class.
        """
        return self._value or self.raw

    @property
    def field(self):
        """
        Name of the real ID3 tag to update using :mod:`eyeD3` package.
        """
        return self._field


Date = datetime.date
AnyDuration = Union["Duration", datetime.timedelta, str, int]


class Duration(BaseField, datetime.timedelta):
    """
    Audio duration representation.

    Instantiation examples::

        Duration("1:23")
        Duration("1:23:45")
        Duration(minutes=1, seconds=23)
        Duration(hours=1, minutes=23, seconds=45)
        Duration(datetime.timedelta(hours=1, minutes=23, seconds=45))
        Duration(5025)  # int == 1*3600 + 23*60 + 45 seconds
    """
    def __new__(  # pylint: disable=signature-differs,keyword-arg-before-vararg
        cls: Type["Duration"],
        duration: Optional[AnyDuration] = None,
        *_: Any,
        **kwargs: Any,
    ) -> "Duration":
        if isinstance(duration, str):
            time_parts = duration.replace("-", ":").replace("/", ":").split(":")
            h, m, s = [""] + time_parts if len(time_parts) == 2 else time_parts
            h = int(h) if h else 0
            m = int(m) if m else 0
            s = int(s) if s else 0
            for kw in ["hours", "minutes", "seconds"]:
                kwargs.pop(kw, None)
            d = super(Duration, cls).__new__(cls, hours=h, minutes=m, seconds=s, **kwargs)
            d.__init__(**kwargs)
            d._raw = duration
            return d
        if isinstance(duration, int):
            d = Duration(datetime.timedelta(seconds=duration), **kwargs)
            d._raw = duration
            return d
        if duration is None:
            h = kwargs.pop("hours", 0)
            m = kwargs.pop("minutes", 0)
            s = kwargs.pop("seconds", 0)
            d = super(Duration, cls).__new__(cls, hours=h, minutes=m, seconds=s, **kwargs)
            d.__init__(**kwargs)
            d._raw = kwargs
            return d
        if isinstance(duration, datetime.timedelta):
            h, r = divmod(duration.total_seconds(), 3600)
            m, s = divmod(r, 60)
            for kw in ["hours", "minutes", "seconds"]:
                kwargs.pop(kw, None)
            d = Duration(hours=h, minutes=m, seconds=s, **kwargs)
            d.__init__(**kwargs)
            d._raw = duration
            return d
        raise ValueError(f"invalid value [{duration!s}] for [{cls.__name__}]")

    def __add__(self, other):
        return super(Duration, self).__add__(other)

    def __str__(self):
        """
        Display the time as `MM:SS` if less than 1H or `<H>:MM:SS` otherwise, where `<H>` is an N digit number
        representing the total amount of hours.
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
        """
        Hours part of the duration.
        """
        return self._sec // 3600

    @property
    def minutes(self):
        # type: (...) -> int
        """
        Minutes part of the duration.
        """
        return self._sec % 3600 // 60

    @property
    def seconds(self):
        # type: (...) -> int
        """
        Seconds part of the duration.
        """
        return self._sec % 3600 % 60


# interfaces order important, inherit `BaseField` implementations before sub-type implementations
class StrField(BaseField, str):
    """
    String field representation with optional beautification.
    """
    def __new__(cls, value, *_, allow_none=True, beautify=False, **__):
        # type: (StrField, Optional[str], *Any, bool, bool, **Any) -> StrField
        value = str(value)
        field = super(StrField, cls).__new__(cls, value)  # type: BaseField
        field.__init__(*_, **__)
        field._allow_none = allow_none
        field._beautify = beautify
        field.__set__(field, value)  # pylint: disable=no-member
        return field

    def __str__(self):
        # type: (...) -> str
        return self._value if self._value else ""

    def __repr__(self):
        return str(self._value)

    def __set__(self, instance, value):
        # type: (StrField, Optional[str]) -> None
        if not (isinstance(value, str) or (self._allow_none and value is None)):
            raise ValueError(f"invalid value [{value!s}] for [{type(self).__name__}]")
        self._raw = value
        if self._beautify and isinstance(value, str):
            value = beautify_string(value)
        self._value = value


# interfaces order important, inherit `BaseField` implementations before sub-type implementations
class IntField(int, BaseField):
    """
    Integer field representation.
    """
    _value = None
    _is_none = True

    def __new__(cls, value, *_, allow_none=True, **__):
        # type: (IntField, Union[str, int, None], *Any, bool, **Any) -> IntField
        field = super(IntField, cls).__new__(cls, value or 0)
        field.__init__(*_, **__)
        field._allow_none = allow_none
        field.__set__(field, value)
        return field

    def __str__(self, digit_count=None):
        # type: (Optional[int]) -> str
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
        # type: (...) -> Optional[str]
        return None if self._is_none else self._value

    def __set__(self, instance, value):
        self._raw = value
        self._is_none = value is None
        if isinstance(value, str):
            try:
                value = int(value)
            except ValueError as ex:
                raise ValueError(str(ex).replace("int()", f"{type(self).__name__}()"))
        if not (isinstance(value, int) or (self._allow_none and self._is_none)):
            raise ValueError(f"invalid value [{value!s}] for [{type(self).__name__}]")
        self._value = value

    @property
    def value(self):
        return None if self._is_none else int(self)


CoverFileRaw = Union[Image.Image]
CoverFileAny = Union[str, CoverFileRaw, "CoverFile"]


class CoverFile(BaseField):
    """
    Field for the album image cover file.
    """
    __slots__ = ["_name", "_path", "_link", "_image"]

    def __init__(self, image, *_, **__):
        # type: (CoverFileAny, *Any, **Any) -> None
        from aiu.parser import fetch_image  # pylint: disable=import-outside-toplevel

        super(CoverFile, self).__init__(*_, **__)
        self._raw = image
        self._link = None
        self._path = None
        self._image = None
        if isinstance(image, str):
            if image.startswith("http"):
                self._link = image
                image = fetch_image(image)
            self._name = os.path.split(image)[-1]
            self._path = image
        elif isinstance(image, Image.Image):
            self._image = image
            image_path_ptr = getattr(image, "fp", None)  # type: Optional[FileIO]
            if image_path_ptr:
                self._path = image_path_ptr.name
                self._name = os.path.split(self._path)[-1]
            else:
                self._name = "cover.png"
        else:
            raise ValueError(f"invalid value [{image!s}] for [{type(self).__name__}]")

    @property
    def image(self):
        if self._image:
            return self._image
        self._image = Image.open(self._path)
        return self._image

    @property
    def path(self):
        return self._path

    @property
    def name(self):
        return self._name

    def save(self, path):
        if self._path:
            shutil.copyfile(self._path, path)
        else:
            self._image.save(path)

    def __str__(self):
        return self._name


AudioTagDict = Dict[str, Union[str, int]]
AudioFile: TypeAlias = eyed3.core.AudioFile
AudioFileAny = Union[str, AudioFile]
AudioField = Union[None, int, str, StrField, Date, Duration, CoverFile]


class AudioInfo(dict):
    """
    Represents an audio file information container, each field corresponding to some details as represented in a
    configuration file row.
    """
    __slots__ = ["_beautify"]
    __fields__ = set(t.TAGS) | {"file", "cover"}

    def __init__(self, *args, title=None, beautify=False, **kwargs):
        # type: (Tuple[str, AudioField], Optional[Union[str, StrField]], bool, BaseField) -> None
        super(AudioInfo, self).__init__()
        self._beautify = beautify
        title = title or kwargs.pop(t.TAG_TITLE, None)
        if title:  # none not allowed
            self.title = title
        if args:
            for k, v in args:
                self.set_field(k, v, validate=False)
        for kw, val in kwargs.items():
            self.set_field(kw, val, validate=False)

    def set_field(self, key, value, validate=True):
        # if the field has an explicit property (custom handling/typing), apply it
        if hasattr(self, key):
            self.__setattr__(key, value)
        # otherwise, use the default str format
        elif key in type(self).__fields__:
            self[key] = StrField(value, allow_none=True, beautify=self._beautify, field=getattr(Tag, key, None))
        elif validate:
            raise KeyError(f"Invalid tag field is unknown: [{key}] ({value})")

    def __str__(self):
        cls_str = type(self).__name__
        trk_str = f"{self.track}. " if self.track else ""
        dur_str = f" - {self.duration}" if self.duration else ""
        return f"{cls_str}({trk_str}{self.title}{dur_str})"

    @property
    def __dict__(self):
        return dict(self)   # need to do this because of __slots__

    @property
    def value(self):
        # type: () -> JSON
        """
        Literal Python value representation for all audio info fields.
        """
        return {k: v.value for k, v in self.items()}

    def _get_title(self):
        # type: () -> Optional[StrField]
        return self.get(t.TAG_TITLE)

    def _set_title(self, title):
        # type: (str) -> None
        self[t.TAG_TITLE] = StrField(title, allow_none=False, beautify=self._beautify, field=Tag.title)

    title = property(_get_title, _set_title)

    def _get_artist(self):
        # type: () -> Optional[StrField]
        return self.get(t.TAG_ARTIST)

    def _set_artist(self, artist):
        # type: (str) -> None
        self[t.TAG_ARTIST] = StrField(artist, allow_none=False, beautify=self._beautify, field=Tag.artist)

    artist = property(_get_artist, _set_artist)

    def _get_album_artist(self):
        # type: () -> Optional[StrField]
        return self.get(t.TAG_ALBUM_ARTIST)

    def _set_album_artist(self, artist):
        # type: (str) -> None
        self[t.TAG_ALBUM_ARTIST] = StrField(artist, allow_none=False, beautify=self._beautify, field=Tag.album_artist)

    album_artist = property(_get_album_artist, _set_album_artist)

    def _get_track(self):
        # type: () -> Optional[IntField]
        return self.get(t.TAG_TRACK)

    def _set_track(self, track):
        # type: (Optional[int]) -> None
        if isinstance(track, int) and track < 1 or track in ["", None]:
            track = None  # unset track number
        self[t.TAG_TRACK] = IntField(track, field=Tag.track_num, allow_none=True)

    track = property(_get_track, _set_track)

    def _get_cover(self):
        # type: () -> Union[CoverFile, None]
        return self.get("cover")

    def _set_cover(self, cover):
        # type: (CoverFileAny) -> None
        self["cover"] = cover if isinstance(cover, CoverFile) else CoverFile(cover)

    cover = property(_get_cover, _set_cover)

    def _get_duration(self):
        # type: () -> Optional[Duration]
        return self.get(t.TAG_DURATION)

    def _set_duration(self, duration):
        # type: (Union[str, Duration]) -> None
        self[t.TAG_DURATION] = Duration(duration)

    duration = property(_get_duration, _set_duration)

    def _get_year(self):
        # type: () -> Optional[int]
        return self.get(t.TAG_YEAR)

    def _set_year(self, year):
        # type: (Optional[Union[str, int]]) -> None
        self[t.TAG_YEAR] = IntField(year, allow_none=True)

    year = property(_get_year, _set_year)

    def _get_file(self):
        # type: () -> Optional[str]
        return self.get("file", None)

    def _set_file(self, file):
        # type: (Optional[str]) -> None
        self["file"] = StrField(file, allow_none=True)

    file = property(_get_file, _set_file)


AnyAudioSpec = Union[AudioInfo, Iterable[AudioInfo], Dict[str, AudioField], Iterable[Dict[str, AudioField]]]


class AudioConfig(List[AudioInfo]):
    """
    Represents a set of :class:`AudioInfo`, similarly to each row of a configuration file each representing and audio
    file definition and fields.
    """

    def __init__(self, raw_config=None, shared=False, beautify=False):
        # type: (AnyAudioSpec, bool, bool) -> None
        self._shared = shared
        if not raw_config:
            config = {}
        else:
            if isinstance(raw_config, dict):
                raw_config = [raw_config]
            if not all(isinstance(c, dict) for c in raw_config):
                raise TypeError("Invalid audio information must be dict-like.")
            config = [
                cfg
                if isinstance(cfg, AudioInfo) and not beautify else
                AudioInfo(**cfg, beautify=beautify)
                for cfg in raw_config
            ]
        super(AudioConfig, self).__init__(config)

    @property
    def value(self):
        # type: () -> List[JSON]
        """
        Literal Python value representation for all audio info entries.
        """
        return [info.value for info in self]

    @property
    def shared(self):
        # type: () -> bool
        """
        Indicates if the contained audio configuration corresponds to a shared definition across audio information list.
        """
        return self._shared

    def beautify(self):
        # type: () -> AudioConfig
        """
        Apply field beautification operations to all underlying audio information.

        Generates an alternate representation of this audio configuration with beautification properties applied
        such that the original audio configuration remains available, and that multiple beautification variants
        can be generated by adjusting the applicable application configuration properties before each invocation.
        """
        return AudioConfig([AudioInfo(**info, beautify=True) for info in self])
