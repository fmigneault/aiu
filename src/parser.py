import os
from eyed3.mp3 import isMp3File
from typing import AnyStr, Iterable, TYPE_CHECKING
if TYPE_CHECKING:
    from miu.types import AudioFile


def get_audio_files(path):
    # type: (AnyStr) -> Iterable[AudioFile]
    """Retrieves all supported audio files from the specified path (file or directory)."""
    if not os.path.isdir(path):
        if os.path.isfile(path):
            path = [path]
        else:
            raise ValueError("invalid path: '{}'".format(path))

    return filter(isMp3File, path)
