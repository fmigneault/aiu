from typing import AnyStr, List, Union
import os


def look_for_default_file(path, names):
    # type: (AnyStr, Union[List[AnyStr], AnyStr]) -> Union[AnyStr, None]
    """
    Looks in `path` for any file matching any of the `names`.
    :returns: first matching occurrence, or `None`.
    """
    names = names if isinstance(names, list) else [names]
    contents = sorted(os.listdir(path))
    for c in contents:
        c_name, c_ext = os.path.splitext(c)
        if c_name in names and c_ext != '':
            return c
    return None
