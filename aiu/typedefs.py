from typing import AnyStr, Dict, List, Union
from datetime import date, timedelta
from PIL.Image import Image
import eyed3


class Duration(timedelta):
    def __str__(self):
        """
        Display the time as `MM:SS` if less than 1H or `<H>:MM:SS` otherwise,
        where `<H>` is a N digit number representing the total amount of hours.
        """
        s = super(Duration, self).__str__()
        return s if self.seconds >= 3600 else s[2:]


AudioTagDict = Dict[AnyStr, Union[AnyStr, int]]
AudioFile = eyed3.core.AudioFile
AudioFileAny = Union[AnyStr, AudioFile]
AudioField = Union[None, int, AnyStr, date, Duration]
AudioConfig = List[Dict[AnyStr, AudioField]]

CoverFile = Union[Image]
CoverFileAny = Union[AnyStr, CoverFile]
