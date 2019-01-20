from typing import AnyStr, Dict, Union, TYPE_CHECKING

if TYPE_CHECKING:
    import eyed3
    AudioTagDict = Dict[AnyStr, Union[AnyStr, int]]
    AudioFile = eyed3.core.AudioFile
    AudioFileAny = Union[AnyStr, AudioFile]
