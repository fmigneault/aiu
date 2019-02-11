from aiu.parser import (
    get_audio_files,
    save_audio_config,
    parse_audio_config,
    parser_modes,
    format_modes,
    FORMAT_MODE_ANY,
    FORMAT_MODE_YAML,
)
from aiu.updater import merge_audio_configs, apply_audio_config
from aiu.utils import look_for_default_file, validate_output_file, get_logger
from aiu.typedefs import AudioConfig
from aiu import __meta__
from typing import AnyStr, Optional, Union
from docopt import docopt
from logging import INFO
import os

LOGGER = get_logger()


def main(search_path=None,              # type: Optional[AnyStr]
         info_file=None,                # type: Optional[AnyStr]
         all_info_file=None,            # type: Optional[AnyStr]
         cover_file=None,               # type: Optional[AnyStr]
         parser_mode=FORMAT_MODE_ANY,   # type: Optional[Union[parser_modes]]
         output_mode=FORMAT_MODE_YAML,  # type: Optional[Union[format_modes]]
         logger_level=INFO,             # type: Optional[Union[AnyStr, int]]
         output_file=None,              # type: Optional[AnyStr]
         ):                             # type: (...) -> AudioConfig
    """Audio Info Updater (aiu)
    Main process for updating audio files metadata from parsed configuration files.

    All arguments defining specific metadata fields (`artist`, `year`, `cover`, etc.) override any matching
    information fields found in configurations files (`info`, `all`).
    Applied changes are saved to `output` file.

    Usage:
        aiu [-h] [--help] [-f FILE | -p PATH] [-i INFO | -c CONFIG] [-a ALL] [--image IMAGE | --cover COVER]
            [--artist ARTIST] [--title TITLE] [--album ALBUM] [--album-artist ALBUM_ARTIST] [--year YEAR]
            [--genre GENRE] [--parser PARSER] [-o OUTPUT] [--format FORMAT] [--quiet | --warn | --verbose | --debug]
        aiu --help
        aiu --version

    Options:
        -h --help                           Show this help message.

        --version                           Show the package version.

        -f --file                           Path to a single audio file to edit metadata.

        -p --path="."                       Path where to search for audio and metadata info files to process.

        -i --info="<path>/info.*"           Path to audio metadata info file to be applied to matched audio files.
                                            (default: looks for any text file format named `info`, `config` or `meta`
                                            under `path`, any first match).

        -c --config                         Alias for `--info`. See corresponding details.

        -a --all="<path>/all.*"             Path to audio info file of metadata to apply to all matched audio files.
                                            (default: looks for any text file compatible format named `all`, `any` or
                                            `every` under `path`, any first match).

        --cover="<path>/cover.*"            Path where to find image file to use as audio file album cover.
                                            (default: locks for any image compatible format named `cover`, `artwork`
                                            or `art` under `path`, any first match).

        --image=IMAGE                       Alias for `--cover`. See corresponding details.

        --title TITLE                       Name to apply as `title` metadata attribute to single or many audio files.

        --year YEAR                         Name to apply as `year` metadata attribute to single or many audio files.

        --genre GENRE                       Name to apply as `genre` metadata attribute to single or many audio files.

        --artist ARTIST                     Name to apply as `artist` metadata attribute to single or many audio files.

        --album ALBUM                       Name to apply as `album` metadata attribute to single or many audio files.

        --album-artist ALBUM_ARTIST         Name to apply as `album-artist` metadata attribute to single or many audio
                                            files. If not provided, but `artist` can be found via `--artist` or some
                                            configuration file, the same value is employed unless also providing the
                                            `--no-match-album-artist` argument.

        --no-match-album-artist             Don't use the `album-artist` metadata as `artist` when missing.
                                            See argument `--album-artist`.

        --parser=any                        Parsing mode to enforce, one of [any, csv, tab, json, yaml].

        -o --output="<path>/output.cfg"     Location where to save applied output configurations. Directory must exist.

        --format=yaml                       Format to output applied metadata information, one of [csv, json, yaml].

        -q --quiet                          Do not provide any logging details.

        -w --warn                           Provide minimal logging details (warnings and errors only).

        -v --verbose                        Provide additional information logging.

        -d --debug                          Provide even more logging details (enable debug information).

    Examples:
        aiu
        aiu --path="<specific-dir-path>"
        aiu --cover="<path-to-cover>/some-album-cover.jpg"

    """
    LOGGER.setLevel(logger_level)
    # noinspection PyBroadException
    try:
        search_path = os.path.abspath(search_path or os.path.curdir)
        cfg_info_file = info_file if info_file else look_for_default_file(search_path, ['info', 'config'])
        all_info_file = all_info_file if all_info_file else look_for_default_file(search_path, ['all', 'any', 'every'])
        cover_file = cover_file if cover_file else look_for_default_file(cover_file, ['covert', 'artwork'])
        output_file = validate_output_file(output_file, search_path, default_name='output.cfg')
        audio_files = get_audio_files(search_path)
        cfg_audio_config = parse_audio_config(cfg_info_file, mode=parser_mode)
        all_audio_config = parse_audio_config(all_info_file, mode=parser_mode)
        audio_config = merge_audio_configs([
            (cfg_audio_config, False), (all_audio_config, True), ([{'cover': cover_file}], True)
        ])
        output_config = apply_audio_config(audio_files, audio_config)
        if not save_audio_config(output_config, output_file, mode=output_mode):
            LOGGER.error("Failed saving file, but no unhandled exception occurred.")
        return output_config
    except Exception:
        LOGGER.exception("unhandled exception")


def cli():
    args = docopt(main.__doc__, version=__meta__.__version__)
    main(**args)


if __name__ == '__main__':
    cli()
