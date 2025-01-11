"""
Assign types based on type hinting string.
"""

# Declare published functins and variables.
__all__ = ["auto_type", "type_hint"]

# Import standard libraries.
import ast
import pathlib

# For type hinting.
from collections.abc import Callable

# Import custom modules.
from .dtypes  import ArgEntry, OptEntry, DocStrInfo, UserInput
from .utils   import strtobool

# Define a map from data type string to data type.
DTYPE_HINTS: dict[str, Callable] = {
    "bool": strtobool, "boolean": strtobool, "int": int, "integer": int,
    "flt": float, "float": float, "str": str, "string": str, "path": pathlib.Path
}


def auto_type(value: str) -> int | float | str | pathlib.Path:
    """
    Automatically determine the data type.
    """
    try:
        return ast.literal_eval(value)
    except ValueError:
        return str(value)


def fill_default_values(user_input: UserInput, dsinfo: DocStrInfo):
    """
    Fill default values.

    Args:
        user_input (UserInput) : Parsed user input.
        dsinfo     (DocStrInfo): Parsed docstring info.
    """
    for opt_entry in dsinfo.opts:
        if opt_entry.name not in user_input.opts:
            user_input.opts[opt_entry.name] = opt_entry.default

    return user_input


def type_hint(user_input: UserInput, dsinfo: DocStrInfo, type_fn: Callable, fill_default: bool) -> None:
    """
    Apply type hints.

    Args:
        user_input (UserInput) : Parsed user input.
        dsinfo     (DocStrInfo): Parsed docstring info.
        type_fn    (Callable)  : A function that assign types to values.
    """
    def set_typed_value(val_dict: dict, list_entries: list[ArgEntry] | list[OptEntry], type_fn: Callable) -> None:
        """
        Get typed value.
        """
        for entry in list_entries:

            # Do nothing if the entry is not in the value dictionary.
            if entry.name not in val_dict:
                continue

            # If the value is None, not necessary to assign type.
            if val_dict[entry.name] is None:
                continue

            # Get type function.
            fn = DTYPE_HINTS.get(entry.dtype_str, auto_type) if (type_fn is auto_type) else type_fn

            # If the target value is list of string, then apply the type function
            # to the list contents.
            if isinstance(val_dict[entry.name], list):
                val_dict[entry.name] = [fn(v) for v in val_dict[entry.name]]

            # Else, normaly apply type function to the value.
            else:
                val_dict[entry.name] = fn(val_dict[entry.name])

    # Fill deafult values to the user input.
    if fill_default:
        fill_default_values(user_input, dsinfo)

    # Assign type to the values.
    set_typed_value(user_input.args, dsinfo.args, type_fn)
    set_typed_value(user_input.opts, dsinfo.opts, type_fn)


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
