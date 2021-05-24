CHANGES
=======

`Unreleased <https://github.com/fmigneault/aiu/tree/master>`_ (latest)
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
