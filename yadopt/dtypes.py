"""
yadopt.dtypes - collections of data types and classes
"""
from __future__ import annotations

# Import standard libraries.
import collections
import pathlib

# For type hinting.
from typing import TypeAlias

# Declare published functions and variables.
__all__ = ["Deque", "Path", "Span"]


# Double-ended queue.
Deque: TypeAlias = collections.deque

# File path class for YadOpt.
Path: TypeAlias = pathlib.Path

# Span of a string, a pair of start index and end index.
Span: TypeAlias = tuple[int, int]

# Allowable type names for YadOpt.
DTYPE_NAMES: set[str] = {
    # Booleans.
    "bool", "boolean",
    # Integers.
    "int", "integer",
    # Floating numbers.
    "flt", "float",
    # Strings.
    "str", "string",
    # Path.
    "path",
    # Auto type.
    "auto",
    # None.
    "nonetype",
}


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
