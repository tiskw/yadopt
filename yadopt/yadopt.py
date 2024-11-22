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
    docinfo, usage = parse_docstr(docstr)

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
    return generate_dat(user_input, docinfo.args, docinfo.opts)


def wrap(*pargs, **kwargs) -> Callable:
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
    return vars(args)


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
    def get_class_str(value):
        """
        Returns string expression of the class of the given instance.
        """
        # Removes "<class '" from left and "'>" from right.
        return repr(type(value))[8:-2]

    # Conver the given path as an instance of pathlib.Path.
    path = pathlib.Path(path)

    # Convert to dictionary.
    args_dict = to_dict(args)

    # Determine the open function.
    open_func = gzip.open if path.suffix.endswith(".gz") else open

    # Case 1: JSON file.
    if any(path.name.endswith(sfx) for sfx in [".json", ".json.gz"]):

        # Create a dictionary of data types for each values in the dictionary "args_dict".
        data_types = {key:get_class_str(value) for key, value in args_dict.items()}

        # Escape the pathlib.Path instance because it is not writable to JSON file.
        args_dict = {k:(str(v) if isinstance(v, pathlib.Path) else v) for k, v in args_dict.items()}

        # Create a dictionary to be dumped as a JSON file.
        contents = {"data": args_dict, "type": data_types}

        # Compute the keyword arguments for the "json.dump" function.
        extra_kwargs = {"indent": 4}
        extra_kwargs.update(**kwargs)

        # Write to JSON file.
        with open_func(path, "wt") as ofp:
            json.dump(contents, ofp, **extra_kwargs)

    # Case 2: pickle file.
    elif any(path.name.endswith(sfx) for sfx in [".pkl", ".pkl.gz", ".pickle", ".pickle.gz"]):

        # Write to pickle file.
        with open_func(path, "wb") as ofp:
            pickle.dump(args_dict, ofp, **kwargs)

    # Otherwise: raise an error.
    else:
        raise YadOptError["invalid_file_type"]("yadopt.save", path)


def load(path: str, **kwargs: dict) -> YadOptArgs:
    """
    Load a parsed command line arguments from JSON or pickle file.

    Args:
        path   (str) : Source path.
        kwargs (dict): Extra keyword arguments that will be passed to the load functions.

    Returns:
        (YadOptArgs): Restored parsed command line arguments.
    """
    data_types_dict = {"bool": bool, "int": int, "float": float, "str": str,
                       "pathlib.PosixPath": pathlib.Path,
                       "pathlib.WindowsPath": pathlib.WindowsPath}

    # Conver the given path as an instance of pathlib.Path.
    path = pathlib.Path(path)

    # Determine the open function.
    open_func = gzip.open if path.suffix.endswith(".gz") else open

    # Case 1: JSON file.
    if any(path.name.endswith(sfx) for sfx in [".json", ".json.gz"]):

        # Load the JSON file.
        with open_func(path, "rt") as ifp:
            args_dict = json.load(ifp, **kwargs)

        # Get data contents and data types.
        args_dict, data_types = args_dict["data"], args_dict["type"]

        # Restore data types.
        for key in list(args_dict.keys()):
            dtype = data_types_dict[data_types[key]]
            args_dict[key] = dtype(args_dict[key])

        return YadOptArgs(args_dict)

    # Case 2: pickle file.
    if any(path.name.endswith(sfx) for sfx in [".pkl", ".pkl.gz", ".pickle", ".pickle.gz"]):

        # Load the pickle file.
        with open_func(path, "rb") as ifp:
            args_dict = pickle.load(ifp, **kwargs)

        return YadOptArgs(args_dict)

    # Otherwise: raise an error.
    raise YadOptError["invalid_file_type"]("yadopt.load", path)


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
