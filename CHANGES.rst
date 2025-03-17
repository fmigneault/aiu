CHANGES
=======

`Unreleased <https://github.com/fmigneault/aiu/tree/master>`_ (latest)
------------------------------------------------------------------------------------

* Nothing yet.

`2.0.2 <https://github.com/fmigneault/aiu/tree/2.0.2>`_ (2025-03-17)
------------------------------------------------------------------------------------

* Fix ``Duration`` class positional arguments failing when generated from ``deepcopy`` calling ``__new__``.

`2.0.1 <https://github.com/fmigneault/aiu/tree/2.0.1>`_ (2025-03-17)
------------------------------------------------------------------------------------

* Fix ``aiu.clean.beautify_string`` lookup of first word separated by sentence punctuations.
* Fix ``aiu.clean.beautify_string`` potentially applying beautification an entire sentence as if it was a single word,
  leanding to lowercase characters for following words of the sentence not properly capitalized by the string formatter.

`2.0.0 <https://github.com/fmigneault/aiu/tree/2.0.0>`_ (2025-03-16)
------------------------------------------------------------------------------------

* Refactor definitions originally within ``aiu.__init__.py`` to ``aiu.config.py`` to avoid install import error.
* Add ``--no-beautify`` option (beautification enabled by default) to control ID3 tag renaming and word/stopword
  operations employed to adjust the audio fields based on resolved configuration files. When disabled, the field
  values will be employed directly as provided or resolved by ``--info``, ``--all`` and ``--link`` references.
* Modify the string beautification process to occur at a centralized step to more easily inspect its results,
  rather than spread across local configuration parsing and YouTube resolution steps.
* Update ``aiu.clean.beautify_string`` to employ string-formatter operators rather than hardcoded
  string ``capitalize``/``lower`` methods.
* Fix loading of ``stopwords`` and ``exceptions`` configuration files to discard empty definitions or lines.
* Fix loading of ``stopwords`` to enforce lowercase for lookup.
* Fix ``StrField`` not using the raw ``str`` representation (e.g.: merging configuration resulted in forwarding
  of the ``StrField`` object between instances), causing invalid output and logs parsing from unknown object types.
* Allow ``--parser`` names to be specified in a case-insensitive manner.
* Adjust ``--prefix-track`` to imply ``--rename-title`` even when omitted to make the operation effective.
* Fix parameter reference in ``--rename-format`` (from ``FORMAT`` to ``RENAME_FORMAT``) to match the displayed metavar.

`1.11.1 <https://github.com/fmigneault/aiu/tree/1.11.1>`_ (2024-07-27)
------------------------------------------------------------------------------------

* Fix YouTube Music album scraping with adjustments for latest API responses
  (relates to `tombulled/python-youtube-music#26 <https://github.com/tombulled/python-youtube-music/pull/26>`_
  and `fmigneault/python-youtube-music#2 <https://github.com/fmigneault/python-youtube-music/pull/2>`_).

`1.11.0 <https://github.com/fmigneault/aiu/tree/1.11.0>`_ (2023-11-05)
------------------------------------------------------------------------------------

* Add search path override to output directory location when the current directory path is detected as the script path.
* Add ``--no-heuristic-tag-match`` and corresponding ``heuristic_tag_match`` flag applied by default that will attempt
  matching existing ID3 tags from the source audio files against target configuration ID3 tags when file names were not
  sufficient to find a match.
* Add more file name matching heuristics to consider duplicated descriptors across multiple file names, in order to
  reduce the set of false-positive candidates using only word portions of the title that are distinct and descriptive.
* Add options ``--heuristic-stopword`` and ``--heuristic-config`` that allows providing a set of stopwords to be ignored
  only during the heuristic file name matching strategy. These allow removing words often found in file names that cause
  noise for the purpose of matching the audio file title. The default file employed if no parameters for these options
  are unspecified is ``aiu/config/ignore.cfg``.
* Rename ``aiu.Config.EXCEPTIONS`` and ``aiu.Config.STOPWORDS`` to ``aiu.Config.EXCEPTIONS_RENAME`` and
  ``aiu.Config.STOPWORDS_RENAME`` respectively to distinguish them from new ``aiu.Config.STOPWORDS_MATCH``
  employed by ``--heuristic-stopword`` and ``--heuristic-config``.
