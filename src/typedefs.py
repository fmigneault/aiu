from typing import AnyStr, Dict, List, Union, TYPE_CHECKING
from datetime import date, time

if TYPE_CHECKING:
    import eyed3
    AudioTagDict = Dict[AnyStr, Union[AnyStr, int]]
    AudioFile = eyed3.core.AudioFile
    AudioFileAny = Union[AnyStr, AudioFile]
    AudioField = Union[None, int, AnyStr, date, time]
    AudioConfig = List[Dict[AnyStr, AudioField]]
