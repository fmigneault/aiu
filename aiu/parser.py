"""
Utilities for parsing audio metadata from various formats.
"""

import csv
import io
import itertools
import json
import logging
import math
import os
import re
import tempfile
from typing import (
    Iterable,
    List,
    Optional,
    Union,
    overload,
)
from typing_extensions import Literal, TypeVar

import requests
import yaml
from eyed3.mimetype import guessMimetype
from eyed3.mp3 import MIME_TYPES as MP3_MIME_TYPES
from PIL import Image

from aiu.config import LOGGER, ExceptionsType, StopwordsType
from aiu.tags import TAG_DURATION, TAG_TITLE, TAG_TRACK
from aiu.typedefs import AudioConfig, Duration, FormatInfo

AnyConfig = Union[ExceptionsType, StopwordsType]

numbered_list = re.compile(r"^[\s\-#.]*([0-9]+)[\s\-#.]*(.*)")
duration_info = re.compile(r"""     # Match any 'duration' representation, need to filter if many (ex: one in title)
                                    # Use literal [0-9] ranges because \d can match an empty string, which raises int()
    .*?                                         # non-greedy match on filler (as close as possible)
    ((?:(?:[0-9]*)|(?:2[0-3])|(?:[0-9])):       # hours time part of any length (0-inf, not 00-12)
     (?:[0-5][0-9])                             # minutes time part (00-59)
     (?::[0-5][0-9])?)                          # seconds time part (00-59)
""", re.VERBOSE)

FormatInfoType = TypeVar("FormatInfoType", bound=FormatInfo)

FORMAT_MODE_ANY = FormatInfo("any", "*")
FORMAT_MODE_CSV = FormatInfo("csv", "csv")
FORMAT_MODE_TAB = FormatInfo("tab", ["tsv", "tab", "cfg", "config", "meta", "info", "txt"])
FORMAT_MODE_LIST = FormatInfo("list", ["ls", "lst", "list"])
FORMAT_MODE_JSON = FormatInfo("json", "json")
FORMAT_MODE_YAML = FormatInfo("yaml", ["yml", "yaml"])
FORMAT_MODE_RAW = FormatInfo("raw", ["raw", "cls", "class", "ref"])     # YAML with full class and properties values
FORMAT_MODES = frozenset([
    FORMAT_MODE_CSV,
    FORMAT_MODE_TAB,
    FORMAT_MODE_JSON,
    FORMAT_MODE_YAML,
    FORMAT_MODE_RAW,
])

PARSER_MODES = frozenset([
    FORMAT_MODE_ANY,
    FORMAT_MODE_CSV,
    FORMAT_MODE_TAB,
    FORMAT_MODE_LIST,
    FORMAT_MODE_JSON,
    FORMAT_MODE_YAML,
])
ALL_PARSER_EXTENSIONS = frozenset(
    itertools.chain(*(p.extensions for p in PARSER_MODES))) - {FORMAT_MODE_ANY.extensions[0]}

ALL_IMAGE_EXTENSIONS = frozenset(["tif", "png", "jpg", "jpeg"])


@overload
def load_config(maybe_config, wanted_config, is_map):
    # type: (Optional[AnyConfig], Optional[str], Literal[True]) -> ExceptionsType
    ...


@overload
def load_config(maybe_config, wanted_config, is_map):
    # type: (Optional[AnyConfig], Optional[str], Literal[False]) -> StopwordsType
    ...


def load_config(maybe_config, wanted_config, is_map):
    # type: (Optional[AnyConfig], Optional[Union[str, AnyConfig]], bool) -> Optional[AnyConfig]
    if maybe_config is None and isinstance(wanted_config, str) and os.path.isfile(wanted_config):
        try:
            with open(wanted_config, mode="r", encoding="utf-8") as f:
                lines = [w.strip() for w in f.readlines() if not w.startswith("#")]
                if is_map:
                    lines = [line.split(":") for line in lines]
                    maybe_config = {k.strip().lower(): w.strip() for k, w in lines if k and w}
                else:
                    maybe_config = [line.lower() for line in lines if line]
        except Exception:
            raise ValueError(
                f"Invalid configuration file could not be parsed:\n  file: [{wanted_config!s}]\n  map?: [{is_map}]"
            )
    if isinstance(wanted_config, (list, dict)):
        maybe_config = wanted_config
    return maybe_config


def find_mode(mode, formats):
    # type: (Union[str, FormatInfo], Iterable[FormatInfo]) -> Union[FormatInfo, None]
    if isinstance(mode, FormatInfo):
        return mode
    for fmt in formats:
        if fmt.matches(extension=mode) or fmt.name == mode:
            return fmt
    return None


