from aiu.typedefs import AudioFile, AudioConfig, FormatInfo
from aiu.utils import get_logger
from eyed3.mp3 import isMp3File
from typing import AnyStr, Iterable, Optional, Union
import string
import math
import yaml
import json
import csv
import os
import re

LOGGER = get_logger()

numbered_list = re.compile(r"^[\s\-#.]*([0-9]+)[\s\-#.]*(.*)")
duration_info = re.compile(r"""     # Match any 'duration' representation, need to filter if many (ex: one in title)
                                    # Use literal [0-9] ranges because \d can match an empty string, which raises int()
    .*?                                         # non-greedy match on filler (as close as possible)
    ((?:(?:[0-9]*)|(?:[2][0-3])|(?:[0-9])):     # hours time part of any length (0-inf, not 00-12)
     (?:[0-5][0-9])                             # minutes time part (00-59)
     (?::[0-5][0-9])?)                          # seconds time part (00-59)
""", re.VERBOSE)

FORMAT_MODE_ANY = FormatInfo('any', '*')
FORMAT_MODE_CSV = FormatInfo('csv', 'csv')
FORMAT_MODE_TAB = FormatInfo('tab', ['tab', 'cfg', 'config', 'meta', 'info', 'txt'])
FORMAT_MODE_JSON = FormatInfo('json', 'json')
FORMAT_MODE_YAML = FormatInfo('yaml', ['yml', 'yaml'])
format_modes = frozenset([
    FORMAT_MODE_CSV,
    FORMAT_MODE_TAB,
    FORMAT_MODE_JSON,
    FORMAT_MODE_YAML,
])
parser_modes = frozenset([FORMAT_MODE_ANY] + list(format_modes))


def find_mode(mode, formats):
    # type: (Union[AnyStr, FormatInfo], Iterable[FormatInfo]) -> Union[FormatInfo, None]
    if isinstance(mode, FormatInfo):
        return mode
    for fmt in formats:
        if fmt.matches(mode):
            return fmt
    return None


def parse_audio_config(config_file, mode=FORMAT_MODE_ANY):
    # type: (AnyStr, Optional[Union[AnyStr, FormatInfo]]) -> AudioConfig
    """Attempts various parsing methods to retrieve audio files metadata from a config file."""

    if not os.path.isfile(config_file):
        raise ValueError("invalid file path: [{}]".format(config_file))

    fmt_mode = find_mode(mode, parser_modes)
    if not fmt_mode:
        raise ValueError("invalid parser mode: [{}]".format(mode))

    # --- CSV with header row ---
    if fmt_mode in [FORMAT_MODE_ANY, FORMAT_MODE_CSV]:
        LOGGER.debug("parsing using mode [{}]".format(FORMAT_MODE_CSV))
        # noinspection PyBroadException
        try:
            with open(config_file, 'r') as f:
                config = AudioConfig(list(csv.DictReader(f)))
            LOGGER.debug("success using mode [{}]".format(FORMAT_MODE_CSV))
            return config
        except Exception:
            log_func = LOGGER.warning if fmt_mode is FORMAT_MODE_ANY else LOGGER.exception
            log_func("failed parsing as [{}], moving on...".format(FORMAT_MODE_CSV))
            if fmt_mode is not FORMAT_MODE_ANY:
                pass

    # --- TAB with/without numbering ---
    if fmt_mode in [FORMAT_MODE_ANY, FORMAT_MODE_TAB]:
        LOGGER.debug("parsing using mode [{}]".format(FORMAT_MODE_TAB))
        # noinspection PyBroadException
        try:
            with open(config_file, 'r') as f:
                config = f.readlines()
            for i, row in enumerate(config):
                row = row.strip()
                info = re.match(numbered_list, row)
                track, row = info.groups() if info else (None, row)
                info = re.findall(duration_info, row)
                # assume the duration is the last info if multiple matches
                duration = info[-1] if info else (None, row)
                if duration:
                    row = row[:-len(duration)]
                row = row.strip()
                # noinspection PyTypeChecker
                config[i] = {
                    'track': track,
                    'title': row,
                    'duration': duration,
                }
            if not all([isinstance(c, dict) for c in config]):
                raise ValueError("invalid parsing result as [{}], moving on...".format(FORMAT_MODE_TAB))
            # noinspection PyTypeChecker
            config = AudioConfig(config)
            LOGGER.debug("success using mode [{}]".format(FORMAT_MODE_TAB))
            return config
        except Exception:
            log_func = LOGGER.warning if fmt_mode is FORMAT_MODE_ANY else LOGGER.exception
            log_func("failed parsing as [{}], moving on...".format(FORMAT_MODE_TAB))
            if fmt_mode is not FORMAT_MODE_ANY:
                pass

    # --- YAML / JSON ---
    if fmt_mode in [FORMAT_MODE_ANY, FORMAT_MODE_JSON, FORMAT_MODE_YAML]:
        mode_yj = "{}/{}".format(FORMAT_MODE_YAML, FORMAT_MODE_JSON)
        LOGGER.debug("parsing using mode [{}]".format(mode_yj))
        # noinspection PyBroadException
        try:
            with open(config_file, 'r') as f:
                config = yaml.load(f)
            if not isinstance(config, list):
                config = [config]
            config = AudioConfig(config)
            LOGGER.debug("success using mode [{}]".format(mode_yj))
            return config
        except Exception:
            log_func = LOGGER.warning if fmt_mode is FORMAT_MODE_ANY else LOGGER.exception
            log_func("failed parsing as [{}], moving on...".format(mode_yj))
            if fmt_mode is not FORMAT_MODE_ANY:
                pass

    raise ValueError("no more parsing method available, aborting...")


