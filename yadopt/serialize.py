"""
yadopt.serialize - serialize and deserialize parsed command line arguments.
"""
from __future__ import annotations

# Import standard libraries.
import dataclasses
import datetime
import getpass
import gzip
import json
import platform
import socket
import subprocess

# For type hinting.
from collections.abc import Callable
from typing          import Any

# Import custom modules.
from .datamodel import make_yadoptargs_data
from .dtypes    import Path
from .errors    import YadOptError
from .toml      import dump_toml, load_toml
from .yadopt    import YadOptArgs, parse

# Declare published functions and variables.
__all__ = ["save", "load"]


def save(path: str | Path, args: YadOptArgs, metadata: bool = True, indent: int = 4) -> None:
    """
    Save the parsed command line arguments as a file.

    Args:
        path     (str | Path): [IN] Destination path.
        args     (YadOptArgs): [IN] Parsed command line arguments to be saved.
        metadata (bool)      : [IN] If True, include metadata information in the output file.
        indent   (int)       : [IN] Indent size of the output JSON file.
    """
    # Convert the given path as an instance of Path.
    path_out: Path = Path(path) if isinstance(path, str) else path

    # Validate the file format.
    if not any(path_out.name.endswith(sfx) for sfx in [".json", ".json.gz", ".toml", ".toml.gz"]):
        raise YadOptError.InvalidFileFormat(suffix=path_out.suffix)

    # Determine the open function.
    open_fn: Callable = gzip.open if path_out.suffix.endswith(".gz") else open

    # Generate a dictionary from the parsed arguments.
    data_dict: dict[str, Any] = generate_dict_from_parsed_args(args, metadata)

    # Save as a JSON/TOML file.
    if any(path_out.name.endswith(sfx) for sfx in [".json", ".json.gz"]):
        with open_fn(path_out, "wt") as ofp:
            json.dump(data_dict, ofp, indent=indent)
    elif any(path_out.name.endswith(sfx) for sfx in [".toml", ".toml.gz"]):
        with open_fn(path_out, "wt") as ofp:
            ofp.write(dump_toml(data_dict))


def load(path: str | Path) -> YadOptArgs:
    """
    Load a parsed command line arguments from a file.

    Args:
        path (str | Path): [IN] Source path.

    Returns:
        (YadOptArgs): Restored parsed command line arguments.
    """
    # Convert the given path as an instance of Path.
    path_out: Path = Path(path) if isinstance(path, str) else path

    # Validate the file format (only checking the suffix).
    if not any(path_out.name.endswith(sfx) for sfx in [".json", ".json.gz", ".toml", ".toml.gz"]):
        raise YadOptError.InvalidFileFormat(suffix=path_out.suffix)

    # Determine the open function.
    open_fn: Callable = gzip.open if path_out.suffix.endswith(".gz") else open

    # Load the given file as a dictionary.
    if any(path_out.name.endswith(sfx) for sfx in [".json", ".json.gz"]):
        with open_fn(path_out, "rt") as ifp:
            data_dict = json.load(ifp)
    if any(path_out.name.endswith(sfx) for sfx in [".toml", ".toml.gz"]):
        with open_fn(path_out, "rb") as ifp:
            data_dict = load_toml(ifp)

    # If the loaded data is in the legacy format (2026.01.05), restore it accordingly.
    if any(path_out.name.endswith(sfx) for sfx in [".toml", ".toml.gz"]):
        if (args_regacy := from_20260105_format(data_dict)) is not None:
            return args_regacy

    # Validate the loaded structure.
    validate_persisted_data(data_dict)

    return generate_parsed_args_from_dict(data_dict)


def generate_dict_from_parsed_args(args: YadOptArgs, metadata: bool) -> dict[str, Any]:
    """
    Generate a dictionary from the parsed command line arguments.

    Args:
        args     (YadOptArgs): [IN] Parsed command line arguments.
        metadata (bool)      : [IN] If True, include metadata information in the output dictionary.

    Returns:
        (dict[str, Any]): Dictionary containing the parsed arguments and metadata.
    """
    # Get the groups dictionary from the YadOptArgs instance.
    groups: dict[str, list[str]] = getattr(args, "_groups_", {})

    # Create an output dictionary with group names as keys and empty lists as values.
    data_dict: dict[str, Any] = {group_name: {} for group_name in groups.keys()}

    for group_name, names in groups.items():

        # Iterate over the names in the group.
        for name in filter(lambda name: hasattr(args, name), names):

            # Get the value of the attribute from the YadOptArgs instance.
            value: Any = encode_value(getattr(args, name))

            # Append the (name, value) tuple to the corresponding group in the output dictionary.
            data_dict[group_name][name] = value

    # Add dataclass information to the output dictionary.
    data_dict["_YADOPT_DATACLASS_INFO_"] = {
        "class_name": args.__class__.__name__,
    }

    # Add metadata information to the output dictionary.
    data_dict["_YADOPT_METADATA_"] = get_metadata(metadata)

    return data_dict


def generate_parsed_args_from_dict(data_dict: dict[str, Any]) -> YadOptArgs:
    """
    Generate a YadOptArgs instance from the given dictionary.

    Args:
        data_dict (dict[str, Any]): [IN] Dictionary containing the parsed arguments and metadata

    Returns:
        (YadOptArgs): Restored parsed command line arguments.
    """
    # Extract the body of the data dictionary.
    data_dict_body: dict[str, Any] = {}
    for group_name, values in data_dict.items():
        if not (group_name.startswith("_") and group_name.endswith("_")):
            data_dict_body.update(values)

    # Decode the values in the body of the data dictionary.
    for key in data_dict_body.keys():
        data_dict_body[key] = decode_value(data_dict_body[key])

    # Determine the dataclass type based on the stored class name.
    dataclass_name: str = data_dict["_YADOPT_DATACLASS_INFO_"]["class_name"]
    if dataclass_name != YadOptArgs.__name__:
        dataclass_type = dataclasses.make_dataclass(cls_name=dataclass_name, fields=[], eq=False, bases=(YadOptArgs,))
    else:
        dataclass_type = YadOptArgs

    # Create a groups dictionary from the data dictionary.
    groups: dict[str, list[str]] = {group_name: list(values.keys()) for group_name, values in data_dict.items()}

    return make_yadoptargs_data(data_dict_body, groups, dataclass_type)


