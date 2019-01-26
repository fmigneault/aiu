from eyed3.mp3 import isMp3File
from typing import AnyStr, Iterable, TYPE_CHECKING
from datetime import datetime
import warnings
import string
import yaml
import csv
import six
import os
import re

if TYPE_CHECKING:
    from aiu.typedefs import AudioFile, AudioConfig

white_space_no_space = string.whitespace.replace(' ', '')
numbered_list = re.compile(r"^[\s\-#.]*([0-9]+)[\s\-#.]*(.*)$")
duration_info = re.compile()    # TODO


def clean_fields(config):
    # type: (AudioConfig) -> AudioConfig
    for i, entry in enumerate(config):
        for field in entry:
            if isinstance(config[i][field], six.string_types):
                config[i][field] = config[i][field].strip(white_space_no_space)
            if field == 'duration' and config[i][field] is not None:
                time_str = entry['duration'].replace('-', ':').replace('/', ':')
                if time_str.count(':') == 2:
                    config[i][field] = datetime.strptime(time_str, '%M:%S').time()
                else:
                    config[i][field] = datetime.strptime(time_str, '%H:%M:%S').time()
    return config


def parse_audio_config(config_file):
    # type: (AnyStr) -> AudioConfig
    """Attempts various parsing methods to retrieve audio files metadata from a config file."""

    if not os.path.isfile(config_file):
        raise ValueError("invalid file path: [{}]".format(config_file))

    # --- YAML / JSON ---
    # noinspection PyBroadException
    try:
        with open(config_file, 'r') as f:
            config = yaml.load(f)
        return clean_fields(config if isinstance(config, list) else list(config))
    except Exception:
        warnings.warn("failed parsing as YAML/JSON, moving on...")
        pass

    # --- CSV with header row ---
    # noinspection PyBroadException
    try:
        with open(config_file, 'r') as f:
            return clean_fields(list(csv.DictReader(f)))
    except Exception:
        warnings.warn("failed parsing as CSV, moving on...")
        pass

    # --- TAB with/without numbering ---
    # noinspection PyBroadException
    try:
        with open(config_file, 'r') as f:
            config = f.readlines()
        for i, row in enumerate(config):
            info = re.match(numbered_list, row)
            track, row = info.groups() if info else (None, row)
            info = re.match(duration_info, row)
            duration, row = info.groups() if info else (None, row)
            config[i] = {
                'track': track,
                'title': row,
                'duration': duration,
            }
        return clean_fields(config)
    except Exception:
        warnings.warn("failed parsing as TAB, moving on...")
        pass

    raise ValueError("no more parsing method available, aborting...")


def get_audio_files(path):
    # type: (AnyStr) -> Iterable[AudioFile]
    """Retrieves all supported audio files from the specified path (file or directory)."""
    if not os.path.isdir(path):
        if os.path.isfile(path):
            path = [path]
        else:
            raise ValueError("invalid path: [{}]".format(path))

    return filter(isMp3File, path)