def write_config(audio_config, file_path, fmt_mode):
    # type: (AudioConfig, AnyStr, FormatInfo) -> None
    """Raw writing operation to dump audio config to file with specified format."""
    all_have_track = all(isinstance(_.track, int) for _ in audio_config)
    audio_config = sorted(audio_config, key=lambda _: _.track if all_have_track else _.title)
    with open(file_path, 'w') as f:
        if fmt_mode is FORMAT_MODE_JSON:
            json.dump(audio_config, f)
        elif fmt_mode is FORMAT_MODE_YAML:
            yaml.dump(audio_config, f)
        elif fmt_mode is FORMAT_MODE_CSV:
            header = list(audio_config[0].keys())
            w = csv.DictWriter(f, fieldnames=header)
            w.writeheader()
            w.writerows(audio_config)
        elif fmt_mode is FORMAT_MODE_TAB:
            max_title_len = len(max(audio_config, key=lambda _: _.title).title)
            max_track_len = 0 if not all_have_track else int(math.log10(max(_.track for _ in audio_config))) + 1
            max_track_dot = max_track_len + 1   # extra space for '.' after track number
            line_fmt = '{track:track_tab}{title:title_tab}{duration}' \
                .replace('title_tab', str(max_title_len)) \
                .replace('track_tab', str(max_track_dot))
            for ac in audio_config:
                f.write(line_fmt.format(
                    track='{}.'.format(ac.track) if all_have_track else '',
                    title=ac.title,
                    duration=ac.duration if ac.duration else '')
                )
        else:
            raise NotImplemented("format [{}] writing to file unknown".format(fmt_mode))


def save_audio_config(audio_config, file_path, mode=FORMAT_MODE_YAML):
    # type: (AudioConfig, AnyStr, Optional[Union[AnyStr, FormatInfo]]) -> bool
    """Saves the audio config if permitted by the OS and using the corrected file extension."""
    fmt_mode = find_mode(mode, format_modes)
    if not mode:
        raise ValueError("invalid output format mode [{}], aborting...".format(mode))
    name, ext = os.path.splitext(file_path)
    if not fmt_mode.matches(ext):
        LOGGER.warning("file extension [{}] doesn't match requested save format [{}], fixing to [{}]."
                       .format(ext, mode, fmt_mode.name))
        ext = fmt_mode.extension
    file_path = "{}{}{}".format(name, '' if ext.startswith('.') else '.', ext)
    if os.path.isfile(file_path):
        os.remove(file_path)
    write_config(audio_config, file_path, fmt_mode)
    return os.path.isfile(file_path)


def get_audio_files(path):
    # type: (AnyStr) -> Iterable[AudioFile]
    """Retrieves all supported audio files from the specified path (file or directory)."""
    if not os.path.isdir(path):
        if os.path.isfile(path):
            path = [path]
        else:
            raise ValueError("invalid path: [{}]".format(path))

    return filter(isMp3File, path)
