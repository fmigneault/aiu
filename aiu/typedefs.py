from typing import AnyStr, Dict, List, Optional, Union
from PIL import Image, ImageFile
from slugify import slugify
import datetime
import eyed3
import six


class FormatInfo(object):
    """Format information container for parsing and input/output of metadata config files."""
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
    def extension(self):
        return self._ext[0]

    def matches(self, extension):
        return extension in self._ext


class Duration(datetime.timedelta):
    def __init__(self, duration=None, **kwargs):
        if isinstance(duration, six.string_types):
            time_parts = duration.replace('-', ':').replace('/', ':').split(':')
            h, m, s = [None] + time_parts if len(time_parts) == 2 else time_parts
            self.__init__(hours=h, minutes=m, seconds=s)
        elif isinstance(duration, datetime.timedelta):
            super(Duration, self).__init__(**kwargs)
        else:
            raise ValueError("invalid value [{!s}] for {}".format(duration, self.__name__))

    def __str__(self):
        """
        Display the time as `MM:SS` if less than 1H or `<H>:MM:SS` otherwise,
        where `<H>` is a N digit number representing the total amount of hours.
        """
        s = super(Duration, self).__str__()
        return s if self.seconds >= 3600 else s[2:]


Date = datetime.date


class StingField(object):
    def __init__(self, value, allow_none=True):
        # type: (Union[AnyStr, None], Optional[bool]) -> None
        self._allow_none = allow_none
        self.__set__(self, value)

    def __str__(self):
        # type: (...) -> AnyStr
        return self._value if self._value else ''

    def __get__(self, instance, owner):
        # type: (...) -> Union[AnyStr, None]
        return self._value

    def __set__(self, instance, value):
        if not isinstance(value, six.string_types) or (self._allow_none and value is None):
            raise ValueError("invalid value [{!s}] for {}".format(value, self.__name__))
        self._value = value


CoverFileRaw = Union[Image.Image]
CoverFileAny = Union[AnyStr, CoverFileRaw]


class CoverFile(object):
    def __init__(self, image):
        # type: (CoverFileAny) -> None
        if isinstance(image, six.string_types):
            self._cover = ImageFile.ImageFile(image)
            self._name = slugify(image)
        elif isinstance(image, Image.Image):
            self._cover = image
            self._name = 'cover.jpg'
        else:
            raise ValueError("invalid value [{!s}] for {}".format(image, self.__name__))

    def __str__(self):
        return self._name


AudioTagDict = Dict[AnyStr, Union[AnyStr, int]]
AudioFile = eyed3.core.AudioFile
AudioFileAny = Union[AnyStr, AudioFile]
AudioField = Union[None, int, StingField, Date, Duration, CoverFile]


class AudioInfo(dict):
    def __init__(self, title, **kwargs):
        super(AudioInfo, self).__init__()
        self.title = title or kwargs.pop('title', None)
        for kw in kwargs:
            self.__setattr__(kw, kwargs[kw])

    def _get_title(self):
        return self['title']

    def _set_title(self, title):
        # type: (AnyStr) -> None
        self['title'] = StingField(title, allow_none=False)

    title = property(_get_title, _set_title)

    def _get_track(self):
        return self['track']

    def _set_track(self, track):
        self['track'] = StingField(track)

    track = property(_get_track, _set_track)

    def _get_cover(self):
        # type: (...) -> Union[CoverFile, None]
        return self['cover']

    def _set_cover(self, cover):
        # type: (CoverFileAny) -> None
        self['cover'] = CoverFile(cover)

    cover = property(_get_cover, _set_cover)

    def _get_duration(self):
        # type: (...) -> Union[Duration, None]
        return self['duration']

    def _set_duration(self, duration):
        # type: (Union[AnyStr, Duration]) -> None
        self['duration'] = Duration(duration)

    duration = property(_get_duration, _set_duration)


class AudioConfig(list):
    def __init__(self, raw_config):
        # type: (Union[AudioInfo, List[AudioInfo], Dict[AnyStr, AudioField], List[Dict[AnyStr, AudioField]]]) -> None
        if not isinstance(raw_config, list):
            raw_config = [raw_config]
        config = [AudioInfo(cfg) for cfg in raw_config]
        super(AudioConfig, self).__init__(config)
