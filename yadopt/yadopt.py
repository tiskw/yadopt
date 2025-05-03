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
import pprint
import textwrap
import sys

# For type hinting.
from collections.abc import Callable
from typing          import Any

# Import custom modules.
from .argopt  import parse_docstr_arg, parse_docstr_opt
from .argvec  import parse_argvec
from .checker import check_user_input
from .docstr  import get_section_lines
from .dtypes  import YadOptArgs, ArgEntry, OptEntry, UsageEntry, UserInput
from .errors  import YadOptError
from .gendat  import generate_data
from .hints   import auto_type, type_hint
from .usage   import parse_docstr_usage
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


def pretty_print(header: str, obj, indent: int = 4):
    """
    Pretty print.
    """
    print(header)
    print(textwrap.indent(pprint.pformat(obj), " " * indent))


def parse(docstr: str, argv: list[str] = sys.argv, type_fn: Callable = auto_type,
          force_continue: bool = False, verbose: bool = False) -> YadOptArgs:
    """
    Parse a given docstring and an argument vector, and return a YadoptArgs instance.

    Args:
        docstr         (str)      : Docstring to be parsed.
        argv           (list[str]): Argument vector.
        type_fn        (Callable) : A function that assign types to values.
        force_continue (bool)     : Never exit the software if True.
        verbose        (bool)     : Displays verbose messages that are useful for debugging.

    Returns:
        (YadOptArgs): Parsed command line arguments.
    """
    # Check default type.
    if not callable(type_fn):
        raise YadOptError["invalid_type_func"](type_fn)

    # Parse usage section.
    usage_docstr: str = "Usage:\n" + "\n".join(get_section_lines(docstr, "usage"))
    usages: list[UsageEntry] = parse_docstr_usage(docstr)
    if verbose:
        pretty_print("yadopt: Info: usages = ", usages)

    #
    args: list[ArgEntry] = parse_docstr_arg(docstr)
    if verbose:
        pretty_print("yadopt: Info: args = ", args)

    #
    opts: list[OptEntry] = parse_docstr_opt(docstr)
    if verbose:
        pretty_print("yadopt: Info: opts = ", opts)

    # Retokenize the input vector.
    argv = list(retokenize(copy.copy(argv)))
    if verbose:
        pretty_print("yadopt: Info: argv = ", argv)

    # Parse the given command line arguments.
    user_input: UserInput = parse_argvec(argv, args, opts, usages)
    if verbose:
        print("yadopt: Info: user_input =", user_input)

    # If appropriate usage not found, print message and return or exit.
    if len(user_input.pres) == len(user_input.args) == len(user_input.opts) == 0:

        # Print error message.
        print_error_message_user_input_not_match(usage_docstr, inspect.stack()[1])

        # Return if force_continue is True, otherwise exit.
        if force_continue:
            return YadOptArgs()
        sys.exit(os.EX_USAGE)

    # Check argvec using the parsed doc info.
    check_user_input(user_input, args, opts)

    # Apply type hints. This function also fill default values.
    type_hint(user_input, args, opts, type_fn, fill_default=True)

    # Print help message and exit if --help is specified, and return or exit.
    if user_input.opts.get("help", False) or ("help" in user_input.pres):

        # Print help message.
        print(docstr.strip())

        # Return if force_continue is True, otherwise exit this function.
        if force_continue:
            return YadOptArgs()
        sys.exit(os.EX_USAGE)

    # Returns data instance.
    return generate_data(user_input, args, opts, argv, docstr)


def wrap(*pargs: Any, **kwargs: Any) -> Callable:
    """
    Wrapper function for the command line parsing.

    Args:
        pargs  (list): Positional arguments for 'yadopt.parse' function.
        kwargs (dict): Keyword arguments for 'yadopt.parse' function.

    Returns:
        (Callable): Decorator function.

    Note:
        This function atually returns a function bacause this function
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
    Save the parsed command line arguments as a JSON file.

    Args:
        path   (str)       : Destination path.
        args   (YadOptArgs): Parsed command line arguments to be saved.
        indent (int)       : Indent size of the output JSON file.
    """
    # Conver the given path as an instance of pathlib.Path.
    path_out: pathlib.Path = pathlib.Path(path)

    # Determine the open function.
    open_fn: Callable = gzip.open if path_out.suffix.endswith(".gz") else open

    # Case 1: JSON file.
    if any(path_out.name.endswith(sfx) for sfx in [".json", ".json.gz"]):

        # Create the contents to save.
        data_json: dict = {"argv": getattr(args, "_argv_"), "docstr": getattr(args, "_dstr_")}

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
