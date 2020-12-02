from aiu.typedefs import AudioFileAny, AudioFile, CoverFileAny, CoverFile, LoggerType
from aiu import LOGGER
from typing import AnyStr, Callable, Iterable, List, Optional, Union
from PIL import Image
from functools import wraps
import eyed3
import os
import six
import shutil


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
    # type: (AnyStr, Union[List[AnyStr], AnyStr], Optional[Union[List[AnyStr], AnyStr]]) -> Union[AnyStr, None]
    """
    Looks in `path` for any file matching any of the `names`.

    :returns: full path of first matching occurrence, or `None`.
    """
    names = allowed_names if isinstance(allowed_names, (list, set)) else [allowed_names]
    if allowed_extensions:
        allowed_extensions = allowed_extensions if isinstance(allowed_extensions, (list, set)) else [allowed_extensions]
    contents = sorted(os.listdir(path))
    for c in contents:
        c_name, c_ext = os.path.splitext(c)
        if c_name in names and c_ext != "":
            if not allowed_extensions or c_ext in allowed_extensions:
                return os.path.abspath(os.path.join(path, c))
    return None


def backup_files(file_paths, backup_dir):
    # type: (Iterable[AnyStr], AnyStr) -> None
    os.makedirs(backup_dir, exist_ok=True)
    for file_path in file_paths:
        copy_path = os.path.join(backup_dir, os.path.split(file_path)[-1])
        LOGGER.debug("Backup [%s]", copy_path)
        shutil.copyfile(file_path, copy_path)


def get_audio_file(audio_file):
    # type: (AudioFileAny) -> AudioFile
    if isinstance(audio_file, six.string_types):
        audio_file = eyed3.load(audio_file)
    if not isinstance(audio_file, AudioFile):
        raise TypeError("Audio file expected.")
    return audio_file


def get_cover_file(cover_file):
    # type: (CoverFileAny) -> CoverFile
    if isinstance(cover_file, six.string_types):
        cover_file = Image.open(cover_file)
    if not isinstance(cover_file, CoverFile):
        raise TypeError("Cover file expected.")
    return cover_file


def validate_output_file(output_file_path, search_path, default_name='output.cfg'):
    # type: (AnyStr, AnyStr, Optional[AnyStr]) -> AnyStr
    if not output_file_path:
        output_file_path = os.path.join(search_path, default_name)
    output_file_path = os.path.abspath(output_file_path)
    if not os.path.isdir(os.path.dirname(output_file_path)):
        raise ValueError("invalid save location: [{}]".format(output_file_path))
    return output_file_path
