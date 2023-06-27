from typing import Union

from boltons.iterutils import remap

from app.common.exceptions.exceptions import ValidationError


def remove_none_values(d: Union[dict, list], ignore_keys: set = None) -> dict:
    """
    Return Dict that has the none values removed except ignoring certain keys.
    Recursively descend through any embedded Dicts/Lists doing the same
    Returns new Dict if inplace is false. Otherwise modifies given Dict
    """
    if ignore_keys:
        if not isinstance(ignore_keys, set):
            ignore_keys = set(ignore_keys)
        return remap(d, lambda p, k, v: v is not None or k in ignore_keys)
    return remap(d, lambda p, k, v: v is not None)


def must_be_only_one_of(custom_message=None, could_be_none=False, **kwargs):
    """Raising an exception when more than one of parameters present"""
    present_values = remove_none_values(kwargs)
    if len(present_values) == 1:
        return

    elif len(present_values) == 0 and could_be_none:
        return

    if custom_message is not None:
        raise ValueError(custom_message)

    elif not present_values and not could_be_none:
        raise ValueError(
            f"One of {','.join(kwargs.keys())} should be present."
        )
    else:
        raise ValueError(
            f"Only one of {','.join(kwargs.keys())} should be present"
        )
