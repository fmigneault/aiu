import os
import re
import shutil
from functools import wraps
from typing import Callable, Iterable, List, Optional, Union

import eyed3
from PIL import Image

from aiu.typedefs import AudioConfig, AudioFileAny, AudioFile, AudioInfo, CoverFileAny, CoverFile, LoggerType
from aiu import LOGGER


def log_exception(logger=None):
    # type: (LoggerType) -> Callable
    """Decorator that logs an exception on raise within the passed ``function``."""
    if not isinstance(logger, LoggerType):
        logger = LOGGER

    def decorator(function):
        @wraps(function)
        def log_exc(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except Exception as ex:
                logger.exception("{!r}".format(ex))
        return log_exc
    return decorator


def look_for_default_file(path, allowed_names, allowed_extensions=None):
    # type: (str, Union[List[str], str], Optional[Union[List[str], str]]) -> Union[str, None]
    """
    Looks in `path` for any file matching any of the `names`.

    :returns: full path of first matching occurrence, or `None`.
    """
    names = allowed_names if isinstance(allowed_names, (list, set)) else [allowed_names]
    if allowed_extensions and isinstance(allowed_extensions, str):
        allowed_extensions = [allowed_extensions]
    contents = sorted(os.listdir(path))
    for c in contents:
        c_name, c_ext = os.path.splitext(c)
        c_ext = c_ext.replace(".", "")
        if c_name in names and c_ext != "":
            if not allowed_extensions or c_ext in allowed_extensions:
                return os.path.abspath(os.path.join(path, c))
    return None


def backup_files(file_paths, backup_dir):
    # type: (Iterable[str], str) -> None
    make_dirs_cleaned(backup_dir, exist_ok=True)
    for file_path in file_paths:
        copy_path = os.path.join(backup_dir, os.path.split(file_path)[-1])
        LOGGER.debug("Backup [%s]", copy_path)
        shutil.copyfile(file_path, copy_path, follow_symlinks=True)


def get_audio_file(audio_file):
    # type: (AudioFileAny) -> AudioFile
    if isinstance(audio_file, str):
        audio_file = eyed3.load(audio_file)
    if not isinstance(audio_file, AudioFile):
        raise TypeError("Audio file expected.")
    return audio_file


def get_cover_file(cover_file):
    # type: (CoverFileAny) -> CoverFile
    if isinstance(cover_file, str):
        cover_file = Image.open(cover_file)
    if not isinstance(cover_file, CoverFile):
        raise TypeError("Cover file expected.")
    return cover_file


def save_cover_file(config, output_dir):
    # type: (AudioConfig, str) -> None
    """
    Searches for any album image cover file within the audio configuration files and saves it.

    Only saves the first match, assuming all audio files belong to the same album and share the same cover.
    """
    path = os.path.join(output_dir, "cover.png")
    for cfg in config:  # type: AudioInfo
        if cfg.cover is not None:
            if os.path.isfile(path):
                LOGGER.warning("Could not save cover image, file already exists: [%s]", path)
                return
            LOGGER.warning("Saved cover image: [%s]", path)
            cfg.cover.save(path)
            return
    LOGGER.warning("Could not find any cover image to save. Operation skipped.")


def validate_output_file(output_file_path, search_path, default_name="output.cfg"):
    # type: (str, str, Optional[str]) -> str
    if not output_file_path:
        output_file_path = os.path.join(search_path, default_name)
    output_file_path = os.path.abspath(output_file_path)
    if os.path.isdir(output_file_path):
        output_dir = output_file_path
        output_file_path = os.path.join(output_dir, default_name)
    else:
        output_dir = os.path.dirname(output_file_path)
    if not os.path.isdir(output_dir):
        LOGGER.debug("Missing output save location, creating it: [%s]", output_file_path)
        make_dirs_cleaned(output_dir)
    return output_file_path


def make_dirs_cleaned(path, replace="-", exist_ok=True, mode=0o755):
    """
    Performs directory creation after cleanup of invalid characters in the path.
    """
    assert len(replace) == 1
    new_path = path = os.path.normpath(os.path.abspath(path))
    if not os.path.exists(path):
        dir_path = path
        parts = []
        while True:
            top_path, dir_path = os.path.split(dir_path)
            if not top_path or not dir_path:
                break
            parts.append(re.sub(r"[^\w\-_\. ]", replace, dir_path))
            dir_path = top_path
            if os.path.isdir(top_path):
                break
        new_path = os.path.join(top_path, os.path.sep.join(reversed(parts)))
        LOGGER.debug("Replaced directory path [%s] => [%s]", parts, new_path)
    os.makedirs(new_path, mode=mode, exist_ok=exist_ok)
