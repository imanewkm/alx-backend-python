#!/usr/bin/env python3
""" Variable Annotations """
from typing import Sequence, Any, Union, Mapping, Optional, TypeVar


T = TypeVar('T')


def safely_get_value(dct: Mapping, key: Any, default: Union[
                     T, None] = None) -> Union[Any, T]:
    """ More involved
    type annotations """
    if key in dct:
        return dct[key]
    else:
        return default
