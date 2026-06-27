"""
yadopt.dtypes - collections of data types and classes
"""

# Declare published functions and variables.
__all__ = ["Match", "Path", "Span", "PosEntry", "OptEntry", "ArgsInfo"]

# Import standard libraries.
import collections
import dataclasses
import itertools
import pathlib
import pprint
import re
import textwrap
import typing

# For type hinting.
from typing import TypeAlias


#===================================================================================================
# Data type aliases
#===================================================================================================

# Double-ended queue.
Deque: TypeAlias = collections.deque

# Regular expression match object.
Match: TypeAlias = re.Match

# Named tuple object.
NamedTuple: TypeAlias = typing.NamedTuple

# File path class for YadOpt.
Path: TypeAlias = pathlib.Path

# Span of a string, a pair of start index and end index.
Span: TypeAlias = tuple[int, int]


#===================================================================================================
# Commonly used custom data types and classes
#===================================================================================================

@dataclasses.dataclass
class PosEntry:
    """
    Parsed result of positional argument definition in docstring.
    """
    name    : str         # Positional argument name.
    is_mult : bool        # Indicates whether this argument can be multiple.
    type_dsc: str | None  # Data type string written in the head of description.
    desc    : str         # Description of this option.
    default : str | None  # Default value (string).
    group   : str         # Group name of this entry.


@dataclasses.dataclass
class OptEntry:
    """
    Parsed result of optional argument definition in docstring.
    """
    name     : str         # Option name.
    name_alt : str | None  # Alternative option name.
    val_name : str | None  # Name of option value (used for type hinting).
    raw_names: list[str]   # Original option name(s) as written in the declaration.
    type_dsc : str | None  # Data type string written in the head of description.
    desc     : str         # Description of this option.
    default  : str | None  # Default value (string).
    group    : str         # Group name of this entry.


@dataclasses.dataclass
class ArgsInfo:
    """
    Parsed result of docstring.
    """
    posargs: list[PosEntry]   # Argument entries.
    optargs: list[OptEntry]   # Option entries.
    docstr : str              # Original docstring.

    def __str__(self) -> str:
        text = "ArgsInfo:\n"
        for idx, item in enumerate(itertools.chain(self.posargs, self.optargs)):
            text += f" |-({idx:02d}) " + textwrap.indent(pprint.pformat(item), " |      ")[8:] + "\n"
        return text.strip()


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
