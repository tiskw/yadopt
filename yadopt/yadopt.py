"""
Yet another docopt, a human-friendly command line arguments parser.
"""

# Declare published functins and variables.
__all__ = ["parse", "wrap", "YadOptArgs"]

# Import standard libraries.
import copy
import functools
import inspect
import os
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
    def decorator(func):
        """
        """
        return functools.partial(func, args)

    # Parse command line arguments.
    args = parse(*pargs, **kwargs)

    # Returns decorator function.
    return decorator


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
