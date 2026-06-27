"""
yadopt.toml - TOML parser and writer for YadOpt
"""

# Declare published functions and variables.
__all__ = ["dump_toml", "load_toml"]

# Import standard libraries.
import datetime
import getpass
import importlib
import json
import platform
import socket
import subprocess
import sys
import textwrap

# For type hinting.
from typing import Any, TextIO

# Import custom modules.
from .errors import YadOptError


#===================================================================================================
# Public classes and functions
#===================================================================================================

def dump_toml(parsed: list[dict], groups: dict[str, list[str]]) -> str:
    """
    Convert the given YadOptArgs instance to a TOML string.

    Args:
        args   (YadOptArgs): [IN] Parsed command line arguments to be converted.
        parsed (list[dict]): [IN] List of tagged dictionaries of the parsed arguments.
        groups (dict)      : [IN] Dictionary of groups.

    Returns:
        (str): TOML string.
    """
    # Raise an error if TOML is not supported by Python.
    check_toml_supported()

    # Create TOML file template.
    template_toml: str = textwrap.dedent("""
        [YadOptArgs]

        # Tagged dictionary of the parsed arguments.
        parsed = {parsed}

        # Group information.
        groups = {groups}

        [Metadata]

        # Information of execution environment and time.
        hostname = '{hostname}'
        username = '{username}'
        platform = '{platform}'
        timestamp = '{timestamp}'

        # Python runtime information.
        python_ver = '{python_ver}'

        # Git information.
        git_hash = '{git_hash}'
        git_changed = {git_changed}
    """).strip()

    # Convert the given parsed arguments and groups to TOML string.
    parsed_str: str = "[\n"
    for entry in parsed:
        parsed_str += " " * 4 + to_toml_dict(entry) + ",\n"
    parsed_str = parsed_str.rstrip(",\n ") + "\n]"

    # Convert the given groups to TOML string.
    groups_str: str = to_toml_dict(groups)

    return template_toml.format(parsed=parsed_str, groups=groups_str, **get_metadata())


def load_toml(fp: TextIO) -> dict:
    """
    Load TOML file and returns YadOptArgs section.

    Args:
        fp (TextIO): File pointer of the target file.

    Returns:
        (dict): Contents of the TOML file.
    """
    # Raise an error if TOML is not supported by Python.
    check_toml_supported()

    # Import tomllib library.
    tomllib = load_tomllib()

    # Load text from the given file pointer and parse it as TOML.
    data_toml: dict = tomllib.load(fp)

    if "YadOptArgs" not in data_toml:
        raise YadOptError.InvalidTomlFile(reason="Missing 'YadOptArgs' section")

    return data_toml["YadOptArgs"]


#===================================================================================================
# Private classes and functions
#===================================================================================================

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


def get_metadata() -> dict:
    """
    Returns metadata information.

    Returns:
        (dict): Metadata dictionary.
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

    return {"hostname"   : socket.gethostname(),
            "username"   : get_username(),
            "platform"   : platform.platform(),
            "timestamp"  : get_datetime_str(),
            "python_ver" : platform.python_version(),
            "git_hash"   : get_git_hash(),
            "git_changed": get_git_changed()}


def to_toml_dict(data_dict: dict[str, Any]) -> str:
    """
    Convert the given dictionary to a string expression in a TOML file.

    Args:
        data_dict (dict[str, Any]): [IN] Input dictionary.
    """
    output: str = "{"
    for key, value in data_dict.items():
        output += json.dumps(key) + "=" + json.dumps(value) + ", "
    return output.rstrip(", ") + "}"


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
