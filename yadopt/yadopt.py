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
import pickle
import sys

# For type hinting.
from collections.abc import Callable

# Import custom modules.
from .argvec  import parse_argvec
from .docstr  import parse_docstr
from .errors  import YadOptError
from .gendat  import generate_dat, YadOptArgs
from .checker import check_user_input
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


def parse(docstr: str, argv: list[str] = None, default_type: str|type = "auto",
          force_continue: bool = False) -> YadOptArgs:
    """
    Parse docstring and returns YadoptArgs instance.

    Args:
        docstr         (str)      : Docstring to be parsed.
        argv           (list[str]): Argument vector.
        default_type   (str)      : Default type.
        force_continue (bool)     : Never exit the software if True.

    Returns:
        (YadOptArgs): Parsed command line arguments.
    """
    # Check default type.
    if (default_type != "auto") and not callable(default_type):
        raise YadOptError["invalid_default_type"](default_type)

    # Use system argv values if not specified.
    if argv is None:
        argv = copy.copy(sys.argv)

    # Retokenize the input vector.
    argv = list(retokenize(argv))

    # Parse the given docstring and create a data class.
    docinfo, usage = parse_docstr(copy.copy(docstr))

    # Parse the given command line arguments.
    user_input = parse_argvec(argv, docinfo.usages, docinfo.opts)

    # If appropriate usage not found, print message and return or exit.
    if user_input is None:

        # Print error message.
        print_error_message_user_input_not_match(usage, inspect.stack()[1])

        # Return if force_continue is True, otherwise exit.
        if force_continue:
            return None
        sys.exit(os.EX_USAGE)

    # Check argvec using the parsed doc info.
    check_user_input(user_input, docinfo)

    # Print help message and exit if --help is specified, and return or exit.
    if ("help" in user_input.opts) or ("help" in user_input.pres):

        # Print help message.
        print(docstr.strip())

        # Return if force_continue is True, otherwise exit.
        if force_continue:
            return None
        sys.exit(os.EX_USAGE)

    # Returns data instance.
    return generate_dat(user_input, docinfo, argv)


def wrap(*pargs: list, **kwargs: dict) -> Callable:
    """
    Wrapper function for the command line parsing.

    Args:
        pargs  (list): Positional arguments for 'yadopt.parse' function.
        kwargs (dict): Keyword arguments for 'yadopt.parse' function.

    Returns:
        (Callable): Decorator function.

    Notes:
        This function atually returns a decorator function bacause this function
        is designed as a decorator function with argument (= docstr).
    """
    # Parse command line arguments.
    args = parse(*pargs, **kwargs)

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


def to_namedtuple(args: YadOptArgs) -> collections.namedtuple:
    """
    Convert YadOptArgs instance to a named tuple.

    Args:
        args (YadOptArgs): Parsed command line arguments.

    Returns:
        (namedtuple): Namedtuple of the given parsed arguments.
    """
    args_d = to_dict(args)
    fields = list(args_d.keys())
    return collections.namedtuple("YadOptArgsNamedtuple", fields)(**args_d)


def save(path: str, args: YadOptArgs, **kwargs: dict):
    """
    Save the parsed command line arguments as JSON or pickle file.

    Args:
        path   (str)       : Destination path.
        args   (YadOptArgs): Parsed command line arguments to be saved.
        kwargs (dict)      : Extra keyword arguments that will be passed to the dump functions.
    """
    # Conver the given path as an instance of pathlib.Path.
    path = pathlib.Path(path)

    # Determine the open function.
    open_func = gzip.open if path.suffix.endswith(".gz") else open

    # Case 1: a simple ".txt" file.
    if any(path.name.endswith(sfx) for sfx in [".txt", ".txt.gz"]):

        # Initialize the lines to be dumped.
        lines = []

        # Append preceding tokens.
        for key, value in args._user_.pres.items():
            if value == True:
                lines.append(key)

        # Append arguments.
        for key, value in args._user_.args.items():
            if value is not None:
                lines.append(value)

        # Append options.
        for key, value in to_dict(args).items():
            if key in args._user_.opts:
                lines.append(f"--{key} {value}")

        # Write to text file.
        with open_func(path, "wt") as ofp:
            ofp.write("\n".join(lines))

    # Case 2: a JSON file.
    # The author is thinking to support JSON format too, but not implemented yet.

    # Otherwise: raise an error.
    else:
        raise YadOptError["invalid_file_type"]("yadopt.save", path)


def load(path: str, docstr: str = None, **kwargs: dict) -> YadOptArgs:
    """
    Load a parsed command line arguments from JSON or pickle file.

    Args:
        path   (str) : Source path.
        docstr (str) : Docstring to be parsed.
        kwargs (dict): Extra keyword arguments that will be passed to the load functions.

    Returns:
        (YadOptArgs): Restored parsed command line arguments.
    """
    # Conver the given path as an instance of pathlib.Path.
    path = pathlib.Path(path)

    # Determine the open function.
    open_func = gzip.open if path.suffix.endswith(".gz") else open

    # Case 1: a simple ".txt" file.
    if any(path.name.endswith(sfx) for sfx in [".txt", ".txt.gz"]):

        # Read the text file and make an argument vector.
        argv = sum([line.split() for line in open_func(path, "rt")], [])

        # Append the first real argument vector at the top of the "argv".
        argv = sys.argv[0:1] + argv

        # Parse the argument vector using the given docstring.
        return parse(docstr, argv)

    # Case 2: a JSON file.
    # The author is thinking to support JSON format too, but not implemented yet.

    # Otherwise: raise an error.
    raise YadOptError["invalid_file_type"]("yadopt.load", path)


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
