CHANGES
=======

0.4.0
---------------------

* Add file renaming operations using flags ``--rename-title``, ``--rename-format`` and ``--prefix-track``.
* Add ``config/exceptions.cfg`` file that provides a map of exceptions to ignore for rename/beautify operations.
* Add more reporting and processing control with flags ``--no-rename``,  ``--no-update``,  ``--no-output``
  and ``--no-result``.
* Improve error code reporting with corresponding sections.
* Avoid full traceback dump of error unless ``--debug`` was requested. Only display where error happened.

0.3.0
---------------------

* Add ``--dry`` option to run process without applying modifications/actions.
* Fix handling the default value for ``--path``.
* Fixes to logging formats.

0.2.0
---------------------

* Add audio file rename options.
* Fix no arguments raising parsing error. Know does default ``--help``.
* Fix runtime execution path not found to metadata.

0.1.0
---------------------

* First structured release.
