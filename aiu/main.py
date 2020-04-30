from aiu.parser import (
    get_audio_files,
    save_audio_config,
    parse_audio_config,
    parser_modes,
    format_modes,
    FORMAT_MODE_ANY,
    FORMAT_MODE_YAML,
)
from aiu.updater import merge_audio_configs, apply_audio_config, update_file_names
from aiu.utils import look_for_default_file, validate_output_file, get_logger, log_exception
from aiu.typedefs import AudioConfig, Duration
from aiu import __meta__, tags as t
from typing import AnyStr, Optional, Union
from inspect import signature
from docopt import docopt
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL, NOTSET
import sys
import os

LOGGER = get_logger()


@log_exception(LOGGER)
def main(
         # --- file/parsing options ---
         search_path=None,              # type: Optional[AnyStr]
         info_file=None,                # type: Optional[AnyStr]
         all_info_file=None,            # type: Optional[AnyStr]
         cover_file=None,               # type: Optional[AnyStr]
         output_file=None,              # type: Optional[AnyStr]
         output_mode=FORMAT_MODE_YAML,  # type: Union[format_modes]
         parser_mode=FORMAT_MODE_ANY,   # type: Union[parser_modes]
         logger_level=INFO,             # type: Union[AnyStr, int],
         # --- specific meta fields ---
         artist=None,                   # type: Optional[AnyStr]
         album=None,                    # type: Optional[AnyStr]
         album_artist=None,             # type: Optional[AnyStr]
         title=None,                    # type: Optional[AnyStr]
         track=None,                    # type: Optional[int]
         genre=None,                    # type: Optional[AnyStr]
         duration=None,                 # type: Optional[Union[Duration, AnyStr]]
         year=None,                     # type: Optional[int]
         match_artist=True,             # type: bool
         # --- other operation flags ---
         rename_format=False,           # type: Optional[AnyStr]
         rename_title=False,            # type: bool
         prefix_track=False,            # type: bool
         dry=False,                     # type: bool
         ):                             # type: (...) -> AudioConfig
    LOGGER.setLevel(logger_level)
    search_path = '.' if search_path == "'.'" else search_path  # default provided as literal string with quotes
    search_path = os.path.abspath(search_path or os.path.curdir)
    LOGGER.info("Search path is: [%s]", search_path)
    cfg_info_file = info_file if info_file else look_for_default_file(search_path, ['info', 'config', 'meta'])
    LOGGER.info("Matched config 'info' file: [%s]", cfg_info_file)
    all_info_file = all_info_file if all_info_file else look_for_default_file(search_path, ['all', 'any', 'every'])
    LOGGER.info("Matched config 'all' file: [%s]", all_info_file)
    cover_file = cover_file if cover_file else look_for_default_file(cover_file, ['covert', 'artwork'])
    LOGGER.info("Matched cover image file: [%s]", cover_file)
    output_file = validate_output_file(output_file, search_path, default_name='output.cfg')
    LOGGER.info("Output config file %s be: [%s]", 'would' if dry else 'will', output_file)
    audio_files = get_audio_files(search_path)
    LOGGER.info("Found audio files to process:\n  %s", "\n  ".join(audio_files))
    config_combo = []
    if cfg_info_file:
        LOGGER.info("Running audio config parsing...")
        cfg_audio_config = parse_audio_config(cfg_info_file, mode=parser_mode)
        config_combo.append((False, cfg_audio_config))
    if all_info_file:
        LOGGER.info("Running audio 'all' config parsing...")
        all_audio_config = parse_audio_config(all_info_file, mode=parser_mode)
        config_combo.append((True, all_audio_config))
    literal_fields = {
        t.TAG_ALBUM: album, t.TAG_ALBUM_ARTIST: album_artist, t.TAG_ARTIST: artist, t.TAG_TITLE: title,
        t.TAG_TRACK: track, t.TAG_DURATION: duration, t.TAG_GENRE: genre, t.TAG_YEAR: year,
    }
    literal_fields = dict((k, v) for k, v in literal_fields.items() if v is not None)
    if cover_file:
        config_combo.append((True, {'cover': cover_file}))
    if literal_fields:
        LOGGER.info("Literal fields to apply: [%s]", literal_fields)
        config_combo.append((True, literal_fields))
    if not config_combo:
        LOGGER.error("Couldn't find any config to process.")
        sys.exit(-1)
    LOGGER.info("Resolving metadata config fields...")
    LOGGER.debug("Match artist parameter: %s", match_artist)
    audio_config = merge_audio_configs(config_combo, match_artist)
    LOGGER.info("Applying config...")
    output_config = apply_audio_config(audio_files, audio_config, dry=dry)
    output_config = update_file_names(output_config, rename_format, rename_title, prefix_track, dry=dry)
    if not save_audio_config(output_config, output_file, mode=output_mode, dry=dry):
        if not dry:  # when dry mode, it is normal that the file was not written
            LOGGER.error("Failed saving file, but no unhandled exception occurred.")
    LOGGER.info("Operation complete.")
    return output_config


