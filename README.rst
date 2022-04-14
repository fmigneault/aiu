======================================
aiu: Audio Info Updater
======================================

Tool for updating ID3 tags of audio files using text metadata and configuration files.

This tool helps normalize album metadata that can be easily retrievable from various websites as plain text and applies
it to audio files with partially matchable names. Matching between metadata and actual audio files employs various
lookup and pattern matching methods to be flexible against various naming conventions.

This tool also supports download of album songs from a
`YouTube Music link <https://github.com/fmigneault/aiu/tree/master#using-youtube-music-album-link>`_
before applying the desired ID3 tag metadata updates.

.. start-badges

.. list-table::
    :stub-columns: 1

    * - dependencies
      - | |py_ver| |dependencies|
    * - releases
      - | |version| |commits-since|

.. |py_ver| image:: https://img.shields.io/badge/python-3.6%2B-blue.svg
    :alt: Requires Python 3.6+
    :target: https://www.python.org/getit

.. |commits-since| image:: https://img.shields.io/github/commits-since/fmigneault/aiu/1.7.1.svg
    :alt: Commits since latest release
    :target: https://github.com/fmigneault/aiu/compare/1.7.1...master

.. |version| image:: https://img.shields.io/badge/tag-1.7.1-blue.svg?style=flat
    :alt: Latest Tag
    :target: https://github.com/fmigneault/aiu/tree/1.7.1

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
.. code-block:: text

    track, title, artist, time
    01, The first song!, Cool Guy, 3:10
    02, Second Song Title, Cool Guy, 2:45

Tabular and numbered list
--------------------------------------
.. code-block:: text

    1. The first song!      3:10
    2. Second Song Title    2:45


List of plain text fields
--------------------------------------
.. code-block:: text

    1
    The first song!
    3:10
    2
    Second Song Title
    2:45


.. _ytm_link:

Using YouTube Music album link
======================================

It is possible to provide a YouTube Music URL formatted with the album ID in query parameter.

::

    https://music.youtube.com/playlist?list=<ALBUM_ID>

When providing such a link to `AIU` (with the ``--link`` option), it can simultaneously retrieve the corresponding
album audio files and apply all appropriate audio tag metadata to them. The resulting files can then be further
updated using the other options and parsing formats from metadata configurations.

.. _ytm_multi_link:

Process multiple artist albums from YouTube Music link
======================================================

If the provided ``--link`` corresponds to a YouTube Music channel URL, all albums of this artist will be downloaded.

::

    https://music.youtube.com/channel/<ARTIST_ID>

Album songs will be stored into corresponding sub-directories under the specified output location.

Note that according to the amount of songs per albums and total albums, this operation can take some time, but it
will at least save the user the manual work of running individual ``aiu`` call per album link.

Other ``aiu`` parameters are also still applicable when using this type of link
(e.g.: ``--artist``, ``--prefix-track``, etc.).
Be mindful of provided flags though to make sure they remain relevant, since they will be applied to all albums
to be processed for that artist.
