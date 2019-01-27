from aiu.typedefs import AudioConfig, AudioFile, AudioFileAny, AudioTagDict, CoverFileAny
from aiu.utils import get_audio_file, get_cover_file, get_logger
from typing import Iterable, Optional, Tuple

LOGGER = get_logger()


def merge_audio_configs(configs):
    # type: (Iterable[Tuple[AudioConfig, bool]]) -> AudioConfig
    """
    Merge matching configuration fields into a single one.
    Matching of corresponding entries is accomplished using `title` field.
    Later config fields in the list override preceding ones if they are not empty or invalid.

    :param configs:
        list of metadata files to merge together with a `bool` associated to each one to indicate if their
        corresponding fields apply to `all` audio files (`True`) or individually (`False`).
    :return: merged config.
    """
    raise NotImplemented


def update_audio_tags(audio_file, audio_tags, overwrite=True):
    # type: (AudioFileAny, AudioTagDict, Optional[bool]) -> None
    """Updates the audio file using provided audio tags."""
    audio_file = get_audio_file(audio_file)
    if not isinstance(audio_tags, AudioTagDict):
        raise TypeError("Audio tag dict expected.")

    for tag, value in audio_tags:
        if not hasattr(audio_file, tag):
            LOGGER.warning("unknown tag '{}'".format(tag))
            continue
        if not overwrite and getattr(audio_file.tag, tag) is not None:
            LOGGER.warning("tag '{}' already set".format(tag))
            continue
        setattr(audio_file.tag, tag, value)
    audio_file.save()


def update_cover_image(audio_file, cover_file, overwrite=True):
    # type: (AudioFileAny, CoverFileAny, Optional[bool]) -> None
    """Update the album cover tag of an audio file using the provided cover image file."""
    audio_file = get_audio_file(audio_file)
    cover_file = get_cover_file(cover_file)
    raise NotImplemented


def apply_audio_config(audio_files, audio_config):
    # type: (Iterable[AudioFile], AudioConfig) -> AudioConfig
    """
    Applies the metadata fields to the corresponding audio files.
    Matching is attempted first with file names, and other heuristics as required afterward.
    """
    raise NotImplemented
