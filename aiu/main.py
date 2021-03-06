#!/usr/bin/env python
"""
Main process for updating audio files metadata from parsed configuration files.

All options defining specific metadata fields (``--artist``, ``--year``, etc.) override any
corresponding information fields found in configurations files from options ``--info`` or ``--all``.
Applied changes listed in ``--output`` file.
"""
import argparse
import os
import sys
from typing import List, Optional, Union, Tuple
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL, NOTSET

import aiu
from aiu import DEFAULT_EXCEPTIONS_CONFIG, DEFAULT_STOPWORDS_CONFIG, LOGGER, TRACE, __meta__, tags as t
from aiu.parser import (
    ALL_IMAGE_EXTENSIONS,
    ALL_PARSER_EXTENSIONS,
    FORMAT_MODE_ANY,
    FORMAT_MODE_YAML,
    FORMAT_MODES,
    PARSER_MODES,
    get_audio_files,
    load_config,
    parse_audio_config,
    save_audio_config
)
from aiu.updater import merge_audio_configs, apply_audio_config, update_file_names
from aiu.utils import backup_files, look_for_default_file, validate_output_file, log_exception
from aiu.typedefs import AudioConfig, Duration
from aiu.youtube import fetch_files, get_metadata


def cli():
    _PROG = "aiu"
    _NAME = "Audio Info Updater ({})".format(_PROG)
    _DESC = "{}. {}".format(_NAME, __doc__)
    _HELP_FORMAT = """{} Format Modes
    
    Below are the applicable format modes for format/parser options. 
    Note that not all modes necessarily apply to both. 
    Refer to their option of applicable values.
    
        ``any``
            Attempts to automatically determine which of the formats to apply based
            on the contents of the provided information file. If this is causing
            problems, switch to explicit specification of the provided format.
    
        ``csv``
            Expects an header row indicating the fields retrieved on following lines.
            Then, each line provide an entry to attempt matching against an audio file.
    
        ``tab``
            Takes a plain list of (any amount of) tab delimited rows where each one
            represents a potential audio file to find. Rows are expected to have
            following format (bracket fields are optional):
    
                [track]     title       duration
    
        ``json`` / ``yaml``
            Standard representation of corresponding formats of a list of objects.
            Each object provides fields and values to attempt match against audio files.
            Fields names correspond to the lower case values
    
        ``list``
            Parses a plain list with each field placed on a separate row. Rows are
            expected to provide continuous intervals between corresponding field, as
            presented below, for each audio files to attempt match. Corresponding fields 
            must be provided for each entry. Either one or both of the TRACK/DURATION 
            fields are mandatory.
    
                [track-1]
                title-1
                [duration-1]
                [track-2]
                title-2
                [duration-2]
                ...
    """.format(_NAME)

    try:
        ap = argparse.ArgumentParser(prog=_PROG, description=_DESC, add_help=False,
                                     formatter_class=lambda prog: argparse.HelpFormatter(prog, width=120))
        gen_args = ap.add_argument_group(title="General Arguments",
                                         description="Arguments that provides information about the application "
                                                     "or usage related details.")
        gen_args.add_argument("--help", "-h", action="help", help="Display this help message.")
        gen_args.add_argument("--help-format", action="store_true",
                              help="Display additional help details about formatter/parser modes.")
        gen_args.add_argument("--version", action="version", version=__meta__.__version__,
                              help="Display the program's version.")
        parser_args = ap.add_argument_group(title="Parsing Arguments",
                                            description="Arguments that control parsing methodologies and "
                                                        "configurations to update matched audio files metadata.")
        parser_args.add_argument("-l", "--link", "--youtube", dest="link",
                                 help="YouTube music link from where to retrieve songs and album metadata. "
                                      "When provided, other options will override whichever tag information was "
                                      "automatically obtained from the URL reference.")
        parser_args.add_argument("-p", "--path", "-f", "--file", default=".", dest="search_path",
                                 help="Path where to search for audio and metadata info files to process. "
                                      "Can either be a directory path where all containing audio files will be "
                                      "processed or a single audio file path to process by itself "
                                      "(default: %(default)s).")
        parser_args.add_argument("-i", "--info", dest="info_file",
                                 help="Path to audio metadata information file to be applied to format matched with "
                                      "audio files. (default: looks for text file compatible format named `info`, "
                                      "`config` or `meta` under `path`, uses the first match with ``any`` format).")
        parser_args.add_argument("-a", "--all", dest="all_info_file",
                                 help="Path to audio info file of metadata to apply to every matched audio files. "
                                      "This is mainly to apply shared tags across a list of matched audio files such "
                                      "as the same ARTIST, ALBUM or YEAR values for a set of grouped tracks. "
                                      "(default: looks for text file compatible format named `all`, `any` or "
                                      "`every` under `path`, uses the first match with ``any`` format).")
        parser_args.add_argument("-P", "--parser", dest="parser_mode",
                                 default="any", choices=[p.name for p in PARSER_MODES],
                                 help="Parsing mode to enforce. See also ``--help-format`` for details. "
                                      "(default: %(default)s)")
        parser_args.add_argument("-o", "--output", dest="output_file",
                                 help="Location where to save applied output configurations (file or directory). "
                                      "(default: ``output.cfg`` located under ``--path``"
                                      " or parent directory of ``--file``).")
        parser_args.add_argument("-F", "--format", dest="output_mode",
                                 default=FORMAT_MODE_YAML, choices=[f.name for f in FORMAT_MODES],
                                 help="Output format of applied metadata details. "
                                      "See also ``--help-format`` for details. (default: %(default)s)")
        parser_args.add_argument("-E", "--exceptions", default=DEFAULT_EXCEPTIONS_CONFIG, dest="exceptions_config",
                                 help="Path to custom exceptions configuration file "
                                      "(default: ``config/exceptions.cfg``). "
                                      "During formatting of fields, words matched against keys in the file will be "
                                      "replaced by the specified value instead of default word capitalization.")
        parser_args.add_argument("-S", "--stopwords", default=DEFAULT_STOPWORDS_CONFIG, dest="stopwords_config",
                                 help="Path to custom stopwords configuration file "
                                      "(default: ``config/stopwords.cfg``). "
                                      "When formatting fields of ID3 tags and file names, the resulting words "
                                      "matched against listed words from that file will be converted to lowercase "
                                      "instead of the default word capitalization.")
        op_args = ap.add_argument_group(title="Operation Arguments",
                                        description="Arguments to control which subset of operations to apply on "
                                                    "matched audio files and parsed metadata.")
        op_args.add_argument("--dry", action="store_true",
                             help="Do not execute any modification, just pretend. "
                                  "(note: works best when combined with outputs of ``--verbose`` or ``--debug``)")
        op_args.add_argument("-b", "--backup", action="store_true",
                             help="Create a backup of files to be modified. Files are saved in directory named "
                                  "``backup`` under the ``--path`` or parent directory of ``--file``. " 
                                  "No backup is accomplished otherwise.")
        op_args.add_argument("--rename-title", "--RT", action="store_true",
                             help="Specifies whether to rename matched audio files with their corresponding ``TITLE``. "
                                  "This is equivalent to ``--rename-format '%%(TITLE)s'``.")
        op_args.add_argument("--prefix-track", "--PT", action="store_true",
                             help="Specifies whether to prefix the file name with ``TRACK`` when combined with "
                                  "``--rename-title`` option. "
                                  "This is equivalent to ``--rename-format '%%(TRACK)s %%(TITLE)s'``.")
        op_args.add_argument("--rename-format", "--RF",
                             help="Specify the specific ``FORMAT`` to employ for renaming files. "
                                  "Formatting template follows the ``%%(<TAG>)`` syntax. "
                                  "Supported ``<TAG>`` fields are listed in ID3 TAG names except image-related items.")
        op_args.add_argument("--no-fetch", "--nF", action="store_true",
                             help="Must be combined with ``--link`` option. Enforces parser mode ``youtube``. "
                                  "When provided, instead of downloading music files, only metadata information will "
                                  "be retrieved from the link in order to obtain ID3 audio tag metadata and apply them "
                                  "to referenced pre-existing audio files in the search path. The metadata retrieved "
                                  "this way replaces corresponding ID3 tag details otherwise provided by ``--info``.")
        op_args.add_argument("--no-info", "--nI", action="store_true",
                             help="Disable auto-detection of 'info' common audio metadata information file names. "
                                  "Useful when detection of an existing file on search path should be avoided. "
                                  "Ignored if ``--info`` is explicitly specified.")
        op_args.add_argument("--no-all", "--nA", action="store_true",
                             help="Disable auto-detection of 'all' common audio metadata information file names. "
                                  "Useful when detection of an existing file on search path should be avoided. "
                                  "Ignored if ``--all`` is explicitly specified.")
        op_args.add_argument("--no-cover", "--nC", action="store_true",
                             help="Disable auto-detection of common cover image file names. "
                                  "Useful when detection of an existing file on search path should be avoided. "
                                  "Ignored if ``--cover`` is explicitly specified.")
        op_args.add_argument("--no-rename", "--nR", action="store_true",
                             help="Do not apply any file rename operation. (note: implied when ``--dry`` is provided)")
        op_args.add_argument("--no-update", "--nU", action="store_true",
                             help="Do not apply any ID3-Tags updates. (note: implied when ``--dry`` is provided)")
        op_args.add_argument("--no-output", "--nO", action="store_true",
                             help="Do not save results to output configurations file. (see: ``--output``)")
        op_args.add_argument("--no-result", "--nP", action="store_true",
                             help="Do not print results to console output. "
                                  "Be aware that result will be reported only if logging level is ``--verbose`` "
                                  "or ``--debug``. This flag is redundant for more restrictive logging levels.")
        id3_args = ap.add_argument_group(title="ID3 Tags Arguments",
                                         description="Options to directly provide specific ID3 tag values to one or "
                                                     "many audio files matched instead of through ``--info`` "
                                                     "and ``--all`` configuration files.")
        id3_args.add_argument("-c", "--cover", "-I", "--image", dest="cover_file",
                              help="Path where to find image file to use as audio file album cover. "
                                   "(default: looks for image of compatible format named "
                                   "`cover`, `artwork`, `art` or `image` under ``--path`` or parent directory "
                                   "of ``--file``, using the first match).")
        id3_args.add_argument("-T", "--title", dest=t.TAG_TITLE,
                              help="Name to apply as ``TAG_TITLE`` metadata attribute to file(s).")
        id3_args.add_argument("-N", "--track", "--track-number", dest=t.TAG_TRACK,
                              help="Name to apply as ``TAG_TRACK`` metadata attribute to file(s).")
        id3_args.add_argument("-Y", "--year", dest=t.TAG_YEAR,
                              help="Name to apply as ``TAG_YEAR`` metadata attribute to file(s).")
        id3_args.add_argument("-D", "--duration", dest=t.TAG_DURATION,
                              help="Name to apply as ``TAG_DURATION`` metadata attribute to file(s).")
        id3_args.add_argument("-G", "--genre", dest=t.TAG_GENRE,
                              help="Name to apply as ``TAG_GENRE`` metadata attribute to file(s).")
        id3_args.add_argument("--CA", "--contrib-artist", "--artist", dest=t.TAG_ARTIST,
                              help="Name to apply as ``TAG_ARTIST`` metadata attribute to file(s).")
        id3_args.add_argument("-A", "--album", dest=t.TAG_ALBUM,
                              help="Name to apply as ``TAG_ALBUM`` metadata attribute to file(s).")
        id3_args.add_argument("--AA", "--album-artist", dest=t.TAG_ALBUM_ARTIST,
                              help="Name to apply as ``TAG_ALBUM_ARTIST`` metadata attribute to audio file(s). "
                                   "If not provided, but ``TAG_ARTIST`` can be found via option ``--artist`` or some "
                                   "other configuration file (``--info`` or ``--all``), the same value is employed "
                                   "unless requested not to do so using option ``--no-match-artist``.")
        id3_args.add_argument("--no-match-artist", "--nMA", action="store_false", dest="match_artist")
        log_args = ap.add_argument_group(title="Logging Arguments",
                                         description="Arguments that control logging and reporting verbosity.")
        lvl_args = log_args.add_mutually_exclusive_group(required=False)
        lvl_args.add_argument("-q", "--quiet", action="store_true",
                              help="Do not provide any logging details except error.")
        lvl_args.add_argument("-w", "--warn", action="store_true",
                              help="Provide minimal logging details (warnings and errors only). "
                                   "Warnings can include important notices about taken decisions or "
                                   "unexpected yet handled parsing of values.")
        lvl_args.add_argument("-v", "--verbose", action="store_true",
                              help="Provide additional information logging.")
        lvl_args.add_argument("-d", "--debug", action="store_true",
                              help="Provide step by step logging details during operations.")
        lvl_args.add_argument("-t", "--trace", action="store_true",
                              help="Provide caught error detailed reporting and traceback.")

        argv = None if sys.argv[1:] else ["--help"]  # auto-help message if no args
        ns = ap.parse_args(args=argv)
        if ns.help_format:
            print(_HELP_FORMAT)
            return 0
        args = vars(ns)
        args.pop("help_format")
        logger_level = NOTSET
        for arg, lvl in [("trace", TRACE), ("debug", DEBUG), ("verbose", INFO), ("warn", WARNING), ("quiet", CRITICAL)]:
            if args.pop(arg, False) and logger_level == NOTSET:
                logger_level = lvl
        if logger_level == NOTSET:
            logger_level = ERROR
        LOGGER.setLevel(logger_level)
    except Exception as exc:
        exc = exc if LOGGER.isEnabledFor(DEBUG) else False
        LOGGER.error("Internal error during parsing.", exc_info=exc)
        return 3
    try:
        result = main(**args)
        if result:
            return 0
    except Exception as exc:
        exc = exc if LOGGER.isEnabledFor(DEBUG) else False
        LOGGER.error("Internal error during operation.", exc_info=exc)
        return 2
    return 1


