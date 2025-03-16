"""
Operations for apply updates to the resulved audio files based on configuration and metadata parsing.
"""

import os
import re
from copy import deepcopy
from difflib import SequenceMatcher
from typing import (
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    TypeVar,
)
from unicodedata import normalize

import eyed3
from PIL import Image

from aiu.config import LOGGER, Config, StopwordsType
from aiu.tags import TAG_TITLE
from aiu.typedefs import (
    AudioConfig,
    AudioFile,
    AudioFileAny,
    AudioInfo,
    AudioTagDict,
    CoverFile,
    CoverFileAny,
)
from aiu.utils import (
    COMMON_WORD_IGNORE_CHARS,
    COMMON_WORD_REPLACE_CHARS,
    COMMON_WORD_SPLIT_CHARS,
    FILENAME_ILLEGAL_CHARS_REGEX,
)

MatchT = TypeVar("MatchT", bound=Iterable)


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
    audio_files = list(audio_files)
    total_files = len(audio_files)
    max_audio_count = max(len(cfg[1]) for cfg in configs)
    if config_shared or all(cfg[0] for cfg in configs):
        max_audio_count = total_files
        config_shared = True
    else:
        max_audio_count = max(max_audio_count, total_files)
    merged_config = AudioConfig(shared=config_shared)
    for i, (_, cfg) in enumerate(configs):
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
                    f"Cannot initialize audio config with [total = {max_audio_count}] "
                    f"and first config [size = {cfg_size}]. "
                    "First config must be [total = size] or [size = 1]. "
                    "Please resolve missing items manually."
                )
        elif cfg_size != max_audio_count:
            # following configs updates the first as required
            # FIXME: not implemented
            LOGGER.warning(
                "Use case not implemented for CFG_SIZE (%s) != MAX_AUDIO_COUNT (%s)! Skipping.",
                cfg_size, max_audio_count
            )
    if match_artist:
        for config in merged_config:
            config.album_artist = config.artist
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
    # threshold can be much more strict - files should almost perfectly match
    # allow some leeway to consider distinct ID3 values which will slightly affect the file size,
    # but not as much as the actual audio data
    match_size_threshold = 0.95
    # use names to avoid high match values due to the rest of the paths that should correspond as base directory
    file_names = [os.path.split(file)[-1] for file in file_paths]
    # use size map simply to avoid re-compute each time the value are used
    file_sizes = {name: float(os.stat(file).st_size) for name, file in zip(file_names, file_paths)}
    match_results = [
        (
            # for each name, compare against all other files, and obtain the best fuzzy match
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
    """
    Updates the audio file using provided audio tags.
    """
    audio_file = get_audio_file(audio_file)
    if not isinstance(audio_tags, dict):
        raise TypeError("Audio tag dict expected.")

    for tag, value in audio_tags.items():
        if not hasattr(audio_file, tag):
            LOGGER.warning("unknown tag '%s'", tag)
            continue
        if not overwrite and getattr(audio_file.tag, tag) is not None:
            LOGGER.warning("tag '%s' already set", tag)
            continue
        setattr(audio_file.tag, tag, value)
    audio_file.tag.save()


def get_audio_file(audio_file):
    # type: (AudioFileAny) -> AudioFile
    """
    Obtains the audio file by path or compatible objects.
    """
    if isinstance(audio_file, str):
        audio_file = eyed3.load(audio_file)
    if not isinstance(audio_file, AudioFile):
        raise TypeError("Audio file expected.")
    return audio_file


def get_cover_file(cover_file):
    # type: (CoverFileAny) -> CoverFile
    """
    Obtains the cover file by path or compatible objects.
    """
    if isinstance(cover_file, str):
        cover_file = Image.open(cover_file)
    if not isinstance(cover_file, CoverFile):
        raise TypeError("Cover file expected.")
    return cover_file


def save_cover_file(config, output_dir):
    # type: (AudioConfig, str) -> Optional[str]
    """
    Searches for any album image cover file within the audio configuration files and saves it.

    Only saves the first match, assuming all audio files belong to the same album and share the same cover.
    """
    path = os.path.join(output_dir, "cover.png")
    for cfg in config:
        if cfg.cover is not None:
            if os.path.isfile(path):
                LOGGER.warning("Could not save cover image, file already exists: [%s]", path)
                return path
            LOGGER.warning("Saved cover image: [%s]", path)
            cfg.cover.save(path)
            return path
    LOGGER.warning("Could not find any cover image to save. Operation skipped.")


def update_cover_file(config, cover_file):
    # type: (AudioConfig, CoverFileAny) -> None
    """
    Apply the new cover file to audio files if they mismatch.
    """
    if isinstance(cover_file, CoverFile):
        cover_file = cover_file.path
    for file_cfg in config:
        prev_cover = file_cfg.get("cover")
        if cover_file and (not prev_cover or cover_file != prev_cover.path):
            LOGGER.debug("Updating temporary cover image [%s] -> [%s] for [%s].",
                         prev_cover.path, cover_file, file_cfg.file)
            file_cfg.cover = cover_file


def filter_shared_items(choices):
    # type: (List[MatchT]) -> List[MatchT]
    """
    Removes the longest prefix or suffix items shared across all choices of variable size.
    """
    if len(choices) < 2:
        return choices
    max_subset = min(len(choice) for choice in choices) - 1
    for length in reversed(range(1, max_subset + 1)):
        first = choices[0]
        prefix = first[:length]
        suffix = first[length:]
        if all(other[:length] == prefix for other in choices[1:]):
            return [choice[length:] for choice in choices]
        if all(other[length:] == suffix for other in choices[1:]):
            return [choice[:length] for choice in choices]
    return choices


def compute_best_match(search, choices):
    # type: (MatchT, Iterable[MatchT]) -> Tuple[int, MatchT, float]
    """
    Selects the best matching string amongst multiple choices with fuzzy matching.

    .. seealso::
        https://stackoverflow.com/a/10383524
    """
    results = []
    for i, test in enumerate(choices):
        ratio = SequenceMatcher(None, search, test).ratio()
        results.append((i, test, ratio))
    results = sorted(results, key=lambda r: r[-1], reverse=True)
    return results[0]


def clean_words(text, stopwords):
    # type: (str, StopwordsType) -> List[str]
    """
    Clean up common characters exceptions and splits the resulting words from the cleaned text.
    """
    for char in COMMON_WORD_SPLIT_CHARS:
        text = text.replace(char, " ")
    for from_char, to_char in COMMON_WORD_REPLACE_CHARS.items():
        text = text.replace(from_char, to_char)
    words = text.lower().split(" ")
    stopwords = set(stopwords) | COMMON_WORD_IGNORE_CHARS
    words = [word for word in words if word and word not in stopwords]
    return words


def compute_word_match(search_files, search_info, threshold_match_words=0.6):
    # type: (List[str], List[AudioInfo], float) -> Dict[str, Optional[AudioInfo]]
    """
    Attempts to associate files by name with corresponding audio information with heuristic word matching.

    :param search_files: List of file names, paths or plain titles of these files to attempt matching.
    :param search_info: Reference information against which matching must be attempted.
    :param threshold_match_words:
        Threshold for which the word sequence would be considered a match with sufficient overlap between the
        source file title and the destination audio information. This value should be sufficiently low to allow
        some extra words that are not matched between the two sets, but sufficiently high to avoid matching anything.
    """
    search_file_words = [
        (file, clean_words(os.path.splitext(os.path.split(file)[-1])[0], Config.STOPWORDS_MATCH))
        for file in search_files
    ]
    search_audio_words = [
        clean_words(info.title, Config.STOPWORDS_MATCH)
        for info in search_info
    ]
    # A common scenario that causes no matches is when multiple files share a part of their name perfectly.
    # For example, when multiple songs are prefixed with their corresponding artist or album name.
    # These shared words are usually not included in the target words of the titles to match against,
    # which causes all matching attempts to yield a low score.
    # Remove them to increase matches using only discriminative words between available choices.
    filtered_file_words = filter_shared_items([words for _, words in search_file_words])
    search_file_words = [(search[0], words) for search, words in zip(search_file_words, filtered_file_words)]

    matches = {}  # type: Dict[str, Optional[AudioInfo]]
    for file, sf_words in search_file_words:
        matches[file] = None
        sf_match = compute_best_match(sf_words, search_audio_words)
        sf_ratio = sf_match[2]
        if sf_ratio > threshold_match_words:
            sf_index = sf_match[0]
            audio_info = search_info[sf_index]
            LOGGER.debug("Found potential word match for [%s] with [%s] (%0.2f%% match).",
                         file, audio_info.title, sf_ratio)
            matches[file] = audio_info
        else:
            LOGGER.debug("No word match found for [%s]. Too low score (%0.2f%% match).", file, sf_ratio)

    # ensure no conflicting matches
    for file in search_files:
        other_files = set(search_files) - {file}
        if not matches[file]:
            continue
        if not all(not matches[other] or matches[other] is not matches[file] for other in other_files):
            # remove shared match (conflict)
            # ensure removal everywhere, not just the current 'file' checked to avoid leaving one as unique match
            cur_info = matches[file]
            for dup_file in search_files:
                if matches[dup_file] and matches[dup_file] is cur_info:
                    LOGGER.debug("Potential word match for [%s] with [%s] caused duplicate, dropping it.",
                                 dup_file, cur_info.title)
                    matches[dup_file] = None
    return matches


def compute_tag_match(search_files, search_info, word_match=False):
    # type: (List[str], List[AudioInfo], bool) -> Dict[str, Optional[AudioInfo]]
    """
    Attempts to associate files by name with corresponding audio information with ID3 tag matching.
    """
    pseudo_search_files = {}
    for audio_file_path in search_files:
        audio_file = get_audio_file(audio_file_path)
        audio_title = getattr(audio_file.tag, TAG_TITLE, None)
        if not audio_title:
            continue
        pseudo_search_files[audio_title] = audio_file_path

    if word_match:
        word_matches = compute_word_match(list(pseudo_search_files), search_info)
        matches = {
            pseudo_search_files[audio_title]: audio_info
            for audio_title, audio_info
            in word_matches.items()
        }
        return matches

    matches = {}
    for audio_title, audio_file_path in pseudo_search_files.items():
        for audio_info in search_info:
            if audio_title == audio_info.title:
                LOGGER.debug("Found exact match for [%s] using ID3 tag.", audio_file_path)
                search_info.remove(audio_info)
                matches[audio_file_path] = audio_info
                break
    return matches


def check_last_item(search_files, search_audio):
    # type: (List[str], List[AudioInfo]) -> Dict[str, Optional[AudioInfo]]
    """
    Last resort check if there is only a single item remaining to match.

    In some cases, the remaining item that could not be matched against any of the previous heuristics is simply caused
    by the (purposely) *too strict* threshold used to avoid over-matching between multiple similar candidate items.
    A common example where one item remains unmatched is when audio information provides a "featuring ..." portion in
    the title, while the actual file name does not provide it, or vice-versa. Because this "featuring ..." part adds
    more words only on one side, the computed similarity necessarily yields a lower matching score. However, the
    difference is usually only slightly lower than what would be needed to be above the threshold (1-2 word off).

    In the situation where only one item to match remains, the risk of over-matching is greatly reduced, because all
    other relatively similar candidates should have been removed already from another audio information with much
    higher matching scores, from previous heuristics. Therefore, attempt validating a match with a looser threshold.

    A match *MUST* still be validated, even if only one item remains.
    Otherwise, an irrelevant name that was correctly unmatched could suddenly become "matched" erroneously.
    """
    matches = {}
    if len(search_files) == 1 and len(search_audio) == 1:
        matches = compute_word_match(search_files, search_audio, threshold_match_words=0.4)
        if matches:
            LOGGER.debug("Found last-item word match for [%s].", search_files[0])
    return matches


def apply_audio_config(audio_files, audio_config, use_tag_match=True, use_word_match=True, dry=False):
    # type: (Iterable[str], AudioConfig, bool, bool, bool) -> AudioConfig
    """
    Applies the metadata fields to the corresponding audio files.

    Matching is attempted first with file names, and other heuristics as required afterward.
    """
    matches = {}
    for i, file_path in enumerate(audio_files):
        _, file_name = os.path.split(file_path)
        matched_info = None  # type: Optional[AudioInfo]
        possible_matches = []
        for audio_info in audio_config:
            if audio_config.shared:
                possible_matches.append(audio_config[i])
                break

            clean_info_title = " ".join(clean_words(audio_info.title.lower(), Config.STOPWORDS_RENAME))
            clean_file_name = " ".join(clean_words(file_name.lower(), Config.STOPWORDS_RENAME))
            if clean_info_title in clean_file_name:
                possible_matches.append(audio_info)

        if len(possible_matches) == 1:
            matched_info = possible_matches[0]
        elif possible_matches:
            # in case multiple audio files share partial/similar names, try guessing the most matching one
            search_titles = [info.title for info in possible_matches]
            matched_index, matched_text, matched_ratio = compute_best_match(file_name, search_titles)
            matched_info = possible_matches[matched_index]
            LOGGER.debug("Used fuzzy title search for [%s], best result: [%s] (%0.2f%% match)",
                         file_path, matched_text, matched_ratio * 100)

        matches[file_path] = matched_info

    # in the event of very long names, this is often the result of too much metadata written in the file name
    # for example: '[ARTIST] - Some Title (feat. Other) (some version) [album]'
    # attempt various heuristics to find a potential alternative file match condition
    leftover_files = audio_files
    for use_heuristic, heuristic in [
        (use_word_match, compute_word_match),
        (use_tag_match, lambda _files, _audio: compute_tag_match(_files, _audio, word_match=False)),
        (use_tag_match and use_word_match, lambda _files, _audio: compute_tag_match(_files, _audio, word_match=True)),
        (use_word_match, check_last_item),
    ]:
        leftover_files = list(set(leftover_files) - {match for match, value in matches.items() if value})
        if not leftover_files:
            break
        if not use_heuristic:
            continue
        leftover_audio = [audio_info for audio_info in audio_config if audio_info not in matches.values()]
        word_matches = heuristic(leftover_files, leftover_audio)
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
                tag_info = list(sorted((k, v) for k, v in matched_info.items() if k not in ["file"]))
                tag_info = [("file", matched_info.file)] + tag_info
                tags_value_list = "\n".join(f"  {k}: {v}" for k, v in tag_info)
                LOGGER.info("Would apply tag updates:\n%s", tags_value_list)
                continue
            audio_file.tag.save()
        else:
            LOGGER.warning("No audio information was matched for file: [%s]", file_path)

    return audio_config


def update_file_names(audio_config, rename_format, rename_title=False, prefix_track=False, dry=False):
    # type: (AudioConfig, Optional[str], bool, bool, bool) -> AudioConfig
    """
    Renames the files and updates the configuration according to specified formats.
    """
    if not audio_config:
        LOGGER.error("No configuration to process!")
        return audio_config
    if rename_title or prefix_track:
        if prefix_track:
            LOGGER.debug("Updating rename format with title and prefix.")
            track_digits = len(str(len(audio_config)))
            rename_format = "%(TRACK)0{}d %(TITLE)s".format(track_digits)  # pylint: disable=consider-using-f-string
        else:
            LOGGER.debug("Updating rename format with title only.")
            rename_format = "%(TITLE)s"
    if not rename_format:
        LOGGER.warning("No rename format or rename flag specified. Not renaming anything.")
        return audio_config
    if "%(" not in rename_format or ")" not in rename_format:
        LOGGER.error("No rename format or template variable specified! Will not rename anything.")
        return audio_config
    format_tags = [tag.lower() for tag in re.findall(r"%\(([A-Za-z_]+)\)s", rename_format)]
    for audio_item in audio_config:
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
            rename_name = re.sub(FILENAME_ILLEGAL_CHARS_REGEX, "_", rename_name)
            rename_norm = normalize("NFKD", rename_name)
            LOGGER.debug("Before/after normalization: [%s] => [%s]", rename_name, rename_norm)
            rename_path, origin_name = os.path.split(audio_item.file)
            origin_name, origin_ext = os.path.splitext(origin_name)
            rename_path = os.path.join(rename_path, rename_norm + origin_ext)
            if dry:
                LOGGER.info("Would rename [%s] => [%s]", origin_name, rename_norm)
                continue
            if origin_name == rename_norm:
                LOGGER.info("File already named: [%s]", origin_name)
            else:
                LOGGER.info("Adjusted file name: [%s] => [%s]", origin_name, rename_norm)
                os.rename(audio_item.file, rename_path)
                audio_item.file = rename_path
    return audio_config
