======================================
aiu: Audio Info Updater
======================================

Tool for updating ID3 tags of audio files using info configuration files.

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