@log_exception(LOGGER)
def main(
         # --- file/parsing options ---
         link=None,                     # type: Optional[str]
         search_path=None,              # type: Optional[str]
         info_file=None,                # type: Optional[str]
         all_info_file=None,            # type: Optional[str]
         cover_file=None,               # type: Optional[str]
         output_file=None,              # type: Optional[str]
         output_mode=FORMAT_MODE_YAML,  # type: Union[FORMAT_MODES]
         parser_mode=FORMAT_MODE_ANY,   # type: Union[PARSER_MODES]
         exceptions_config=None,        # type: Optional[str]
         stopwords_config=None,         # type: Optional[str]
         # --- specific meta fields ---
         artist=None,                   # type: Optional[str]
         album=None,                    # type: Optional[str]
         album_artist=None,             # type: Optional[str]
         title=None,                    # type: Optional[str]
         track=None,                    # type: Optional[int]
         genre=None,                    # type: Optional[str]
         duration=None,                 # type: Optional[Union[Duration, str]]
         year=None,                     # type: Optional[int]
         match_artist=True,             # type: bool
         # --- other operation flags ---
         rename_format=None,            # type: Optional[str]
         rename_title=False,            # type: bool
         prefix_track=False,            # type: bool
         dry=False,                     # type: bool
         backup=False,                  # type: bool
         no_fetch=False,                # type: bool
         no_cover=False,                # type: bool
         no_info=False,                 # type: bool
         no_all=False,                  # type: bool
         no_rename=False,               # type: bool
         no_update=False,               # type: bool
         no_output=False,               # type: bool
         no_result=False,               # type: bool
         ):                             # type: (...) -> AudioConfig
    """
    Main process of AIU CLI.
    """
    search_path = "." if search_path == "'.'" else search_path  # default provided as literal string with quotes
    search_path = os.path.abspath(search_path or os.path.curdir)
    search_dir = search_path if os.path.isdir(search_path) else os.path.split(search_path)[0]
    LOGGER.info("Search path is: [%s]", search_path)

    output_file = validate_output_file(output_file, search_dir, default_name="output.cfg")
    LOGGER.info("Output config file %s be: [%s]", "would" if dry else "will", output_file)
    output_dir = os.path.dirname(output_file)

    # process link to pre-generate configuration files
    youtube_config = None
    if link:
        if dry and not no_fetch:
            LOGGER.warning("Will not fetch files from URL in 'dry' mode. Enforcing '--no-fetch'.")
            no_fetch = True
        LOGGER.info("Retrieving config 'youtube'%s from link: [%s]", "" if no_fetch else " and album files", link)
        meta_file, meta_json = get_metadata(link) if no_fetch else fetch_files(link, output_dir)
        youtube_config = AudioConfig(meta_json)

    # find configurations files
    cfg_info_file = info_file
    if not cfg_info_file and not no_info:
        cfg_info_file = look_for_default_file(search_dir, ["info", "config", "meta"], ALL_PARSER_EXTENSIONS)
    if cfg_info_file and os.path.isfile(cfg_info_file):
        LOGGER.info("Matched config 'info' file: [%s]", cfg_info_file)
    else:
        if cfg_info_file is not None:
            LOGGER.warning("Could not resolve specified config 'info' file: [%s]", cfg_info_file)
        cfg_info_file = None
        LOGGER.debug("No config 'info' file found.")

    if not all_info_file and not no_all:
        all_info_file = look_for_default_file(search_dir, ["all", "any", "every"], ALL_PARSER_EXTENSIONS)
    if all_info_file and os.path.isfile(all_info_file):
        LOGGER.info("Matched config 'all' file: [%s]", all_info_file)
    else:
        if all_info_file is not None:
            LOGGER.warning("Could not resolve specified config 'all' file: [%s]", all_info_file)
        all_info_file = None
        LOGGER.debug("No config 'all' file found.")

    if not cover_file and not no_cover:
        cover_file = look_for_default_file(search_dir, ["cover", "artwork", "art", "image"], ALL_IMAGE_EXTENSIONS)
    if cover_file and os.path.isfile(cover_file):
        LOGGER.info("Matched cover image file: [%s]", cover_file)
    else:
        if cover_file is not None:
            LOGGER.warning("Could not resolve specified cover image file: [%s]", cover_file)
        cover_file = None
        LOGGER.debug("No cover image file found.")

    LOGGER.debug("Using %s exceptions configuration: [%s]",
                 "custom" if exceptions_config else "default",
                 exceptions_config if exceptions_config else DEFAULT_EXCEPTIONS_CONFIG)
    except_file = exceptions_config or DEFAULT_EXCEPTIONS_CONFIG
    aiu.Config.EXCEPTIONS = load_config(aiu.Config.EXCEPTIONS, except_file, is_map=True)
    LOGGER.debug("Using %s stopwords configuration: [%s]",
                 "custom" if stopwords_config else "default",
                 stopwords_config if stopwords_config else DEFAULT_STOPWORDS_CONFIG)
    stopword_file = stopwords_config or DEFAULT_STOPWORDS_CONFIG
    aiu.Config.STOPWORDS = load_config(aiu.Config.STOPWORDS, stopword_file, is_map=False)

    # obtain target audio files to process
    audio_files = get_audio_files(search_path)
    LOGGER.info("Found audio files to process:\n  %s", "\n  ".join(audio_files))

    # parse configurations
    config_combo = []  # type: List[Tuple[bool, AudioConfig]]
    config_shared = True
    if youtube_config:
        config_combo.append((False, youtube_config))
        config_shared = False
    if cfg_info_file:
        LOGGER.info("Running audio config parsing...")
        cfg_audio_config = parse_audio_config(cfg_info_file, mode=parser_mode)
        config_combo.append((False, cfg_audio_config))
        config_shared = False
    if all_info_file:
        LOGGER.info("Running audio 'all' config parsing...")
        all_audio_config = parse_audio_config(all_info_file, mode=parser_mode)
        config_combo.append((True, all_audio_config))
    literal_fields = {
        t.TAG_ALBUM: album, t.TAG_ALBUM_ARTIST: album_artist, t.TAG_ARTIST: artist, t.TAG_TITLE: title,
        t.TAG_TRACK: track, t.TAG_DURATION: duration, t.TAG_GENRE: genre, t.TAG_YEAR: year,
    }
    literal_fields = AudioConfig([dict((k, v) for k, v in literal_fields.items() if v is not None)])
    if cover_file:
        config_combo.append((True, AudioConfig([{"cover": cover_file}])))
    if literal_fields:
        LOGGER.info("Literal fields %s: [%s]", "that would be applied" if dry else "to apply", literal_fields)
        config_combo.append((True, literal_fields))
    if not config_combo:
        LOGGER.error("Couldn't find any config to process.")
        sys.exit(-1)

    # apply parsed configurations against target audio files
    LOGGER.info("Resolving metadata config fields...")
    LOGGER.debug("Match artist parameter: %s", match_artist)
    try:
        audio_config = merge_audio_configs(config_combo, match_artist, len(audio_files), config_shared)
    except ValueError as exc:
        LOGGER.error("Failed merge attempt of multiple configuration sources:\n%s\n"
                     "Maybe retry with explicit '--format' and/or '--parser' parameters?", exc)
        sys.exit(-1)
    if not all(info for info in audio_config):
        LOGGER.error("Cannot process combined configuration with missing details for some tracks: [%s]", audio_config)
        sys.exit(-1)
    if not dry:
        LOGGER.info("Applying config...")
        if backup:
            backup_dir = os.path.join(search_dir, "backup")
            LOGGER.info("Backup of files in: [%s]", backup_dir)
            backup_files(audio_files, backup_dir)
    output_config = apply_audio_config(audio_files, audio_config, dry=dry or no_update)
    output_config = update_file_names(output_config, rename_format, rename_title, prefix_track, dry=dry or no_rename)

    # report results
    if not no_output and not save_audio_config(output_config, output_file, mode=output_mode, dry=dry):
        if not dry:  # when dry mode, it is normal that the file was not written
            LOGGER.error("Failed saving file, but no unhandled exception occurred.")
    elif no_output:
        LOGGER.debug("Saving output configuration was disabled.")
    if not no_result and output_config and LOGGER.isEnabledFor(INFO):
        LOGGER.to_yaml(output_config .value)
    elif no_result:
        LOGGER.debug("Logging result configuration was disabled.")
    LOGGER.info("Operation complete.")
    return output_config


if __name__ == "__main__":
    sys.exit(cli())
