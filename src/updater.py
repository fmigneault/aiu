import warnings
import eyed3
import six

from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from miu.types import AudioFile, AudioFileAny, AudioTagDict


def update_audio_tags(audio_file, audio_tags, overwrite=False):
    # type: (AudioFileAny, AudioTagDict, Optional[bool]) -> AudioFile
    """Updates the audio file using provided audio tags."""
    if isinstance(audio_file, six.string_types):
        audio_file = eyed3.load(audio_file)
    if not isinstance(audio_file, AudioFile):
        raise TypeError("Audio file expected.")
    if not isinstance(audio_tags, AudioTagDict):
        raise TypeError("Audio tag dict expected.")

    for tag, value in audio_tags:
        if not hasattr(audio_file, tag):
            warnings.warn("unknown tag '{}'".format(tag))    
            continue
        if not overwrite and getattr(audio_file.tag, tag) is not None:
            warnings.warn("tag '{}' already set".format(tag))    
            continue
        setattr(audio_file.tag, tag, value)
    audio_file.save()
