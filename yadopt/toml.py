"""
yadopt.toml - TOML parser and writer for YadOpt
"""
from __future__ import annotations

# Import standard libraries.
import importlib
import json
import sys

# For type hinting.
from typing import Any, TextIO

# Import custom modules.
from .errors import YadOptError

# Declare published functions and variables.
__all__ = ["dump_toml", "load_toml"]


def dump_toml(data_dict: dict[str, Any]) -> str:
    """
    Convert the given YadOptArgs instance to a TOML string.

    Args:
        data_dict (dict[str, Any]): [IN] Input dictionary.

    Returns:
        (str): TOML string.
    """
    # Raise an error if TOML is not supported by Python.
    check_toml_supported()

    # Initialize the output string.
    output: str = ""

    for group_name, dict_key_value in data_dict.items():

        # Add group name to the output string.
        output += f"[{group_name}]\n"

        # Add key-value pairs to the output string.
        for key, val in dict_key_value.items():
            output += f"{key} = {to_toml_value(val)}\n"

        # Add a newline after each group for readability.
        output += "\n"

    return output.strip()


def load_toml(ifp: TextIO) -> dict[str, Any]:
    """
    Load a TOML file and return its contents as a dictionary.

    Args:
        ifp (str | Path | IO): [IN] Input file path or file-like object.

    Returns:
        (dict[str, Any]): Dictionary representation of the TOML file.
    """
    # Raise an error if TOML is not supported by Python.
    check_toml_supported()

    # Load the TOML module.
    tomllib = load_tomllib()

    # Load the TOML file.
    return tomllib.load(ifp)


def load_tomllib() -> Any:
    """
    Load module for loading TOML file.
    """
    # Determine the module name to load.
    module_name: str = "tomllib" if (sys.version_info >= (3, 11)) else "tomli"

    # Load the module.
    return importlib.import_module(module_name)


def check_toml_supported() -> bool:
    """
    Returns True if the current Python supports TOML.

    Returns:
        (bool): True if the runtime Python supports TOML.
    """
    try:
        load_tomllib()
    except ImportError as e:
        raise YadOptError.CannotLoadTomllib() from e

    return True


def to_toml_value(value: Any) -> str:
    """
    Convert the given value to a string expression in a TOML file.

    Args:
        value (Any): [IN] Input value.
    """
    # Boolean value.
    if isinstance(value, bool):
        return str(value).lower()

    # Other values.
    return json.dumps(value)


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
