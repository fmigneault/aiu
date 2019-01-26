from aiu.parser import get_audio_files, get_audio_configs
from aiu.utils import look_for_default_file
from aiu.typedefs import AudioConfig
from typing import AnyStr, Optional
import os


def AudioInfoUpdater(search_path=None,      # type: Optional[AnyStr]
                     info_file=None,        # type: Optional[AnyStr]
                     all_info_file=None,    # type: Optional[AnyStr]
                     image_file=None,       # type: Optional[AnyStr]
                     ):                     # type: (...) -> AudioConfig
    """Audio Info Updater
    Main process for updating audio files metadata from parsed configuration files.

    :return:

    .. seealso:
        `aiu.cli.py` for details of corresponding input arguments.
    """
    parser.add_argument('--path', type=str, default=".",
                        help="Path where to search for audio file(s) to process.")
    parser.add_argument('--info', type=str, default="./info.*",
                        help="Path where to find audio info file.")
    parser.add_argument('--all', type=str, default="./all.*",
                        help="Path where to find audio info file applicable to every file(s).")


    search_path = os.path.abspath(search_path or os.path.curdir)
    info_file = info_file if info_file else look_for_default_file(search_path, ['info', 'config'])
    all_info_file = all_info_file if all_info_file else look_for_default_file(search_path, ['all', 'any', 'every'])

    cfg_file = os.path.join(os.path.curdir, 'info.cfg')

    audio_files = get_audio_files(path)



if __name__ == '__main__':
    AudioInfoUpdater()