def parse_audio_config(  # pylint: disable=broad-exception-caught  # raise at end to attempt alternate fallback formats
    config_file,
    mode=FORMAT_MODE_ANY,
):
    # type: (str, Optional[Union[str, FormatInfo]]) -> AudioConfig
    """
    Attempts various parsing methods to retrieve audio files metadata from a config file.
    """

    if not os.path.isfile(config_file):
        raise ValueError(f"invalid file path: [{config_file}]")

    fmt_mode = find_mode(mode, PARSER_MODES)
    if not fmt_mode:
        raise ValueError(f"invalid parser mode: [{mode}]")
    log_lvl = logging.WARNING if fmt_mode is FORMAT_MODE_ANY else logging.ERROR

    # --- CSV with header row ---
    if fmt_mode in [FORMAT_MODE_ANY, FORMAT_MODE_CSV]:
        LOGGER.debug("parsing using mode [%s]", FORMAT_MODE_CSV)
        try:
            with open(config_file, mode="r", encoding="utf-8") as f:
                config = AudioConfig(list(csv.DictReader(f)))
            # avoid false positive when single field without header is valid against 'list' mode
            if not all(fields for fields in config):
                LOGGER.debug("parsing with mode [%s] yielded no values, moving on...", FORMAT_MODE_CSV)
            else:
                LOGGER.debug("success using mode [%s]", FORMAT_MODE_CSV)
                return config
        except Exception as exc:
            LOGGER.log(log_lvl, "failed parsing as [%s], moving on...", FORMAT_MODE_CSV)
            LOGGER.trace("exception during [%s] parsing attempt:", fmt_mode, exc_info=exc)

    # --- TAB with/without numbering ---
    if fmt_mode in [FORMAT_MODE_ANY, FORMAT_MODE_TAB]:
        LOGGER.debug("parsing using mode [%s]", FORMAT_MODE_TAB)
        try:
            return parse_audio_config_tab(config_file)
        except Exception as exc:
            LOGGER.log(log_lvl, "failed parsing as [%s], moving on...", FORMAT_MODE_TAB)
            LOGGER.trace("exception during [%s] parsing attempt:", fmt_mode, exc_info=exc)

    # --- YAML / JSON ---
    if fmt_mode in [FORMAT_MODE_ANY, FORMAT_MODE_JSON, FORMAT_MODE_YAML]:
        LOGGER.debug("parsing using mode [%s/%s]", FORMAT_MODE_YAML, FORMAT_MODE_JSON)
        try:
            return parse_audio_config_objects(config_file)
        except Exception as exc:
            LOGGER.log(log_lvl, "failed parsing as [%s/%s], moving on...", FORMAT_MODE_YAML, FORMAT_MODE_JSON)
            LOGGER.trace("exception during [%s] parsing attempt:", fmt_mode, exc_info=exc)

    # --- LIST ---
    # parse this format last as it is the hardest to guess, and probably easiest to incorrectly match against others
    if fmt_mode in [FORMAT_MODE_ANY, FORMAT_MODE_LIST]:
        LOGGER.debug("parsing using mode [%s]", FORMAT_MODE_LIST)
        try:
            return parse_audio_config_list(config_file)
        except Exception as exc:
            LOGGER.log(log_lvl, "failed parsing as [%s], moving on...", FORMAT_MODE_LIST)
            LOGGER.trace("exception during [%s] parsing attempt:", fmt_mode, exc_info=exc)

    raise ValueError("no more parsing method available, aborting...")


