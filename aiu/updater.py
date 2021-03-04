from aiu.typedefs import AudioConfig, AudioFile, AudioFileAny, AudioInfo, AudioTagDict, CoverFileAny
from aiu.utils import get_audio_file, get_cover_file
from aiu import LOGGER
from copy import deepcopy
from typing import Iterable, Optional, Tuple
from unicodedata import normalize
import eyed3
import os


ALL_IMAGE_EXTENSIONS = frozenset([".tif", ".png", ".jpg", ".jpeg"])


def merge_audio_configs(configs, match_artist, total_files, config_shared):
    # type: (Iterable[Tuple[bool, AudioConfig]], bool, int, bool) -> AudioConfig
    """
    Merge matching audio info fields into a single one, for each :class:`AudioInfo` in resulting :class:`AudioConfig`.

    Lazy matching of corresponding entries in resulting :class:`AudioConfig` is accomplished using ``TAG_TITLE`` field.

    Later :class:`AudioInfo` fields in ``configs`` list override preceding ones if they are not empty or invalid.
    For this reason

    :param configs:
        List of metadata configuration to merge together with a `bool` associated to each one indicating if their
        corresponding fields apply to `all` audio files (`True`) or specifically to each index (`False`).
    :param match_artist:
        Indicates if ``TAG_ALBUM_ARTIST`` should be set equal as ``TAG_ARTIST`` if missing.
    :param total_files:
        Indication of number of audio files to eventually process.
        Employed to expand the configurations if all combinations apply only to ``all`` audio files.
    :param config_shared:
        Indication whether the audio file configurations only correspond to ``all`` definitions.
        In this case, a special flag is set in the resulting merged configuration for later reference.
    :return: merged config.
    """
    max_audio_count = max(len(cfg[1]) for cfg in configs)
    if config_shared or all(cfg[0] for cfg in configs):
        max_audio_count = total_files
        config_shared = True
    else:
        max_audio_count = max(max_audio_count, total_files)
    merged_config = AudioConfig(shared=config_shared)
    for i, (cfg_all, cfg) in enumerate(configs):
        cfg_size = len(cfg)
        if not i:
            # first config is written as is, or duplicated if unique
            if cfg_size == max_audio_count:
                merged_config.extend(cfg)
            elif cfg_size == 1:
                merged_config.extend([deepcopy(cfg[0]) for _ in range(max_audio_count)])
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
    audio_file.tag.save()


def update_cover_image(audio_file, cover_file, overwrite=True):
    # type: (AudioFileAny, CoverFileAny, Optional[bool]) -> None
    """Update the album cover tag of an audio file using the provided cover image file."""
    audio_file = get_audio_file(audio_file)
    cover_file = get_cover_file(cover_file)
    raise NotImplementedError  # TODO


def apply_audio_config(audio_files, audio_config, dry=False):
    # type: (Iterable[str], AudioConfig, bool) -> AudioConfig
    """
    Applies the metadata fields to the corresponding audio files.
    Matching is attempted first with file names, and other heuristics as required afterward.
    """
    for i, file_path in enumerate(audio_files):
        file_dir, file_name = os.path.split(file_path)
        matched_info = None
        for audio_info in audio_config:
            if audio_config.shared:
                matched_info = audio_config[i]
                break
            elif audio_info.title.lower() in file_name.lower():
                matched_info = audio_info
                break

        if matched_info:
            LOGGER.debug("Matched file [%s] with [%s]", file_path, matched_info)
            if matched_info.file:
                LOGGER.warning("[%s] already matched with [%s], skipping...", matched_info, matched_info.file)
                continue
            matched_info.file = file_path
            audio_file = get_audio_file(file_path)
            for tag_name, tag in matched_info.items():
                if dry:
                    LOGGER.debug("Would apply tag [%s] to file [%s]", tag_name, file_path)
                    continue
                if tag.field is not None:
                    setattr(audio_file.tag, tag.field, tag.value)
            if dry:
                tag_info = list(sorted((k, v) for k, v in matched_info.items() if k not in ['file']))
                tag_info = [('file', matched_info.file)] + tag_info
                tags_value_list = '\n'.join('  {}: {}'.format(k, v) for k, v in tag_info)
                LOGGER.info("Would apply tag updates:\n%s", tags_value_list)
                continue
            audio_file.tag.save()
        else:
            LOGGER.warning("No audio information was matched for file: [%s]", file_path)

    return audio_config  # FIXME: should return applied with respect to saved audio file tags


def update_file_names(audio_config, rename_format, rename_title=False, prefix_track=False, dry=False):
    # type: (AudioConfig, Optional[str], bool, bool, bool) -> AudioConfig
    """
    Renames the files and updates the configuration according to specified formats.
    """
    if not audio_config:
        LOGGER.error("No configuration to process!")
        return audio_config
    if rename_title:
        if prefix_track:
            LOGGER.debug("Updating rename format with title and prefix.")
            track_digits = len(str(len(audio_config)))
            rename_format = "%(TRACK)0{}d %(TITLE)s".format(track_digits)
        else:
            LOGGER.debug("Updating rename format with title only.")
            rename_format = "%(TITLE)s"
    if not rename_format:
        LOGGER.warning("No rename format or rename flag specified. Not renaming anything.")
        return audio_config
    if "%(" not in rename_format or ")" not in rename_format:
        LOGGER.error("No rename format or template variable specified! Will not rename anything.")
        return audio_config
    for audio_item in audio_config:  # type: AudioInfo
        if audio_item.file:
            if not os.path.isfile(audio_item.file):
                LOGGER.error("Invalid file value cannot be found: [%s]", audio_item.file)
                continue
            rename_name = rename_format.lower() % audio_item
            rename_norm = normalize("NFKD", rename_name)
            LOGGER.debug("Before/after normalization: [%s] => [%s]", rename_name, rename_norm)
            rename_path, origin_name = os.path.split(audio_item.file)
            origin_name, origin_ext = os.path.splitext(origin_name)
            rename_path = os.path.join(rename_path, rename_norm + origin_ext)
            if dry:
                LOGGER.info("Would rename [%s] => [%s]", origin_name, rename_norm)
                continue
            os.rename(audio_item.file, rename_path)
            audio_item.file = rename_path
            if origin_name == rename_norm:
                LOGGER.info("File already named: [%s]", origin_name)
            else:
                LOGGER.info("Adjusted file name: [%s] => [%s]", origin_name, rename_norm)
    return audio_config
