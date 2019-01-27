from aiu.typedefs import AudioFile, AudioConfig, Duration
from aiu.utils import get_logger
from eyed3.mp3 import isMp3File
from typing import AnyStr, Dict, Iterable, List, Optional, Union
from datetime import datetime
import string
import yaml
import csv
import six
import os
import re

LOGGER = get_logger()

white_space_no_space = string.whitespace.replace(' ', '')
numbered_list = re.compile(r"^[\s\-#.]*([0-9]+)[\s\-#.]*(.*)")
duration_info = re.compile(r"""     # Match any 'duration' representation, need to filter if many (ex: one in title)
    .*?                                 # non-greedy match on filler (as close as possible)
    ((?:(?:\d*)|(?:[2][0-3])|(?:\d)):   # hours time part of any length (0-inf, not 00-12)
     (?:[0-5]\d)                        # minutes time part (00-59)
     (?::[0-5]\d)?)                     # seconds time part (00-59)
""", re.VERBOSE)

PARSER_MODE_ANY = 'any'
PARSER_MODE_CSV = 'csv'
PARSER_MODE_TAB = 'tab'
PARSER_MODE_JSON = 'json'
PARSER_MODE_YAML = 'yaml'
parser_modes = frozenset([
    PARSER_MODE_ANY,
    PARSER_MODE_CSV,
    PARSER_MODE_TAB,
    PARSER_MODE_JSON,
    PARSER_MODE_YAML,
])
FORMAT_MODE_CSV = PARSER_MODE_CSV
FORMAT_MODE_JSON = PARSER_MODE_JSON
FORMAT_MODE_YAML = PARSER_MODE_YAML
format_modes = frozenset([
    FORMAT_MODE_CSV,
    FORMAT_MODE_JSON,
    FORMAT_MODE_YAML,
])


def clean_fields(config):
    # type: (List[Dict[AnyStr, AnyStr]]) -> AudioConfig
    for i, entry in enumerate(config):
        for field in entry:
            if isinstance(config[i][field], six.string_types):
                config[i][field] = config[i][field].strip(white_space_no_space)
            if field == 'duration' and config[i][field] is not None:
                time_parts = entry['duration'].replace('-', ':').replace('/', ':').split(':')
                h, m, s = [None] + time_parts if len(time_parts) == 2 else time_parts
                config[i][field] = Duration(hours=h, minutes=m, seconds=s)
    return config


def parse_audio_config(config_file, mode=None):
    # type: (AnyStr, Optional[Union[parser_modes]]) -> AudioConfig
    """Attempts various parsing methods to retrieve audio files metadata from a config file."""

    if not os.path.isfile(config_file):
        raise ValueError("invalid file path: [{}]".format(config_file))

    if mode not in parser_modes:
        LOGGER.warning("unknown parser mode [{}], reverting to default [{}].".format(mode, PARSER_MODE_ANY))
        mode = PARSER_MODE_ANY

    # --- YAML / JSON ---
    if mode in [PARSER_MODE_ANY, PARSER_MODE_YAML, PARSER_MODE_JSON]:
        mode_yj = "{}/{}".format(FORMAT_MODE_YAML, PARSER_MODE_JSON)
        LOGGER.debug("parsing using mode '{}'".format(mode_yj))
        # noinspection PyBroadException
        try:
            with open(config_file, 'r') as f:
                config = yaml.load(f)
            config = clean_fields(config if isinstance(config, list) else list(config))
            LOGGER.debug("success using mode '{}'".format(mode_yj))
            return config
        except Exception:
            LOGGER.warning("failed parsing as '{}', moving on...".format(mode_yj))
            pass

    # --- CSV with header row ---
    if mode in [PARSER_MODE_ANY, PARSER_MODE_CSV]:
        LOGGER.debug("parsing using mode '{}'".format(PARSER_MODE_CSV))
        # noinspection PyBroadException
        try:
            with open(config_file, 'r') as f:
                config = clean_fields(list(csv.DictReader(f)))
            LOGGER.debug("success using mode '{}'".format(PARSER_MODE_CSV))
            return config
        except Exception:
            LOGGER.warning("failed parsing as '{}', moving on...".format(PARSER_MODE_CSV))
            pass

    # --- TAB with/without numbering ---
    if mode in [PARSER_MODE_ANY, PARSER_MODE_TAB]:
        LOGGER.debug("parsing using mode '{}'".format(PARSER_MODE_TAB))
        # noinspection PyBroadException
        try:
            with open(config_file, 'r') as f:
                config = f.readlines()
            for i, row in enumerate(config):
                info = re.match(numbered_list, row)
                track, row = info.groups() if info else (None, row)
                info = re.match(duration_info, row)
                # assume the duration is the last info if multiple matches
                duration, row = info.groups()[-1] if info else (None, row)
                # noinspection PyTypeChecker
                config[i] = {
                    'track': track,
                    'title': row,
                    'duration': duration,
                }
            if not all([isinstance(c, dict) for c in config]):
                raise ValueError("invalid parsing result as '{}', moving on...".format(PARSER_MODE_TAB))
            # noinspection PyTypeChecker
            config = clean_fields(config)
            LOGGER.debug("success using mode '{}'".format(PARSER_MODE_TAB))
            return config
        except Exception:
            LOGGER.warning("failed parsing as '{}', moving on...".format(PARSER_MODE_TAB))
            pass

    raise ValueError("no more parsing method available, aborting...")


def save_audio_config(audio_config, file_path, mode=FORMAT_MODE_YAML):
    # type: (AudioConfig, AnyStr, Optional[Union[format_modes]]) -> bool
    if mode not in format_modes:
        raise ValueError("invalid output format mode [{}], aborting...".format(mode))
    os.remove(file_path)
    with open(file_path, 'w'):
        raise NotImplemented
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
