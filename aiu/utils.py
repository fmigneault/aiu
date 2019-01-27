from aiu.typedefs import AudioFileAny, AudioFile, CoverFileAny, CoverFile
from aiu import __meta__
from typing import AnyStr, List, Optional, Union
from PIL import Image
import logging
import eyed3
import six
import os


# noinspection PyProtectedMember
def get_logger():
    # type: (...) -> logging._loggerClass
    logger_extra = {'path': os.path.curdir}
    logger_format = "[%(name)s] %(asctime)-15s %(levelname)-8s %(message)s [path: '%(path)s']"
    logging.basicConfig(format=logger_format)
    logger = logging.getLogger(__meta__.__package__)
    logger_handler = logging.StreamHandler()
    logger_handler.setFormatter(logger_format)
    logger.addHandler(logger_handler)
    logging.LoggerAdapter(logger, logger_extra)
    return logger


def look_for_default_file(path, names):
    # type: (AnyStr, Union[List[AnyStr], AnyStr]) -> Union[AnyStr, None]
    """
    Looks in `path` for any file matching any of the `names`.
    :returns: first matching occurrence, or `None`.
    """
    names = names if isinstance(names, list) else [names]
    contents = sorted(os.listdir(path))
    for c in contents:
        c_name, c_ext = os.path.splitext(c)
        if c_name in names and c_ext != '':
            return c
    return None


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