* Add alternative option names ``--rename-exceptions-config`` and ``--rename-stopwords-config`` to corresponding
  ``--exceptions`` and ``--stopwords`` options to provide more explicit representation of their purpose.
* Fix ``heuristic_word_match`` and ``heuristic_delete_duplicates`` flags not passed down for iterative per-album call.
* Apply the resolved ``album_artist`` ID3 tag or its default value set by ``artist`` ID3 tag according to options
  ``--no-match-artist`` and ``--album-artist`` as detailed in their description.
* Fix default value of ``match_artist``, set when omitting ``-no-match-artist`` that caused ``--album-artist`` value
  provided explicitly to be ignored.
* Remove duplicate and unimplemented function for applying ID3 tags.
* Move ID3 tag and cover file utilities from ``aiu.utils`` to ``aiu.updater`` module.
* Fix ID3 tags properties passed by individual options (``-A``, ``-T``, etc.) to be incorrectly reported in the logging
  definition, as well as passing them as individual ``AudioInfo`` objects instead of a single combined one under the
  generated ``AudioConfig`` for these tags. If more than one literal ID3 tag field was provided simultaneously, this
  would cause erroneous mismatches in length comparison between multiple ``AudioConfig`` from the various sources.
* Fix logging calls not using the lazy string evaluation format in some cases.

`1.10.1 <https://github.com/fmigneault/aiu/tree/1.10.1>`_ (2023-07-04)
------------------------------------------------------------------------------------

* Add ``Makefile`` target ``version`` to quickly retrieve the information to facilitate use with ``bump`` targets.
* Fixes to ``Makefile`` and ``setup.py`` encountering issues on reinstall.

`1.10.0 <https://github.com/fmigneault/aiu/tree/1.10.0>`_ (2023-06-28)
------------------------------------------------------------------------------------

* Add ``--force-fetch`` option complementary to ``--no-fetch`` to enforce re-download of files if matches are found in
  the output directory, instead of reusing previously cached results.
* Add more result file matching combinations to attempt better detection of cached pre-downloaded audio files. Notably,
  when the ``--prefix-track`` and/or ``--rename-title`` options are omitted, most predefined match patterns where never
  able to work due to assumed track indices. A combination of ``{artist} - {song}`` patterns allow to match commonly
  employed file name conventions for song track naming.
* Fix and improve common mismatches between desired file name patterns and downloaded ones caused by ``youtube_dl``
  over-sanitizing valid file-system characters that contained unicode or accents. These characters will now be preserved
  to better retain the original song title, album and artist names using those characters, and as a side effect, more
  efficiently match the expected download file name against target ID3 metadata.
* Add DevOps ``Makefile`` along with multiple inspection, linting and validation utilities.

`1.9.1 <https://github.com/fmigneault/aiu/tree/1.9.1>`_ (2022-10-30)
------------------------------------------------------------------------------------

* Fix the generated output audio file name that could sometime contain illegal characters after substitution of the
  requested metadata according to the rename format. Illegal characters will be replaced by ``_`` prior to rename.

`1.9.0 <https://github.com/fmigneault/aiu/tree/1.9.0>`_ (2022-09-05)
------------------------------------------------------------------------------------

* Add multiple heuristic rules to attempt matching ambiguous file names against provided audio information.
* Add heuristics and patched characters conditions to better detect ambiguous file names renamed following download
  to better detect them once again on subsequent download operation, taking advantage of cached file contents.
* Add CLI options to allow toggling of experimental heuristics that are more prone to errors than typical "hard"
  matching conditions, at the expense of potential failure to resolve more complicated matching cases.

`1.8.0 <https://github.com/fmigneault/aiu/tree/1.8.0>`_ (2022-09-03)
------------------------------------------------------------------------------------

* Update `TODO <TODO.md>`_ items that have been implemented in previous versions.
* Set default logging level to ``INFO`` (i.e.: ``-v`` option) to provide basic steps and progress bar details.
* Fix reported ``cover`` field in generated output configuration to use the saved image within the output
  location instead of the temporary location employed for downloading the YouTube album/song cover.
* Fix missing properties to better handle ``CoverFile`` class attributes.

`1.7.2 <https://github.com/fmigneault/aiu/tree/1.7.2>`_ (2022-08-16)
------------------------------------------------------------------------------------

