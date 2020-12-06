======================================
aiu: Audio Info Updater
======================================

Tool for updating ID3 tags of audio files using text metadata and configuration files.

This tool helps normalize album metadata that can be easily retrievable from various websites as plain text and applies
it to audio files with partially matchable names. Matching between metadata and actual audio files employs various
lookup and pattern matching methods to be flexible against various naming conventions.


.. start-badges

.. list-table::
    :stub-columns: 1

    * - dependencies
      - | |py_ver| |dependencies|
    * - releases
      - | |version| |commits-since|

.. |py_ver| image:: https://img.shields.io/badge/python-2.7%2C%203.5%2B-blue.svg
    :alt: Requires Python 3.5+
    :target: https://www.python.org/getit

.. |commits-since| image:: https://img.shields.io/github/commits-since/fmigneault/aiu/0.5.0.svg
    :alt: Commits since latest release
    :target: https://github.com/fmigneault/aiu/compare/0.5.0...master

.. |version| image:: https://img.shields.io/badge/tag-0.5.0-blue.svg?style=flat
    :alt: Latest Tag
    :target: https://github.com/fmigneault/aiu/tree/0.5.0

.. |dependencies| image:: https://pyup.io/repos/github/fmigneault/aiu/shield.svg
    :alt: Dependencies Status
    :target: https://pyup.io/account/repos/github/fmigneault/aiu/

.. end-badges


Build package and install
======================================

At the command line

.. code-block:: shell

    $ conda create -n aiu
    $ source activate aiu
    $ pip install "<git-root-dir>"

Running
======================================

At the command line

.. code-block:: shell

    aiu "<args>"

See ``aiu --help`` for specific argument details.

Audio Info Specification Formats
======================================

Following are the various formats supported for metadata files.

The CLI can take 2 sets for configuration files, one for "per-song" metadata (e.g.: each song has its own and distinct
title), and another for "shared" metadata (e.g.: all songs of the album have the same artist).

YAML
--------------------------------------
.. code-block:: yaml

    - track: 1
      title: The first song!
      artist: Cool Guy
      time: 3:10
    - track: 2
      title: Second Song Title
      artist: Cool Guy
      time: 2:45

JSON
--------------------------------------
.. code-block:: json

    [
        {
            "track": 1,
            "title": "The first song!",
            "artist": "Cool Guy",
            "time": "3:10",
        },
        {
            "track": 2,
            "title": "Second Song Title",
            "artist": "Cool Guy",
            "time": "2:45",
        }
    ]

CSV
--------------------------------------
::

    track, title, artist, time
    01, The first song!, Cool Guy, 3:10
    02, Second Song Title, Cool Guy, 2:45

Tabular and numbered list
--------------------------------------
::

    1. The first song!      3:10
    2. Second Song Title    2:45


List of plain text fields
--------------------------------------
::

    1
    The first song!
    3:10
    2
    Second Song Title
    2:45

