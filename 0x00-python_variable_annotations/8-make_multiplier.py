#!/usr/bin/env python3
""" Variable Annotations """
from typing import List, Union, Tuple, Callable


def make_multiplier(multiplier: float) -> Callable[[float], float]:
    """takes a float multiplier as argument and
    returns a function that multiplies a float by multiplier"""
    def multipl_func(value: float) -> float:
        return value * multiplier
    return multipl_func
