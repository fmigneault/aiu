from aiu.typedefs import AudioConfig, AudioFile, AudioFileAny, AudioTagDict, CoverFileAny
from aiu.utils import get_audio_file, get_cover_file, get_logger
from typing import Iterable, Optional, Tuple

LOGGER = get_logger()


def merge_audio_configs(configs, match_artist=False):
    # type: (Iterable[Tuple[bool, AudioConfig]], Optional[bool]) -> AudioConfig
    """
    Merge matching audio info fields into a single one, for each :class:`AudioInfo` in resulting :class:`AudioConfig`.

    Lazy matching of corresponding entries in resulting :class:`AudioConfig` is accomplished using ``TAG_TITLE`` field.

    Later :class:`AudioInfo` fields in ``configs`` list override preceding ones if they are not empty or invalid.
    For this reason

    :param configs:
        list of metadata files to merge together with a `bool` associated to each one indicating if their
        corresponding fields apply to `all` audio files (`True`) or specifically to each index (`False`).
    :param match_artist:
        indicates if ``TAG_ALBUM_ARTIST`` should be set equal as ``TAG_ARTIST`` if missing.
    :return: merged config.
    """
    merged_config = AudioConfig()
    max_audio_count = max(len(cfg[1]) for cfg in configs)
    for i, cfg in enumerate(configs):
        cfg_size = len(cfg[1])
        if not i:
            # first config is written as is, or duplicated if unique
            if cfg_size == max_audio_count:
                merged_config.append(cfg[1])
            elif cfg_size == 1:
                merged_config.extend([cfg[1]] * max_audio_count)
            else:
                raise ValueError("Cannot initialize audio config with [total = {}] and first config [size = {}]. "
                                 "First config must be [total = size] or [size = 1]".format(max_audio_count, cfg_size))
        else:
            # following configs updates the first as required
            if cfg_size != max_audio_count:
                cfg_i =


                #for c in cfg[1]:
    return merged_config


def update_audio_tags(audio_file, audio_tags, overwrite=True):
    # type: (AudioFileAny, AudioTagDict, Optional[bool]) -> None
    """Updates the audio file using provided audio tags."""
    audio_file = get_audio_file(audio_file)
    if not isinstance(audio_tags, dict):
        raise TypeError("Audio tag dict expected.")

    for tag, value in audio_tags.items():
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
    raise NotImplementedError  # TODO


def apply_audio_config(audio_files, audio_config):
    # type: (Iterable[AudioFile], AudioConfig) -> AudioConfig
    """
    Applies the metadata fields to the corresponding audio files.
    Matching is attempted first with file names, and other heuristics as required afterward.
    """
    raise NotImplementedError  # TODO
