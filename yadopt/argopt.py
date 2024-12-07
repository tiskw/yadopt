"""
Docstring parser.
"""

# Declare published functions and variables.
__all__ = ["parse_argopt", "ArgEntry", "OptEntry"]

# Import standard libraries.
import dataclasses
import pathlib
import re

# Import custom modules.
from .utils import get_default, match_and_get


@dataclasses.dataclass
class ArgEntry:
    """
    Information of command line argument.
    """
    name       : str   # Option name.
    data_type  : type  # Data type of the option value.
    description: str   # Description of this option.
    default    : str   # Default value (string).

@dataclasses.dataclass
class OptEntry:
    """
    Information of command line option.
    """
    name       : str   # Option name.
    name_alt   : str   # Alternative option name.
    data_type  : type  # Data type of the option value.
    n_args     : int   # Number of arguments.
    description: str   # Description of this option.
    default    : str   # Default value (string).


def parse_argopt(line: str) -> ArgEntry|OptEntry|None:
    """
    Parse a line of argument/option section.

    Args:
        line (str): Input line.

    Returns:
        (ArgEntry|OptEntry): Parsed result.

    Examples:
        >>> parse_argopt(" -o   m")
        OptEntry(name='o', name_alt=None, data_type=None, n_args=0, description='m', default=None)
        >>> parse_argopt(" --opt   m")
        OptEntry(name='opt', name_alt=None, data_type=None, n_args=0, description='m', default=None)
        >>> parse_argopt(" -o, --opt   m")
        OptEntry(name='opt', name_alt='o', data_type=None, n_args=0, description='m', default=None)
    """
    arg_patterns_and_indices = [
        # regular expression, (name, ), None
        # ----------------------------------
        (r"\s+(\w+)", (1, ), None),
    ]
    opt_patterns_and_indices = [
        # regular expression,        (name, alt, value), n_args   # | opt type | opt value | delim |
        # ------------------------------------------------------  # --------------------------------
        (r"\s+-(\w+)=(\w+), --(\w+)=(\w+)", (3, 1,    2   ), 1),  # | both     | double    | equal |
        (r"\s+-(\w+) (\w+), --(\w+) (\w+)", (3, 1,    2   ), 1),  # | both     | double    | space |
        (r"\s+-(\w+), --(\w+)=(\w+)",       (2, 1,    3   ), 1),  # | both     | single    | equal |
        (r"\s+-(\w+), --(\w+) (\w+)",       (2, 1,    3   ), 1),  # | both     | single    | space |
        (r"\s+-(\w+), --(\w+)",             (2, 1,    None), 0),  # | both     | none      | -     |
        (r"\s+--(\w+)=(\w+)",               (1, None, 2   ), 1),  # | long     | single    | equal |
        (r"\s+--(\w+) (\w+)",               (1, None, 2   ), 1),  # | long     | single    | space |
        (r"\s+--(\w+)",                     (1, None, None), 0),  # | long     | none      | -     |
        (r"\s+-(\w+)=(\w+)",                (1, None, 2   ), 1),  # | short    | single    | equal |
        (r"\s+-(\w+) (\w+)",                (1, None, 2   ), 1),  # | short    | single    | space |
        (r"\s+-(\w+)",                      (1, None, None), 0),  # | short    | none      | -     |
    ]

    # Try to parse as argument line.
    name, description, _ = match_and_get(line, arg_patterns_and_indices)
    if name is not None:

        # Get data type.
        data_type, description = get_type(name, description)

        # Get default value.
        description, default = get_default(description)

        return ArgEntry(name, data_type, description, default)

    # Try to parse as option line.
    name, alt, value, description, n_args = match_and_get(line, opt_patterns_and_indices)
    if name is not None:

        # Get data type.
        data_type, description = get_type(value, description)

        # Get default value.
        description, default = get_default(description)

        return OptEntry(name, alt, data_type, n_args, description, default)

    return None


def get_type(var_name: str, description: str) -> tuple[type, str]:
    """
    Returns appropriate data type.

    Args:
        var_name (str): Variable name.

    Returns:
        (type): An appropriate Python data type.

    Examples:
        >>> get_type("x_int", "Integer value.")
        (<class 'int'>, 'Integer value.')
        >>> get_type("x", "(int) Integer value.")
        (<class 'int'>, 'Integer value.')
    """
    name_type_map = {"bool": bool, "boolean": bool,
                     "int": int, "integer": int,
                     "flt": float, "float": float,
                     "str": str, "string": str,
                     "path": pathlib.Path}

    # Try to get type from the description.
    m = re.match(r"\s*\((\w+)\)\s*", description)
    if m is not None:
        data_type = name_type_map.get(m.group(1).strip(), str)
        description = description[len(m.group(0)):]
        return (data_type, description)

    # Conservative error handling.
    if not isinstance(var_name, str):
        return (None, description)

    # Try to get type from the variable name.
    for key, dtype in name_type_map.items():
        if var_name.lower().endswith(key):
            return (dtype, description)

    return (None, description)


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