* Fix invalid double quote character (``"``) incorrectly escaped into single quote character (``'``) instead of
  expected underscore character (``_``) by internal ``python-youtube-music`` (``ytm``) code under Windows, causing
  invalid path resolution of the downloaded file in combination with dispatched call to ``youtube_dl``.

`1.7.1 <https://github.com/fmigneault/aiu/tree/1.7.1>`_ (2022-04-14)
------------------------------------------------------------------------------------

* Fix missing encoding when writing JSON temp file metadata that contains characters needing UTF-8.
* Fix ``LP_OVERLAPPED`` error by upgrading requirement of ``yt-dlp`` with more recent version.

`1.7.0 <https://github.com/fmigneault/aiu/tree/1.7.0>`_ (2022-01-08)
------------------------------------------------------------------------------------

* Add support of input YouTube Music channel link to automatically download and process all available artist albums.
  Individual albums are iteratively processed as separate ``aiu`` operations and downloaded songs are stored into
  corresponding album sub-directories.
* Fix incorrect direct reference to ``YoutubeMusicDL`` instead of ``CachedYoutubeMusicDL`` implementation when
  no ``tqdm`` progression is requested.
* Fix base YouTube downloader to employ ``yt_dlp`` instead of ``youtube_dl``, providing download speed
  improvements and other YouTube related issue handling.
* Fix displayed SSL warnings caused by underlying YouTube downloader requests that cannot be addressed
  directly by this tool.
* Add ``--nP`` and ``--no-progress`` argument to allow disabling only progress bars while keeping more verbose logging.
* Add ``--no-summary`` to better represent ``--no-result`` argument behaviour.
* Replace ``--nP`` by ``--nS`` for argument ``--no-result``.
* Fix failing resolution of single ``AudioInfo`` element (single audio file) due to ``Duration`` field not allowing
  additional positional arguments during deepcopy.

`1.6.0 <https://github.com/fmigneault/aiu/tree/1.6.0>`_ (2021-09-22)
------------------------------------------------------------------------------------

* Fix invalid attempts to retrieve ``album`` and ``artist`` name from metadata with possibly unavailable field
  (use patch: `fmigneault/python-youtube-music@patch-new-youtube-music-version <
   https://github.com/fmigneault/python-youtube-music/tree/patch-new-youtube-music-version>`_,
   relates to: `tombulled/python-youtube-music#13 <https://github.com/tombulled/python-youtube-music/issues/13>`_).

`1.5.0 <https://github.com/fmigneault/aiu/tree/1.5.0>`_ (2021-08-27)
------------------------------------------------------------------------------------

* Add option ``--remove-track`` to allow explicit removal of ID3 Tag track number and also support *invalid* values
  provided to ``--track`` option (integer < 1, empty string ``""``) as equivalent to the new one.

`1.4.0 <https://github.com/fmigneault/aiu/tree/1.4.0>`_ (2021-08-26)
------------------------------------------------------------------------------------

* Improve YouTube Music Download operation with check of already available song file to bypass unnecessary
  re-download from `python-youtube-music (ytm) <https://github.com/tombulled/python-youtube-music>`_ package.
  Cached file references that skip download are reported in logs (debug level) after progress bar processing completes.
* Validate that all required ID3 tags information are available for track renaming operation against the different
  CLI flag against predefined and custom format names. Missing explicit ID3 tags within the template name format will
  be raised and identified in logs to help resolution from the user by providing missing fields.
* Fix incorrect parsing of file paths with some UTF-8 encoded characters during evaluation of MP3-like files by
  bumping requirement of `eyeD3 <https://github.com/nicfit/eyeD3>`_ to more recent ``0.9.6`` version.

`1.3.0 <https://github.com/fmigneault/aiu/tree/1.3.0>`_ (2021-07-08)
------------------------------------------------------------------------------------

* Add support to ``--link`` referring to a single YouTube Video or Music URL instead of a full album.
* Reapply master of original YouTube Music repository (instead of fork) with integrated fix of missing track
  (see PR `tombulled/python-youtube-music#11 <https://github.com/tombulled/python-youtube-music/pull/11>`_).

`1.2.0 <https://github.com/fmigneault/aiu/tree/1.2.0>`_ (2021-05-24)
------------------------------------------------------------------------------------

* Add download progression display in the outputs when ``--link`` and ``--debug``/``--verbose`` are requested.
* Add option ``--output-dir`` (``-O``, ``--outdir``) to define an alternate output directory location when fetching
  files in combination with ``--link``.
* Add alias ``--output-format`` to ``--format`` option.
* Change default value of ``--output`` to ``output.yml`` to align it with the default value of ``--format``.
* Save the album cover image file that is retrieved from the remote Youtube Music link when fetching tracks.
* Fix some literal fields provided by input options (``--album``, ``album-artist``, ``--year``) that were
  incorrectly dropped.
* Fix an issue where resolution between cover file sources already resolved would not be recognized and raise an error.

`1.1.0 <https://github.com/fmigneault/aiu/tree/1.1.0>`_ (2021-04-04)
------------------------------------------------------------------------------------

* Fix handling of *shared* ID3 metadata across audio files when *only* global options are provided.
  For example, only giving ``--artist <ARTIST>`` without any other audio configuration file to match audio files
  against caused many ``AttributeError`` and incorrect application of specified tags to *all* files
  (fixes `#1 <https://github.com/fmigneault/aiu/issues/1>`_).
* Fix YouTube Music attempting to set ID3 metadata tags unsupported by ``AudioConfig`` and ``AudioInfo`` objects.
* Fix failing YouTube Music album download operation due to missing ``track`` field in some rare cases
  (relates to `PR python-youtube-music#11 <https://github.com/tombulled/python-youtube-music/pull/11>`_).
* Fix and improve fetching with caching of cover art from Youtube Music album metadata.
* Fix false positive of ``csv`` parser with all empty values against a ``list`` formatted configuration file.
* Improve reporting of the cause of failure when parsing or merging multiple configuration files.
* Remove multiple unnecessary package dependencies.

`1.0.0 <https://github.com/fmigneault/aiu/tree/1.0.0>`_ (2021-03-02)
------------------------------------------------------------------------------------

* Add basic implementation allowing fetch of metadata and downloading of YouTube Music album files.
* Add options ``--no-cover``, ``--no-info``, and ``--no-all`` to disable default auto-detection of configuration files.
* Add *featuring* abbreviations handling in ``exceptions.cfg`` file.
* Drop support of Python 2.7 and 3.5

`0.5.1 <https://github.com/fmigneault/aiu/tree/0.5.1>`_ (2020-12-05)
------------------------------------------------------------------------------------

* Fix parsing ``list`` format when number of lines can both result into 3-fields and 2-fields variant.
* Fix handling unspecified ``--rename-format``, ``--rename-title`` and ``--prefix-track``.

`0.5.0 <https://github.com/fmigneault/aiu/tree/0.5.0>`_ (2020-12-05)
------------------------------------------------------------------------------------

* Add argument ``--backup`` that will enforce saving a copy of audio files to be edited beforehand.
* Add argument ``--exceptions`` to override default file ``config/exceptions.cfg``.
* Add argument ``--stopwords`` to override default file ``config/stopwords.cfg``.
* Add ``list`` parser that takes track numbers, song titles and duration on separate lines as often retrieved from raw
  copy-paste conversion in text file from web-pages that display the information with HTML table/divs.
* Drop ``docopt`` in favor of ``argparse`` which offer more explicit and versatile configuration of options.
* Fix parsing of single ``--file`` path to search default directory locations of other arguments (e.g.: ``--info``).
* Fix processing and writing of tag fields that employ different internal names (``eye3D.id3.Tags``) against generic
  names employed by the parser (e.g.: ``track -> track_num``).

0.4.0 (2020-05-03)
------------------------------------------------------------------------------------

* Add file renaming operations using flags ``--rename-title``, ``--rename-format`` and ``--prefix-track``.
* Add ``config/exceptions.cfg`` file that provides a map of exceptions to ignore for rename/beautify operations.
* Add more reporting and processing control with flags ``--no-rename``,  ``--no-update``,  ``--no-output``
  and ``--no-result``.
* Improve error code reporting with corresponding sections.
* Avoid full traceback dump of error unless ``--debug`` was requested. Only display where error happened.

0.3.0 (2020-04-30)
------------------------------------------------------------------------------------

* Add ``--dry`` option to run process without applying modifications/actions.
* Fix handling the default value for ``--path``.
* Fixes to logging formats.

0.2.0 (2020-04-29)
------------------------------------------------------------------------------------

* Add audio file rename options.
* Fix no arguments raising parsing error. Know does default ``--help``.
* Fix runtime execution path not found to metadata.

0.1.0 (2019-10-26)
------------------------------------------------------------------------------------

* First structured release.
