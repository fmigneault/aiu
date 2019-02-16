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
from inspect import signature
from docopt import docopt
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL, NOTSET
import os

LOGGER = get_logger()


def main(
         # --- file/parsing options ---
         search_path=None,              # type: Optional[AnyStr]
         info_file=None,                # type: Optional[AnyStr]
         all_info_file=None,            # type: Optional[AnyStr]
         cover_file=None,               # type: Optional[AnyStr]
         output_file=None,              # type: Optional[AnyStr]
         output_mode=FORMAT_MODE_YAML,  # type: Optional[Union[format_modes]]
         parser_mode=FORMAT_MODE_ANY,   # type: Optional[Union[parser_modes]]
         logger_level=INFO,             # type: Optional[Union[AnyStr, int]],
         # --- specific meta fields ---
         artist=None,                   # type: Optional[AnyStr]
         album=None,                    # type: Optional[AnyStr]
         album_artist=None,             # type: Optional[AnyStr]
         title=None,                    # type: Optional[AnyStr]
         genre=None,                    # type: Optional[AnyStr]
         year=None,                     # type: Optional[int]
         no_match_artist=False,         # type: Optional[bool]
         ):                             # type: (...) -> AudioConfig
    LOGGER.setLevel(logger_level)
    # noinspection PyBroadException
    try:
        search_path = os.path.abspath(search_path or os.path.curdir)
        cfg_info_file = info_file if info_file else look_for_default_file(search_path, ['info', 'config', 'meta'])
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
    """Audio Info Updater (aiu)
    Main process for updating audio files metadata from parsed configuration files.

    All arguments defining specific metadata fields (`artist`, `year`, `cover`, etc.) override any matching
    information fields found in configurations files (`config`, `info`, `all`).
    Applied changes are saved to `output` file.

    Usage:
        aiu [-h] [--help] [-p PATH | -f FILE] [-i INFO] [-a ALL] [--image IMAGE | --cover COVER]
            [--artist ARTIST] [--title TITLE] [--album ALBUM] [--album-artist ALBUM_ARTIST] [--year YEAR]
            [--genre GENRE] [--parser PARSER] [-o OUTPUT] [--format FORMAT] [--quiet | --warn | --verbose | --debug]
        aiu --help
        aiu --version

    Options:
        -h, --help                      Show this help message.

        --version                       Show the package version.

        -p, --path PATH                 Path where to search for audio and metadata info files to process.
                                        [default: .]

        -f, --file FILE                 Path to a single audio file to edit metadata. (default: use `path`)

        -i, --info INFO                 Path to audio metadata info file to be applied to matched audio files.
                                        (default: looks for any text file format named `info`, `config` or `meta`
                                        under `path`, any first match).

        -a, --all ALL                   Path to audio info file of metadata to apply to all matched audio files.
                                        (default: looks for any text file compatible format named `all`, `any` or
                                        `every` under `path`, any first match).

        --cover COVER                   Path where to find image file to use as audio file album cover.
                                        (default: locks for any image compatible format named `cover`, `artwork`
                                        or `art` under `path`, any first match).

        --image IMAGE                   Alias for `--cover`. See corresponding details.

        --title TITLE                   Name to apply as `title` metadata attribute to file(s).

        --year YEAR                     Name to apply as `year` metadata attribute to file(s).

        --genre GENRE                   Name to apply as `genre` metadata attribute to file(s).

        --artist ARTIST                 Name to apply as `artist` metadata attribute to file(s).

        --album ALBUM                   Name to apply as `album` metadata attribute to file(s).

        --album-artist ALBUM_ARTIST     Name to apply as `album-artist` metadata attribute to audio file(s).
                                        If not provided, but `artist` can be found via `--artist` or some
                                        configuration file (`--info` or `--all`), the same value is employed
                                        unless also providing `--no-match-artist` argument.

        --no-match-artist               Don't use the `artist` metadata as `album-artist` when missing.
                                        See argument `--album-artist`.

        --parser PARSER                 Parsing mode to enforce, one of [any, csv, tab, json, yaml].
                                        [default: any]

        -o, --output OUTPUT             Location where to save applied output configurations. Directory must exist.
                                        (default: `output.cfg` located under `path`).

        --format FORMAT                 Format to output applied metadata information, one of [csv, json, yaml].
                                        [default: yaml]

        -q, --quiet                     Do not provide any logging details.

        -w, --warn                      Provide minimal logging details (warnings and errors only).

        -v, --verbose                   Provide additional information logging.

        -d, --debug                     Provide even more logging details (enable debug information).

    Examples:
        aiu
        aiu --path="<specific-dir-path>"
        aiu --cover="<path-to-cover>/some-album-cover.jpg"

    """
    # noinspection PyTypeChecker
    args = docopt(cli.__doc__, help=True, version=__meta__.__version__)

    # substitute args names as required, and remove '--'
    args_keys = list(args)
    for arg in args_keys:
        args[arg.replace('--', '').replace('-', '_')] = args.pop(arg)
    logger_level = NOTSET
    for arg, lvl in [('debug', DEBUG), ('verbose', INFO), ('warn', WARNING), ('quiet', CRITICAL)]:
        if args.pop(arg, False):
            logger_level = lvl
    args.update({
        'search_path': args.pop('path', None) or args.pop('file', None),
        'info_file': args.pop('info'),
        'all_info_file': args.pop('all'),
        'cover_file': args.pop('cover', None) or args.pop('image', None),
        'output_file': args.pop('output'),
        'output_mode': args.pop('format'),
        'parser_mode': args.pop('parser'),
        'logger_level': logger_level or ERROR,
    })
    sig = signature(main)
    args = dict((k, v) for k, v in args.items() if k in sig.parameters)
    main(**args)


if __name__ == '__main__':
    cli()