def cli():
    """Audio Info Updater (aiu)
    Main process for updating audio files metadata from parsed configuration files.

    All options defining specific metadata fields (`artist`, `year`, etc.) override any matching
    information fields found in configurations files via options `info` or `all`.
    Applied changes are saved to `output` file.

    Usage:
        aiu [-h] [--help] [-p PATH | -f FILE] [-i INFO] [-a ALL] [--image IMAGE | --cover COVER]
            [--artist ARTIST] [--title TITLE] [--album ALBUM] [--album-artist ALBUM_ARTIST] [--year YEAR]
            [--genre GENRE] [--parser PARSER] [-o OUTPUT] [--format FORMAT]
            [--rename-format | --rename-title [--prefix-track]]
            [--quiet | --warn | --verbose | --debug] [--dry]
        aiu --help
        aiu --version

    Options:

        Generic Arguments
        =================

        -h, --help                      Show this help message.

        --version                       Show the package version.

        Parsing Arguments
        ===================

        -p, --path PATH                 Path where to search for audio and metadata info files to process.
                                        [default: '.'] (current directory)

        -f, --file FILE                 Path to a single audio file to edit metadata. (default: `path`)

        -i, --info INFO                 Path to audio metadata info file to be applied to matched audio files.
                                        (default: looks for text file compatible format named `info`, `config` or
                                        `meta` under `path`, uses the first match with ``any`` format).

        -a, --all ALL                   Path to audio info file of metadata to apply to all matched audio files.
                                        (default: looks for text file compatible format named `all`, `any` or
                                        `every` under `path`, uses the first match with ``any`` format).

        --parser PARSER                 Parsing mode to enforce, one of ``[any, csv, tab, json, yaml]``.
                                        [default: any]

        -o, --output OUTPUT             Location where to save applied output configurations. Directory must exist.
                                        (default: `output.cfg` located under `path`).

        --format FORMAT                 Output format of applied metadata details, one of ``[csv, json, yaml, raw]``.
                                        [default: yaml]

        Operation Arguments
        ===================

        --dry                           Do not do any modification, just pretend.
                                        (note: works best when combined with ``--verbose`` or ``--debug``)

        --rename-title                  Specifies to rename matched audio files with their corresponding ``TITLE``.
                                        This is equivalent to ``--rename-format '%(TITLE)s'``.

        --prefix-track                  Specifies to prefix the file name with ``TRACK`` when combined with
                                        ``--rename-title`` option.
                                        This is equivalent to ``--rename-format '%(TRACK)s %(TITLE)s'``.

        --rename-format FORMAT          Specify the specific ``FORMAT`` to employ for renaming files.
                                        Formatting follows the %-style syntax. Supported arguments are the below
                                        tags except image-related items.

        ID3 Tags Arguments
        ==================

        --cover COVER                   Path where to find image file to use as audio file album cover.
                                        (default: locks for image compatible format named `cover`, `artwork` or `art`
                                        under `path`, uses the first match).

        --image IMAGE                   Alias for ``--cover``. See corresponding details.


        --title TITLE                   Name to apply as ``TAG_TITLE`` metadata attribute to file(s).

        --track TRACK                   Name to apply as ``TAG_TRACK`` metadata attribute to file(s).

        --year YEAR                     Name to apply as ``TAG_YEAR`` metadata attribute to file(s).

        --duration DURATION             Name to apply as ``TAG_DURATION`` metadata attribute to file(s).

        --genre GENRE                   Name to apply as ``TAG_GENRE`` metadata attribute to file(s).

        --artist ARTIST                 Name to apply as ``TAG_ARTIST`` metadata attribute to file(s).

        --album ALBUM                   Name to apply as ``TAG_ALBUM`` metadata attribute to file(s).

        --album-artist ALBUM_ARTIST     Name to apply as ``TAG_ALBUM_ARTIST`` metadata attribute to audio file(s).
                                        If not provided, but ``TAG_ARTIST`` can be found via option `artist` or some
                                        configuration file (`info` or `all`), the same value is employed
                                        unless also providing option `no-match-artist`.

        --no-match-artist               Don't use the ``TAG_ARTIST`` metadata as ``TAG_ALBUM_ARTIST`` when missing.
                                        See option `album-artist`.

        Logging Arguments
        =================

        -q, --quiet                     Do not provide any logging details.

        -w, --warn                      Provide minimal logging details (warnings and errors only).

        -v, --verbose                   Provide additional information logging.

        -d, --debug                     Provide even more logging details (enable debug information).

    Examples::

        aiu
        aiu --path "<specific-dir-path>"
        aiu --cover "<path-to-cover>/some-album-cover.jpg"

    """
    # noinspection PyTypeChecker
    args = sys.argv[1:] or "--help"
    args = docopt(cli.__doc__, argv=args, help=True, version=__meta__.__version__)

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
        'match_artist': not args.pop('no_match_artist', False),
    })
    sig = signature(main, follow_wrapped=True)
    args = dict((k, v) for k, v in args.items() if k in sig.parameters)
    main(**args)


if __name__ == '__main__':
    cli()