def parse_audio_config_objects(config_file):
    # type: (str) -> AudioConfig
    """
    Parse a file formatted with list of object in JSON/YAML.

    Format::

        - track: #
          title: ""
          duration: ""
        - ...
    """
    with open(config_file, mode="r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    if not isinstance(config, list):
        config = [config]
    config = AudioConfig(config)
    LOGGER.debug("success using mode [%s/%s]", FORMAT_MODE_YAML, FORMAT_MODE_JSON)
    return config


def parse_audio_config_list(config_file):
    # type: (str) -> AudioConfig
    """
    Parse a file formatted with list row-fields of continuous intervals.

    Either ``track`` or ``duration`` or both *must* be provided.

    Format::

        [track-1]
        title-1
        [duration-1]
        [track-2]
        title-2
        [duration-2]
        ...
    """
    with open(config_file, mode="r", encoding="utf-8") as f:
        lines = [row.strip() for row in f.readlines() if row]

    # check for either track, duration or both + title for each
    fields_2 = not len(lines) % 2
    fields_3 = not len(lines) % 3
    config = []

    def _parse_fields_3():
        _config = []
        try:
            _titles = [lines[i + 1] for i in range(0, len(lines), 3)]
            _track_matches = [re.match(numbered_list, lines[i]) for i in range(0, len(lines), 3)]
            _duration_matches = [re.match(duration_info, lines[i + 2]) for i in range(0, len(lines), 3)]
            _track_groups = [list(m.groups()) for m in _track_matches]
            _duration_groups = [list(m.groups())[0] for m in _duration_matches]
            _track_valid = all(grp[0].isnumeric() and grp[1] == "" for grp in _track_groups)
            _duration_valid = all(Duration(grp) for grp in _duration_groups)
            if _track_valid and _duration_valid:
                _tracks = [grp[0] for grp in _track_groups]
                _durations = [grp for grp in _duration_groups]
                _config = [{TAG_TRACK: track, TAG_TITLE: title, TAG_DURATION: duration}
                           for track, title, duration in zip(_tracks, _titles, _durations)]
        except Exception as exc:  # pylint: disable=broad-exception-caught  # fallback to caller
            LOGGER.trace("exception during [%s] parsing attempt (assuming 3 fields):", FORMAT_MODE_LIST, exc_info=exc)
        return _config

    def _parse_fields_2():
        _config = []
        try:
            _track_matches = [re.match(numbered_list, lines[i]) for i in range(0, len(lines), 2)]
            _duration_matches = [re.match(duration_info, lines[i + 1]) for i in range(0, len(lines), 2)]
            if all(match is not None for match in _track_matches):
                _track_groups = [list(m.groups()) for m in _track_matches]
                if all(grp[0].isnumeric() and grp[1] == "" for grp in _track_groups):
                    _tracks = [grp[0] for grp in _track_groups]
                    _titles = [lines[i + 1] for i in range(0, len(lines), 2)]
                    _config = [{TAG_TRACK: track, TAG_TITLE: title} for track, title in zip(_tracks, _titles)]
            elif all(match is not None for match in _duration_matches):
                _duration_groups = [list(m.groups())[0] for m in _duration_matches]
                if all(Duration(grp) for grp in _duration_groups):  # will raise on any invalid parsing
                    _titles = [lines[i] for i in range(0, len(lines), 2)]
                    _durations = [grp for grp in _duration_groups]
                    _config = [{TAG_DURATION: duration, TAG_TITLE: title}
                               for duration, title in zip(_durations, _titles)]
        except Exception as exc:  # pylint: disable=broad-exception-caught  # fallback to caller
            LOGGER.trace("exception during [%s] parsing attempt (assuming 3 fields):", FORMAT_MODE_LIST, exc_info=exc)
        return _config

    # sometimes, number of lines can be ambiguous between 2/3 lines (eg: 42/3 = 14, 42/2 = 21)
    # try first with 3 fields which is harder to match, and then retry with 2 if not successful
    if fields_3:
        config = _parse_fields_3()
    if fields_2 and not config:
        config = _parse_fields_2()
    if not config:
        raise ValueError(f"invalid number of lines to parse as [{FORMAT_MODE_LIST}], moving on...")
    if not all(isinstance(c, dict) for c in config):
        raise ValueError(f"invalid parsing result as [{FORMAT_MODE_LIST}], moving on...")
    config = AudioConfig(config)
    LOGGER.debug("success using mode [%s]", FORMAT_MODE_LIST)
    return config


def parse_audio_config_tab(config_file):
    # type: (str) -> AudioConfig
    """
    Parse a file formatted with TAB.

    Format::

        [track]   title   duration
    """
    with open(config_file, mode="r", encoding="utf-8") as f:
        lines = f.readlines()
    config = []
    for row in lines:
        row = row.strip()
        info = re.match(numbered_list, row)
        track, row = info.groups() if info else (None, row)
        info = re.findall(duration_info, row)
        # assume the duration is the last info if multiple matches
        duration = info[-1] if info else None
        if duration:
            row = row[:-len(duration)]
        row = row.strip()
        config.append({
            TAG_TRACK: track,
            TAG_TITLE: row,
            TAG_DURATION: duration,
        })
    if not all(isinstance(c, dict) for c in config):
        raise ValueError(f"invalid parsing result as [{FORMAT_MODE_TAB}], moving on...")
    config = AudioConfig(config)
    LOGGER.debug("success using mode [%s]", FORMAT_MODE_TAB)
    return config


def write_config(audio_config, file_path, fmt_mode):
    # type: (AudioConfig, str, FormatInfo) -> None
    """
    Raw writing operation to dump audio config to file with specified format.
    """
    all_have_track = all(isinstance(_.track, int) for _ in audio_config)
    audio_config = AudioConfig(sorted(audio_config, key=lambda _: _.track if all_have_track else _.title or _.file))
    if fmt_mode is FORMAT_MODE_RAW:
        # yaml with classes with output yaml representation of their references
        fmt_mode = FORMAT_MODE_YAML
    else:
        audio_config = audio_config.value
    with open(file_path, mode="w", encoding="utf-8") as f:
        if fmt_mode is FORMAT_MODE_JSON:
            json.dump(audio_config, f)
        elif fmt_mode is FORMAT_MODE_YAML:
            yaml.dump(audio_config, f, default_flow_style=False)
        elif fmt_mode is FORMAT_MODE_CSV:
            header = list(audio_config[0].keys())
            w = csv.DictWriter(f, fieldnames=header)
            w.writeheader()
            w.writerows(audio_config)
        elif fmt_mode is FORMAT_MODE_TAB:
            max_title_len = len(max(audio_config, key=lambda _: _.title).title)
            max_track_len = 0 if not all_have_track else int(math.log10(max(_.track for _ in audio_config))) + 1
            max_track_dot = max_track_len + 1   # extra space for '.' after track number
            line_fmt = "{track:track_tab}{title:title_tab}{duration}" \
                .replace("title_tab", str(max_title_len)) \
                .replace("track_tab", str(max_track_dot))
            for ac in audio_config:
                track = f"{ac.track}." if all_have_track else ""
                f.write(line_fmt.format(
                    track=track,
                    title=ac.title,
                    duration=ac.duration if ac.duration else "")
                )
        else:
            raise NotImplementedError(f"format [{fmt_mode}] writing to file unknown")


def save_audio_config(audio_config, file_path, mode=FORMAT_MODE_YAML, dry=False):
    # type: (AudioConfig, str, Optional[Union[str, FormatInfo]], bool) -> bool
    """
    Saves the audio config if permitted by the OS and using the corrected file extension.
    """
    fmt_mode = find_mode(mode, FORMAT_MODES)
    if not mode:
        raise ValueError(f"invalid output format mode [{mode}], aborting...")
    name, ext = os.path.splitext(file_path)
    if not fmt_mode.matches(ext):
        LOGGER.warning("file extension [%s] doesn't match requested save format [%s], fixing to [%s].",
                       ext, mode, fmt_mode.name)
        ext = fmt_mode.extensions[0]
    dot = "" if ext.startswith(".") else "."
    file_path = f"{name}{dot}{ext}"
    if os.path.isfile(file_path):
        if dry:
            LOGGER.debug("Would have removed file: [%s]", file_path)
        else:
            os.remove(file_path)
    if dry:
        LOGGER.info("Would have saved the output configuration in file: [%s]", file_path)
    else:
        write_config(audio_config, file_path, fmt_mode)
    return os.path.isfile(file_path)


def get_audio_files(path, allow_none=False):
    # type: (str, bool) -> List[str]
    """
    Retrieves all supported audio files from the specified path (file or directory).
    """
    if not os.path.isdir(path):
        if os.path.isfile(path):
            files = [path]
        elif allow_none:
            return []
        else:
            raise ValueError(f"invalid path: [{path}]")
    else:
        files = [os.path.join(path, f) for f in os.listdir(path)]

    def is_mp3(f):
        try:
            return guessMimetype(f) in MP3_MIME_TYPES
        except PermissionError:
            return False

    return list(filter(is_mp3, files))


_FETCHED_CACHE = {}


def fetch_image(link, output_dir=None):
    # type: (str, Optional[str]) -> str
    """
    Retrieve the image from a reference URL and save it locally, or return the local path if already available.

    Images retrieved from URL will be cached for direct access on following calls.
    """
    global _FETCHED_CACHE  # pylint: disable=W0602

    # avoid over requesting to reduce transfer + avoid rate-limiting
    path = _FETCHED_CACHE.get(link)
    if path is not None:
        LOGGER.debug("Using cached image: [%s]", link)
        return path

    LOGGER.debug("Fetching image: [%s]", link)
    resp = requests.get(link, timeout=5)
    if resp.status_code != 200:
        raise ValueError(f"invalid link could not be reached [{link!s}]")
    mime = resp.headers.get("Content-Type", "")
    name = resp.headers.get("Content-Disposition", "").split("filename=")[-1].split(";")[0].replace("\"", "")
    if not (mime.startswith("image/") or name):
        raise ValueError(
            f"invalid link does not correspond to image reference [{link!s}] "
            "and does not not provide any filename"
        )
    # if name:
    #     ext = os.path.splitext(name)[-1].replace(".", "")
    # else:
    #     ext = mime.replace("image/", "").split(";")[0]

    if output_dir is None:
        output_dir = tempfile.mkdtemp()
    buffer = io.BytesIO(resp.content)
    image = Image.open(buffer)  # type: Image.Image
    path = os.path.join(output_dir, "cover.png")
    image.save(path, format="PNG")  # convert to PNG regardless of source

    _FETCHED_CACHE[link] = path
    return path
