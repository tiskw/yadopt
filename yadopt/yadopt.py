"""
Yet another docopt, a human-friendly command line arguments parser.
"""

# Declare published functins and variables.
__all__ = ["parse", "wrap", "to_dict", "to_namedtuple", "save", "load"]

# Import standard libraries.
import collections
import copy
import functools
import gzip
import inspect
import json
import os
import pathlib
import sys

# For type hinting.
from collections.abc import Callable
from typing          import Any

# Import custom modules.
from .argvec  import parse_argvec
from .checker import check_user_input
from .docstr  import parse_docstr
from .dtypes  import YadOptArgs, DocStrInfo, UserInput
from .errors  import YadOptError
from .gendat  import generate_data
from .hints   import auto_type, type_hint
from .utils   import retokenize


def print_error_message_user_input_not_match(usage: str, frame_info: inspect.FrameInfo):
    """
    Print error message when user input does not match with the usages.

    Args:
        usage      (str)              : Usage string.
        frame_info (inspect.FrameInfo): FrameInfo object of inspect.
    """
    # Compute error source position.
    line_num = frame_info.lineno
    funcname = frame_info.function
    filepath = frame_info.filename
    filename = os.path.basename(filepath)
    err_pos  = f"{filename}/{funcname}/L.{line_num}"

    # Print error message.
    print(usage)
    print("")
    print(f"Error at {err_pos}: error: user input does not match with the usage")


def parse(docstr: str, argv: list[str] = sys.argv, type_fn: Callable = auto_type,
          force_continue: bool = False) -> YadOptArgs:
    """
    Parse docstring and returns YadoptArgs instance.

    Args:
        docstr         (str)      : Docstring to be parsed.
        argv           (list[str]): Argument vector.
        type_fn        (Callable) : A function that assign types to values.
        force_continue (bool)     : Never exit the software if True.

    Returns:
        (YadOptArgs): Parsed command line arguments.
    """
    # Check default type.
    if not callable(type_fn):
        raise YadOptError["invalid_type_func"](type_fn)

    # Retokenize the input vector.
    argv = list(retokenize(copy.copy(argv)))

    # Parse the given docstring and create a data class.
    dsinfo: DocStrInfo = parse_docstr(copy.copy(docstr))

    # Parse the given command line arguments.
    user_input: UserInput = parse_argvec(argv, dsinfo)

    # If appropriate usage not found, print message and return or exit.
    if len(user_input.pres) == len(user_input.args) == len(user_input.opts) == 0:

        # Print error message.
        print_error_message_user_input_not_match(dsinfo.utxt, inspect.stack()[1])

        # Return if force_continue is True, otherwise exit.
        if force_continue:
            return YadOptArgs()
        sys.exit(os.EX_USAGE)

    # Check argvec using the parsed doc info.
    check_user_input(user_input, dsinfo)

    # Apply type hints. This function also fill default values.
    type_hint(user_input, dsinfo, type_fn, fill_default=True)

    # Print help message and exit if --help is specified, and return or exit.
    if user_input.opts.get("help", False) or ("help" in user_input.pres):

        # Print help message.
        print(docstr.strip())

        # Return if force_continue is True, otherwise exit.
        if force_continue:
            return YadOptArgs()
        sys.exit(os.EX_USAGE)

    # Returns data instance.
    return generate_data(user_input, dsinfo, argv)


def wrap(*pargs: Any, **kwargs: Any) -> Callable:
    """
    Wrapper function for the command line parsing.

    Args:
        pargs  (list): Positional arguments for 'yadopt.parse' function.
        kwargs (dict): Keyword arguments for 'yadopt.parse' function.

    Returns:
        (Callable): Decorator function.

    Note:
        This function atually returns a decorator function bacause this function
        is designed as a decorator function with argument (= docstr).
    """
    # Parse command line arguments.
    args: YadOptArgs = parse(*pargs, **kwargs)

    # Instanciate a decorator function and returns it.
    return lambda func: functools.partial(func, args)


def to_dict(args: YadOptArgs) -> dict:
    """
    Convert YadOptArgs instance to a dictionary.

    Args:
        args (YadOptArgs): Parsed command line arguments.

    Returns:
        (dict): Dictionary of the given parsed arguments.
    """
    return {key:val for key, val in vars(args).items() if (key[0] != "_") and (key[-1] != "_")}


def to_namedtuple(args: YadOptArgs) -> tuple[Any, ...]:
    """
    Convert YadOptArgs instance to a named tuple.

    Args:
        args (YadOptArgs): Parsed command line arguments.

    Returns:
        (namedtuple): Namedtuple of the given parsed arguments.
    """
    args_d: dict = to_dict(args)
    fields: list = list(args_d.keys())
    return collections.namedtuple("YadOptArgsNt", fields)(**args_d)


def save(path: str, args: YadOptArgs, indent: int = 4) -> None:
    """
    Save the parsed command line arguments as a text file.

    Args:
        path (str)       : Destination path.
        args (YadOptArgs): Parsed command line arguments to be saved.
    """
    # Conver the given path as an instance of pathlib.Path.
    path_out: pathlib.Path = pathlib.Path(path)

    # Determine the open function.
    open_fn: Callable = gzip.open if path_out.suffix.endswith(".gz") else open

    # Case 1: JSON file.
    if any(path_out.name.endswith(sfx) for sfx in [".json", ".json.gz"]):

        # Create the contents to save.
        data_json: dict = {"argv": getattr(args, "_argv_"), "docstr": getattr(args, "_info_").dstr}

        # Write as a JSON file.
        with open_fn(path_out, "wt") as ofp:
            json.dump(data_json, ofp, indent=indent)

    # Case 2: ??? format.
    # The author is thinking to support JSON format too, but not implemented yet.

    # Otherwise: raise an error.
    else:
        raise YadOptError["invalid_file_type"]("yadopt.save", path)


def load(path: str) -> YadOptArgs:
    """
    Load a parsed command line arguments from a text file.

    Args:
        path (str): Source path.

    Returns:
        (YadOptArgs): Restored parsed command line arguments.
    """
    # Conver the given path as an instance of pathlib.Path.
    path_out: pathlib.Path = pathlib.Path(path)

    # Determine the open function.
    open_fn: Callable = gzip.open if path_out.suffix.endswith(".gz") else open

    # Case 1: JSON file.
    if any(path_out.name.endswith(sfx) for sfx in [".json", ".json.gz"]):

        # Load the JSON file.
        with open_fn(path_out, "rt") as ifp:
            data_json: dict = json.load(ifp)

        # Parse the loaded argument vector using the loaded docstring.
        return parse(**data_json)

    # Case 2: ??? format.
    # The author is thinking to support JSON format too, but not implemented yet.

    # Otherwise: raise an error.
    raise YadOptError["invalid_file_type"]("yadopt.load", path)


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
