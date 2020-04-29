from aiu.typedefs import AudioConfig, AudioFile, AudioFileAny, AudioInfo, AudioTagDict, CoverFileAny
from aiu.utils import get_audio_file, get_cover_file, get_logger, slugify_file_name
from typing import Iterable, Optional, Tuple
import eyed3
import os

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
                merged_config.extend(cfg[1])
            elif cfg_size == 1:
                merged_config.extend([cfg[1] for _ in range(max_audio_count)])
            else:
                raise ValueError("Cannot initialize audio config with [total = {}] and first config [size = {}]. "
                                 "First config must be [total = size] or [size = 1]".format(max_audio_count, cfg_size))
        else:
            # following configs updates the first as required
            if cfg_size != max_audio_count:
                # FIXME: not implemented
                pass


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
    # type: (Iterable[str], AudioConfig, Optional[str]) -> AudioConfig
    """
    Applies the metadata fields to the corresponding audio files.
    Matching is attempted first with file names, and other heuristics as required afterward.
    """
    for file_path in audio_files:
        file_dir, file_name = os.path.split(file_path)
        matched_info = None
        for audio_info in audio_config:     # type: AudioInfo
            if audio_info.title.lower() in file_name.lower():
                matched_info = audio_info
                break

        if matched_info:
            LOGGER.debug("Matched file [%s] with [%s]", file_path, matched_info)
            if matched_info.file:
                LOGGER.warning("[%s] already matched with [%s], skipping...", matched_info, matched_info.file)
                continue
            matched_info.file = file_path
            audio_file = get_audio_file(file_path)
            for tag_name, tag_value in audio_info.items():
                setattr(audio_file.tag, tag_name, tag_value)
            audio_file.tag.save()
        else:
            LOGGER.warning("No audio information was matched for file: [%s]", file_path)

    return audio_config  # FIXME: should return applied with respect to saved audio file tags


def update_file_names(audio_config, rename_title, rename_format, prefix_track):
    # type: (AudioConfig, bool, bool, Optional[str]) -> AudioConfig
    """
    Renames the files and updates the configuration according to specified formats.
    """
    if not audio_config:
        LOGGER.error("No configuration to process!")
        return audio_config
    if rename_title:
        if prefix_track:
            LOGGER.debug("Updating rename format with title and prefix.")
            rename_format = "%(TRACK)s %(TITLE)s"
        else:
            LOGGER.debug("Updating rename format with title only.")
            rename_format = "%(TITLE)s"
    elif not rename_format or "%(" not in rename_format or ")" not in rename_format:
        LOGGER.error("No format or template variable specified!")
    for audio_item in audio_config:  # type: AudioInfo
        if audio_item.file:
            if not os.path.isfile(audio_item.file):
                LOGGER.error("Invalid file value cannot be found: [%s]", audio_item.file)
                continue
            rename_name = rename_format.lower() % audio_item
            rename_name = slugify_file_name(rename_name)
            rename_path, origin_name = os.path.split(audio_item.file)
            origin_name, origin_ext = os.path.splitext(origin_name)
            rename_path = os.path.join(rename_path, rename_name + origin_ext)
            os.rename(audio_item.file, rename_path)
            audio_item.file = rename_path
            LOGGER.info("Renamed file: [%s] => [%s]", origin_name, rename_name)
    return audio_config
