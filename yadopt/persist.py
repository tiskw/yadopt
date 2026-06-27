"""
yadopt.persist - persist YadOptArgs object
"""

# Import standard libraries.
import gzip
import json
import pathlib

# For type hinting.
from collections.abc import Callable
from typing          import Any, Generator

# Import custom modules.
from .dtypes import Path
from .errors import YadOptError
from .hint   import DTYPE_HINTS
from .toml   import dump_toml, load_toml
from .yadopt import YadOptArgs, to_dict


#===================================================================================================
# Public classes and functions
#===================================================================================================

def save(path: str, args: YadOptArgs, indent: int = 4) -> None:
    """
    Save the parsed command line arguments as a file.

    Args:
        path   (str)       : [IN] Destination path.
        args   (YadOptArgs): [IN] Parsed command line arguments to be saved.
        indent (int)       : [IN] Indent size of the output JSON file.
    """
    # Convert the given path as an instance of pathlib.Path.
    path_out: pathlib.Path = pathlib.Path(path)

    # Determine the open function.
    open_fn: Callable = gzip.open if path_out.suffix.endswith(".gz") else open

    # Case 1: JSON file.
    if any(path_out.name.endswith(sfx) for sfx in [".json", ".json.gz"]):

        # Create the contents to save.
        data_json: dict[str, Any] = {
            "parsed": list(to_tagged_data(args)),
            "groups": getattr(args, "_groups_"),
        }

        # Write as a JSON file.
        with open_fn(path_out, "wt") as ofp:
            json.dump(data_json, ofp, indent=indent)

    # Case 2: TOML format.
    elif any(path_out.name.endswith(sfx) for sfx in [".toml", ".toml.gz"]):

        #
        parsed: list[dict[str, Any]] = list(to_tagged_data(args))
        groups: dict[str, list[str]]  = getattr(args, "_groups_")

        # Write as a TOML file.
        with open_fn(path_out, "wt") as ofp:
            ofp.write(dump_toml(parsed, groups))

    # Otherwise: raise an error.
    else:
        raise YadOptError.InvalidFileFormat(suffix=path_out.suffix)


def load(path: str) -> YadOptArgs:
    """
    Load a parsed command line arguments from a file.

    Args:
        path (str): [IN] Source path.

    Returns:
        (YadOptArgs): Restored parsed command line arguments.
    """
    # Convert the given path as an instance of pathlib.Path.
    path_out: pathlib.Path = pathlib.Path(path)

    # Determine the open function.
    open_fn: Callable = gzip.open if path_out.suffix.endswith(".gz") else open

    # Case 1: JSON file.
    if any(path_out.name.endswith(sfx) for sfx in [".json", ".json.gz"]):

        # Load the JSON file.
        with open_fn(path_out, "rt") as ifp:
            data_json: dict = json.load(ifp)

        # Validate the loaded structure.
        validate_persisted_data(data_json)

        # Restore the YadOptArgs instance.
        return from_tagged_data(data_json["parsed"], data_json["groups"])

    # Case 2: TOML format.
    if any(path_out.name.endswith(sfx) for sfx in [".toml", ".toml.gz"]):

        # Load the TOML file.
        with open_fn(path_out, "rb") as ifp:
            data_toml: dict = load_toml(ifp)

        # Validate the loaded structure.
        validate_persisted_data(data_toml)

        # Restore the YadOptArgs instance.
        return from_tagged_data(data_toml["parsed"], data_toml["groups"])

    # Otherwise: raise an error.
    raise YadOptError.InvalidFileFormat(suffix=path_out.suffix)


#===================================================================================================
# Private classes and functions
#===================================================================================================

def to_tagged_data(args: YadOptArgs) -> Generator[dict[str, Any], None, None]:
    """
    Converts the given YadOptArgs instance to a tagged data.

    Args:
        args (YadOptArgs): Source of the tagged data.

    Yields:
        (dict[str, Any]): An entry of the tagged data.
    """
    def get_scalar_dtype_str(value: Any) -> str:
        return "Path" if isinstance(value, Path) else type(value).__name__

    def get_list_dtype_str(value: list[Any]) -> str:
        return get_scalar_dtype_str(value[0]) if value else "str"

    for key, value in to_dict(args).items():

        # Get the string expression of the data type.
        dtype_str: str = get_list_dtype_str(value) if isinstance(value, list) else get_scalar_dtype_str(value)

        # Convert the value to a string expression.
        value_str: str | list[str] = [str(v) for v in value] if isinstance(value, list) else str(value)

        # Yield the tagged dictionary entry.
        yield {"name": key, "value": value_str, "dtype": dtype_str}


def from_tagged_data(parsed: list[dict[str, Any]], groups: dict[str, list[str]]) -> YadOptArgs:
    """
    Restores a YadOptArgs instance from the given tagged dictionary and docstring.

    Args:
        parsed (list[dict[str, Any]]): [IN] List of tagged dictionaries.
        groups (dict[str, list[str]]) : [IN] Dictionary of groups.

    Returns:
        (YadOptArgs): Restored YadOptArgs instance.
    """
    args: YadOptArgs = YadOptArgs(argvec=None, arginf=None, groups=groups)

    for entry in parsed:

        # Get the data type of the entry.
        dtype: Callable = DTYPE_HINTS.get(entry["dtype"].lower(), str)

        # Restore the value of the entry from its string expression.
        value: Any = [dtype(v) for v in entry["value"]] if isinstance(entry["value"], list) else dtype(entry["value"])

        # Set the restored value as an attribute of the YadOptArgs instance.
        setattr(args, entry["name"], value)

    return args


def validate_persisted_data(data: dict[str, Any]) -> None:
    """
    Validate persisted JSON/TOML data before restoration.
    """
    # Case 1: The top-level object must be a dictionary containing "parsed" and "groups" keys.
    if not isinstance(data, dict):
        raise YadOptError.InvalidTomlFile(reason="Top-level persisted object must be a dictionary.")

    # Case 2: The "parsed" key must be a list of dictionaries, and the "groups" key must be a dictionary.
    if "parsed" not in data or "groups" not in data:
        raise YadOptError.InvalidTomlFile(reason="Missing 'parsed' or 'groups' key.")
    if not isinstance(data["parsed"], list):
        raise YadOptError.InvalidTomlFile(reason="The 'parsed' key must be a list.")
    if not isinstance(data["groups"], dict):
        raise YadOptError.InvalidTomlFile(reason="The 'groups' key must be a dictionary.")

    # Case 3: Each entry in the "parsed" list must be a dictionary containing "name", "value", and "dtype" keys.
    for entry in data["parsed"]:
        if not isinstance(entry, dict):
            raise YadOptError.InvalidTomlFile(reason="Each parsed entry must be a dictionary.")
        if not {"name", "value", "dtype"}.issubset(entry.keys()):
            raise YadOptError.InvalidTomlFile(reason="Each parsed entry must contain 'name', 'value', and 'type'.")


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
