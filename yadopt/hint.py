"""
yadopt.hint - assign types based on type hinting string
"""

# Declare published functions and variables.
__all__ = ["type_func", "type_hint"]

# Import standard libraries.
import ast

# For type hinting.
from typing          import Any
from collections.abc import Callable

# Import custom modules.
from .argvec import ArgVector
from .dtypes import Path, PosEntry, OptEntry, ArgsInfo
from .errors import YadOptError


#===================================================================================================
# Public classes and functions
#===================================================================================================

def type_func(name: str, val_name: str | None, type_dsc: str | None) -> Callable:
    """
    Determine data type of arguments/options.

    Args:
        name     (str)       : Argument/option name.
        val_name (str | None): Option value name.
        type_dsc (str | None): Type name written in description head.

    Returns:
        (Callable): Appropriate type function.
    """
    # Case 1: description head.
    if type_dsc is not None:

        # Raise an error if type name is unknown.
        if type_dsc.lower() not in DTYPE_HINTS:
            raise YadOptError.InvalidTypeName(type_name=type_dsc)

        return DTYPE_HINTS[type_dsc.lower()]

    # Case 2: value name suffix.
    if val_name is not None:

        # Get the type name candidate from the value name.
        val_type_name: str = val_name.rsplit("_", maxsplit=1)[-1]

        # Returns the type if the type name is valid.
        if val_type_name.lower() in DTYPE_HINTS:
            return DTYPE_HINTS[val_type_name.lower()]

    # Case 3: argument/option name suffix.
    if name:

        # Returns the type if the name ends with the type name.
        for key, dtype in DTYPE_HINTS.items():
            if name.lower().endswith(key):
                return dtype

    # Otherwise, returns default type.
    return str


def type_hint(argvec: ArgVector, arginf: ArgsInfo, verbose: bool) -> None:
    """
    Apply type hints. This function modifies the given argument vector in-place.

    Args:
        argvec  (ArgVector): [IN] Parsed user input.
        arginf  (ArgsInfo) : [IN] Parsed result of docstring.
        verbose (bool)     : [IN] Displays verbose messages that are useful for debugging.
    """
    def set_typed_value(val_dict: dict, args_or_opts: list[PosEntry] | list[OptEntry], verbose: bool) -> None:
        """
        Get typed value.
        """
        if verbose:
            print("In type_hint.set_typed_value:")

        for entry in args_or_opts:

            if verbose:
                print("  - entry =", entry)

            # Do nothing if the entry is not in the value dictionary.
            if entry.name not in val_dict:
                continue

            # Option without value.
            if isinstance(entry, OptEntry) and (entry.val_name is None):
                if not isinstance(val_dict[entry.name], bool):
                    val_dict[entry.name] = strtobool(val_dict[entry.name])
                continue

            # If the value is still None, not necessary to assign type.
            if val_dict[entry.name] is None:
                continue

            # If the value looks like None, set real None.
            if (val_dict[entry.name] == "None") or (val_dict[entry.name] == "NONE"):
                val_dict[entry.name] = None
                continue

            # Get type function.
            func_dtype = type_func(entry.name, entry.val_name if isinstance(entry, OptEntry) else None, entry.type_dsc)

            # If the target value is list of string, then apply the type function to the list contents.
            if isinstance(val_dict[entry.name], list):
                val_dict[entry.name] = [func_dtype(v) for v in val_dict[entry.name]]

            # Else, normally apply type function to the value.
            else:
                val_dict[entry.name] = func_dtype(val_dict[entry.name])

    # Assign type to the values.
    set_typed_value(argvec.posargs, arginf.posargs, verbose)
    set_typed_value(argvec.optargs, arginf.optargs, verbose)


#===================================================================================================
# Private classes and functions
#===================================================================================================

def auto_type(value: str) -> Any:
    """
    Automatically determine the data type using.

    Args:
        value (str): [IN] String expression of value.

    Returns:
        Any: Parsed value.

    Notes:
        Path values are not inferred automatically because there is no reliable way to distinguish
        a plain string from a file system path.
    """
    try:
        return ast.literal_eval(value)
    except (SyntaxError, TypeError, ValueError):
        return str(value)


def strtobool(s: str | None) -> bool:
    """
    Convert the given string to bool instance. The function `bool(...)` is not suitable
    for this purpose, because `bool("False")` returns `True`.

    Args:
        s (str | None): [IN] Input string.

    Returns:
        (bool | None): Corresponding boolean value.

    Examples:
        >>> strtobool("True")
        True
        >>> strtobool("False")
        False
        >>> strtobool(None)
        False
    """
    if s is None:
        return False

    if s.lower() in {"t", "true", "y", "yes", "on", "1"}:
        return True
    if s.lower() in {"f", "false", "n", "no", "off", "0"}:
        return False

    raise YadOptError.InvalidBoolValue(value=s)


def strtostr(s: str) -> str:
    """
    Convert string expression to string.

    Args:
        s (str): [IN] Input string.

    Returns:
        (str): Corresponding string value.

    Examples:
        >>> strtostr("this is a pen")
        'this is a pen'
        >>> strtostr("'this is a pen'")
        'this is a pen'
        >>> strtostr("'''this is a pen'''")
        'this is a pen'
        >>> strtostr("'1'")
        '1'
        >>> strtostr("'1.0'")
        '1.0'
    """
    try:
        return str(ast.literal_eval(s))
    except (SyntaxError, ValueError):
        return str(s)


# Define a map from data type string to data type.
DTYPE_HINTS: dict[str, Callable] = {
    # Booleans.
    "bool": strtobool, "boolean": strtobool,
    # Integers.
    "int": int, "integer": int,
    # Floating numbers.
    "flt": float, "float": float,
    # Strings.
    "str": strtostr, "string": strtostr,
    # Path.
    "path": Path,
    # Auto type.
    "auto": auto_type,
    # None.
    "nonetype": lambda x: None,
}


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
