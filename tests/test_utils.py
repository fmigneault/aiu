import os
import platform

import mock

from aiu.utils import make_dirs_cleaned


def test_make_dirs_cleaned():
    default_args = {"mode": 0o755, "exist_ok": True}
    cur_dir = os.path.realpath(".")
    path_prefix = os.path.splitdrive(cur_dir)[0] if platform.system() == "Windows" else ""

    def _fix_path(_path):
        _prefix = path_prefix if not _path.startswith(path_prefix) else ""
        return os.path.normpath(_prefix + _path)

    valid_tests = [
        "/tmp/random/valid",
        "/tmp/random/also valid",
        "/tmp/random/is allowed!",
        "/tmp/random/~~all-good~~",
        "/tmp/random/[also] good",
        "/tmp/random/(also) good",
    ]
    invalid_tests = [
        ("/tmp/random/not\"valid", _fix_path("/tmp/random/not-valid")),
        # ("/tmp/random/not\\valid", _fix_path("/tmp/random/not-valid")),  # cannot test on Windows since it gets split
        ("/tmp/random/not:valid", _fix_path("/tmp/random/not-valid")),
        ("/tmp/random/not?valid", _fix_path("/tmp/random/not-valid")),
        ("/tmp/random/not*valid", _fix_path("/tmp/random/not-valid")),
        ("/tmp/random/not<valid", _fix_path("/tmp/random/not-valid")),
        ("/tmp/random/not>valid", _fix_path("/tmp/random/not-valid")),
        ("/tmp/random/not|valid", _fix_path("/tmp/random/not-valid")),
        ("/tmp/random/not ok?", _fix_path("/tmp/random/not ok-")),
        ("./ok/yes|no/good/not:good", _fix_path(cur_dir + "/ok/yes-no/good/not-good")),
    ]

    with mock.patch("os.makedirs") as mkdir_mock:
        for test_dir in valid_tests:
            result_dir = _fix_path(test_dir)
            make_dirs_cleaned(test_dir)
            called_args, called_kwargs = mkdir_mock.call_args
            assert called_args[0].lower() == result_dir.lower()  # ignore case for varying drive letters on Windows
            assert called_kwargs == default_args
        for test_dir, result_dir in invalid_tests:
            make_dirs_cleaned(test_dir)
            called_args, called_kwargs = mkdir_mock.call_args
            assert called_args[0].lower() == result_dir.lower()  # ignore case for varying drive letters on Windows
            assert called_kwargs == default_args
