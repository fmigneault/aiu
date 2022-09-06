import os
import re
from copy import deepcopy
from typing import Dict, Iterable, List, Optional, Tuple
from unicodedata import normalize
from difflib import SequenceMatcher

from aiu.typedefs import AudioConfig, AudioFileAny, AudioInfo, AudioTagDict, CoverFileAny
from aiu.utils import (
    COMMON_WORD_REPLACE_CHARS,
    COMMON_WORD_SPLIT_CHARS,
    FILENAME_ILLEGAL_CHARS,
    get_audio_file,
    get_cover_file
)
from aiu import LOGGER, Config


def merge_audio_configs(configs, match_artist, audio_files, config_shared, delete_duplicate):
    # type: (Iterable[Tuple[bool, AudioConfig]], bool, Iterable[str], bool, bool) -> AudioConfig
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
    :param audio_files:
        List of available audio files to eventually process using provided configurations.
        Use to expand the configurations dimension to match size if all combinations apply only to ``all`` audio files.
        Also employed to validate dimensions of per-audio-file information that should (loosely) match.
    :param config_shared:
        Indication whether the audio file configurations only correspond to ``all`` definitions.
        In this case, a special flag is set in the resulting merged configuration for later reference.
    :param delete_duplicate:
        In case of mismatching audio file and :class:`AudioInfo` counts, delete any file that would resolve the
        inconsistency if they can be validated as duplicates to other files.
    :return: merged config.
    """
    total_files = len(list(audio_files))
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
                if delete_duplicate and max_audio_count > cfg_size:
                    resolved_files = filter_duplicates(audio_files)
                    if len(resolved_files) == cfg_size:
                        LOGGER.debug("Successfully resolved duplicates audio files to align with audio config.")
                        duplicate_files = set(audio_files) - set(resolved_files)
                        for dup_file in duplicate_files:
                            LOGGER.warning("Removing detected audio file as duplicate: [%s]", dup_file)
                            os.remove(dup_file)
                        merged_config.extend(cfg)
                        continue
                raise ValueError(
                    (
                        "Cannot initialize audio config with [total = {}] and first config [size = {}]. "
                        "First config must be [total = size] or [size = 1]. "
                        "Please resolve missing items manually."
                    ).format(max_audio_count, cfg_size)
                )
        else:
            # following configs updates the first as required
            if cfg_size != max_audio_count:
                # FIXME: not implemented
                pass


                #for c in cfg[1]:
    return merged_config


def filter_duplicates(file_paths):
    # type: (List[str]) -> List[str]
    """
    Attempts to filter out partial duplicate files with multiple heuristics.
    """
    # name threshold should be sufficiently high to disallow partial name similarities
    # (e.g.: 'This Song!' and 'This Song (Extended)' should NOT match - actually 2 different songs)
    # but should also be sufficiently low to allow minor formatting or styling differences
    # (e.g.: 'This Song!' and 'This Song_' [corrected rename] should match)
    match_name_threshold = 0.95
    # to ensure consistency, any potential duplicate should also have very close content size
    # size threshold can be much more strict - files should almost perfectly match
    # allow some leeway to consider distinct ID3 values which will slightly affect the file size,
    # but not as much as the actual audio data
    match_size_threshold = 0.95
    # use names to avoid high match values due to the rest of the paths that should correspond as base directory
    file_names = [os.path.split(file)[-1] for file in file_paths]
    # use size map simply to avoid re-compute each time the value are used
    file_sizes = {name: float(os.stat(file).st_size) for name, file in zip(file_names, file_paths)}
    match_results = [
        (
            # for each name, compare against all other files, and obtain best fuzzy match
            compute_best_match(name, file_names[:i] + file_names[i + 1:]),  # (index, name, ratio)
            (name, path)
        )
        for i, (name, path) in enumerate(zip(file_names, file_paths))
    ]
    filter_results = list(filter(lambda res: res[0][-1] > match_name_threshold, match_results))
    filter_results = [
        (
            1 - abs(file_sizes[match[1]] - file_sizes[name]) / file_sizes[name],  # size diff ratio against best match
            (
                match[1],   # name of the best match by file name (other than the current one)
                file_paths[match[0]]    # path of the best match
            ),
            (name, path)
        )
        for match, (name, path) in filter_results
    ]
    filter_results = list(filter(lambda res: res[0] > match_size_threshold, filter_results))
    # size duplicate matches imply necessarily that (at least) 2 files represent the same content
    # (i.e.: matching duplicates will reference each other since they were similar both ways),
    # we must only remove the other(s) that were not already detected as duplicate to keep only one
    filtered_paths = []
    duplicate_paths = [res[-1][-1] for res in filter_results]
    for path in file_paths:
        if path not in duplicate_paths:
            filtered_paths.append(path)
            continue
        for result in list(filter_results):
            dup_path = result[-1][-1]
            if dup_path == path:
                if dup_path not in filtered_paths:
                    filtered_paths.append(path)
                    # remove any already processed duplicate from above insertion
                    filter_results = [res for res in filter_results if res[1][-1] != dup_path]
                break
    return filtered_paths


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


def compute_best_match(text, choices):
    # type: (str, Iterable[str]) -> Tuple[int, str, float]
    """
    Selects the best matching string amongst multiple choices with fuzzy matching.

    .. seealso::
        https://stackoverflow.com/a/10383524
    """
    results = []
    for i, test in enumerate(choices):
        ratio = SequenceMatcher(None, text, test).ratio()
        results.append((i, test, ratio))
    results = sorted(results, key=lambda r: r[-1], reverse=True)
    return results[0]


def clean_words(text):
    # type: (str) -> List[str]
    """
    Clean up common characters exceptions and splits the resulting words from the cleaned text.
    """
    for char in FILENAME_ILLEGAL_CHARS + COMMON_WORD_SPLIT_CHARS:
        text = text.replace(char, " ")
    for from_char, to_char in COMMON_WORD_REPLACE_CHARS.items():
        text = text.replace(from_char, to_char)
    words = text.lower().split(" ")
    words = [word for word in words if word not in Config.STOPWORDS]
    return words


def compute_word_match(search_files, search_info):
    # type: (List[str], List[AudioInfo]) -> Dict[str, Optional[AudioInfo]]
    """
    Attempts to associate files by name with corresponding audio information with heuristic word matching.
    """
    matches = {}

    search_file_words = {file: clean_words(os.path.split(file)[-1]) for file in search_files}
    search_title_words = {str(info.title): clean_words(info.title) for info in search_info}
    search_title_audio = {str(info.title): info for info in search_info}

    # very loose match to allow many extra words
    # take into account that only leftover/unmatched items should remain
    threshold_match_words = 0.6

    for file, sf_words in search_file_words.items():
        matches[file] = None
        for ai_title, ai_words in search_title_words.items():
            audio_info = search_title_audio[ai_title]
            ratio = SequenceMatcher(None, sf_words, ai_words).ratio()
            if ratio > threshold_match_words:
                if not matches[file]:
                    LOGGER.debug("Found potential word match for [%s] with [%s] (%0.2f%% match)",
                                 file, audio_info.title, ratio)
                    matches[file] = (ratio, audio_info)
                elif matches[file] and matches[file][0] < ratio:
                    LOGGER.debug("Found better word match for [%s] with [%s] (%0.2f%% match, %0.2f%% previous)",
                                 file, audio_info.title, ratio, matches[file][0])
                    matches[file] = (ratio, audio_info)

    # ensure no conflicting matches
    for file in search_files:
        other_files = set(search_files) - {file}
        if not matches[file]:
            continue
        if not all(not matches[other] or matches[other][1] is not matches[file][1] for other in other_files):
            # remove shared match (conflict)
            # ensure removal everywhere, not just the current 'file' checked to avoid leaving one as unique match
            cur_info = matches[file][1]
            for dup_file in search_files:
                if matches[dup_file] and matches[dup_file][1] is cur_info:
                    LOGGER.debug("Potential word match for [%s] with [%s] caused duplicate, dropping it.",
                                 dup_file, cur_info.title)
                    matches[dup_file] = None
    for file in list(matches):
        if matches[file]:
            LOGGER.debug("Found unique word match for [%s] with [%s].", file, matches[file][1].title)
            matches[file] = matches[file][1]  # return expected format, dropping the temporary ratio
    return matches


def apply_audio_config(audio_files, audio_config, use_word_match=True, dry=False):
    # type: (Iterable[str], AudioConfig, bool, bool) -> AudioConfig
    """
    Applies the metadata fields to the corresponding audio files.

    Matching is attempted first with file names, and other heuristics as required afterward.
    """
    matches = {}
    for i, file_path in enumerate(audio_files):
        file_dir, file_name = os.path.split(file_path)
        matched_info = None  # type: Optional[AudioInfo]
        possible_matches = []
        for audio_info in audio_config:  # type: AudioInfo
            if audio_config.shared:
                possible_matches.append(audio_config[i])
                break
            else:
                clean_info_title = " ".join(clean_words(audio_info.title.lower()))
                clean_file_name = " ".join(clean_words(file_name.lower()))
                if clean_info_title in clean_file_name:
                    possible_matches.append(audio_info)

        if len(possible_matches) == 1:
            matched_info = possible_matches[0]
        elif len(possible_matches):
            # in case multiple audio files share partial/similar names, try guessing the most matching one
            search_titles = [info.title for info in possible_matches]
            matched_index, matched_text, matched_ratio = compute_best_match(file_name, search_titles)
            matched_info = possible_matches[matched_index]
            LOGGER.debug("Used fuzzy title search for [%s], best result: [%s] (%0.2f%% match)",
                         file_path, matched_text, matched_ratio * 100)

        matches[file_path] = matched_info

    if use_word_match and any(not match for match in matches.values()):
        # in the event of very long names, this is often the result of too much metadata written in the name
        # for example: '[ARTIST] - Some Title (feat. Other) (some version) [album]'
        # attempt finding a match with the most corresponding words
        # use only remaining audio files that were not already matched to reduce chances of error
        leftover_files = list(set(audio_files) - set(match for match in matches if matches[match]))
        leftover_audio = [audio_info for audio_info in audio_config if audio_info not in matches.values()]
        word_matches = compute_word_match(leftover_files, leftover_audio)
        matches.update(word_matches)

    for file_path in audio_files:
        matched_info = matches[file_path]

        if matched_info:
            LOGGER.debug("Matched file [%s] with [%s]", file_path, matched_info)
            if matched_info.file:
                LOGGER.warning("[%s] already matched with [%s], skipping...", matched_info, matched_info.file)
                continue
            matched_info.file = file_path
            audio_file = get_audio_file(file_path)
            for tag_name, tag in matched_info.items():
                if dry:
                    LOGGER.debug("Would apply tag [%s] with value [%s] to file [%s]", tag_name, tag.value, file_path)
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
    format_tags = [tag.lower() for tag in re.findall("%\(([A-Za-z_]+)\)s", rename_format)]
    for audio_item in audio_config:  # type: AudioInfo
        if audio_item.file:
            if not os.path.isfile(audio_item.file):
                LOGGER.error("Invalid file value cannot be found: [%s]", audio_item.file)
                continue
            tag_values = {tag: audio_item.get(tag, None) for tag in format_tags}
            if any(tag_values[tag] is None for tag in format_tags):
                LOGGER.error("Cannot proceed to renaming files with specified format [%s] against missing ID3 Tag "
                             "from provided configurations for file: [%s]", rename_format, audio_item.file)
                LOGGER.error("Resolved configuration ID3 tags: %s", tag_values)
                raise ValueError("Missing required ID3 Tag.")
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