def encode_value(value: Any) -> Any:
    """
    Convert the value to a safer representation for JSON/TOML serialization.

    Args:
        value (Any): [IN] Value to be encoded.

    Returns:
        (Any): Encoded value suitable for JSON/TOML serialization.
    """
    # Case 1: None value.
    if value is None:
        return '"None"'

    # Case 2: Path object.
    if isinstance(value, Path):
        return f"Path({value})"

    # Case 3: List of values.
    if isinstance(value, list) and len(value) > 0:
        return [encode_value(v) for v in value]

    # Otherwise, return the value as is.
    return value


def decode_value(value: Any) -> Any:
    """
    Convert the encoded value back to its original representation.

    Args:
        value (Any): [IN] Encoded value.

    Returns:
        (Any): Decoded value in its original representation.
    """
    # Case 1: None value.
    if value == '"None"':
        return None

    # Case 2: Path object.
    if isinstance(value, str) and value.startswith("Path(") and value.endswith(")"):
        return Path(value[5:-1])

    # Case 3: List of values.
    if isinstance(value, list) and len(value) > 0:
        return [decode_value(v) for v in value]

    # Otherwise, return the value as is.
    return value


def validate_persisted_data(data_dict: dict[str, Any]) -> None:
    """
    Validate persisted JSON/TOML data before restoration.
    """
    # Case 1: The top-level object must be a dictionary containing "parsed" and "groups" keys.
    if not isinstance(data_dict, dict):
        raise YadOptError.InvalidTomlFile(reason="Top-level persisted object must be a dictionary.")

    # Case 2: The "_YADOPT_METADATA_" key must be a dictionary.
    if "_YADOPT_METADATA_" not in data_dict:
        raise YadOptError.InvalidTomlFile(reason="Missing '_YADOPT_METADATA_' key.")
    if not isinstance(data_dict["_YADOPT_METADATA_"], dict):
        raise YadOptError.InvalidTomlFile(reason="The '_YADOPT_METADATA_' key must be a list.")

    # Case 3: Each group in the top-level dictionary must be a dictionary.
    for group_name in filter(lambda name: name != "_YADOPT_METADATA_", data_dict.keys()):
        if not isinstance(data_dict[group_name], dict):
            raise YadOptError.InvalidTomlFile(reason="Each parsed entry must be a dictionary.")


def get_metadata(contains_extra: bool = True) -> dict[str, str]:
    """
    Returns metadata information.

    Args:
        contains_extra (bool): [IN] If True, include extra metadata information.

    Returns:
        (dict[str, str]): Metadata dictionary.
    """
    def get_datetime_str() -> str:
        """
        Returns datetime string with timezone.
        """
        # Get the current time in UTC timezone, convert it to the system timezone, and stringify.
        return datetime.datetime.now(datetime.timezone.utc).astimezone().strftime("%Y/%m/%d %H:%M:%S %Z")

    def get_git_hash() -> str:
        """
        Get git information.
        """
        output: bytes = run_command(["git", "rev-parse", "HEAD"])
        return "???" if len(output)== 0 else output.decode().strip()

    def get_git_changed() -> str:
        """
        Returns 'true' if Git status is 'changed' otherwise 'false'.
        """
        output: bytes = run_command(["git", "status", "--porcelain"])
        return "false" if len(output) == 0 else "true"

    def get_username() -> str:
        """
        Get username.
        """
        try:
            return getpass.getuser()
        except (ImportError, KeyError, OSError):
            return "???"

    def run_command(tokens: list[str]) -> bytes:
        """
        Run the given command as a shell command.
        """
        try:
            return subprocess.run(tokens, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
        except (subprocess.SubprocessError, FileNotFoundError):
            return b"???"

    # If contains_extra is False, return only the timestamp.
    if not contains_extra:
        return {"timestamp": get_datetime_str()}

    # Otherwise, return detailed metadata.
    return {"hostname"   : socket.gethostname(),
            "username"   : get_username(),
            "platform"   : platform.platform(),
            "timestamp"  : get_datetime_str(),
            "python_ver" : platform.python_version(),
            "git_hash"   : get_git_hash(),
            "git_changed": get_git_changed()}


def from_20260105_format(data_dict: dict) -> YadOptArgs | None:
    """
    Restore a parsed command line arguments from a legacy TOML file (2026.01.05 format).

    Args:
        data_dict (dict): [IN] Loaded JSON/TOML data as a dictionary.

    Returns:
        (YadOptArgs): Restored parsed command line arguments.
    """
    # Check if the data_dict has the expected keys for the legacy format.
    if set(data_dict.keys()) != {"YadOptArgs", "Metadata"}:
        return None

    # Extract the argv from the dictionary and check its type.
    argv = data_dict["YadOptArgs"]["argv"]
    if not isinstance(argv, list) or not all(isinstance(arg, str) for arg in argv):
        return None

    # Extract the docstr from the dictionary and check its type.
    docstr = data_dict["YadOptArgs"]["docstr"]
    if not isinstance(docstr, str):
        return None

    # Parse the argument vector using the docstr.
    return parse(docstr, argv[1:])


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
