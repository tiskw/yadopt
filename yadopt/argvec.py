"""
yadopt.argvec - argument vector parser
"""

# Declare published functions and variables.
__all__ = ["ArgVector", "parse_argvec", "standardize_option_names"]

# Import standard libraries.
import dataclasses
import re

# For type hinting.
from typing import Any, Generator

# Import custom modules.
from .dtypes import Deque, PosEntry, OptEntry, ArgsInfo
from .errors import YadOptError, get_candidate_message
from .utils  import is_python_value


#===================================================================================================
# Public classes and functions
#===================================================================================================

@dataclasses.dataclass
class ArgVector:
    """
    Information of user input.
    """
    posargs: dict[str, Any]
    optargs: dict[str, Any]
    argv   : list[str]

    def __str__(self) -> str:
        text  = "ArgVector:\n"
        text += " |- posargs = " + str(self.posargs) + "\n"
        text += " |- optargs = " + str(self.optargs) + "\n"
        text += " |- args = "    + str(self.argv)
        return text.strip()


def parse_argvec(argv: list[str], arginf: ArgsInfo, verbose: bool) -> ArgVector:
    """
    Parse a given argument vector and return an ArgVector instance.

    Args:
        argv    (list[str]): [IN] Argument vector.
        arginf  (ArgsInfo) : [IN] Parsed result of docstring.
        verbose (bool)     : [IN] Displays verbose messages that are useful for debugging.

    Returns:
        (ArgVector): Parsed argument vector.
    """
    # Initialize the output variable.
    argvec: ArgVector = ArgVector(posargs={}, optargs={}, argv=argv)

    # Make a copy of the argument vector because the following process modifies the argument vector in-place.
    argv_copy: Deque[str] = Deque(argv[1:])

    # Get a map from option name to option entry.
    opt_entries: dict[str, OptEntry] = {name: opt for opt in arginf.optargs for name in opt.raw_names}

    # Initialize the number of argument tokens and a flag whether currently processing multiple positional arguments.
    n_args: int  = len(arginf.posargs)
    is_mul: bool = False

    # Initialize a flag whether accepting option tokens.
    acpt_opt: bool = True

    while argv_copy:

        # Get the next token.
        arg: str = argv_copy.popleft()

        # Case 1: Double delimiter makes the following tokens be treated as argument tokens.
        if arg == "--":
            acpt_opt = False

        # Case 2: Long or short option.
        elif acpt_opt and arg.startswith("-") and is_option_token(arg, opt_entries):
            parse_argvec_opt(arg, argvec, argv_copy, opt_entries)

        # Case 3: Unknown option token.
        elif acpt_opt and arg.startswith("-") and not is_python_value(arg):

            # Get the candidate option names.
            cands: list[str] = [name for opt_entry in arginf.optargs for name in opt_entry.raw_names]

            raise YadOptError.UnknownOption(opt_name=arg, candidate=get_candidate_message(arg, cands))

        # Case 4: Argument token.
        else:
            (n_args, is_mul) = parse_argvec_pos(arg, arginf, argvec, n_args, is_mul)

    if verbose:
        print("In parse_argvec:")
        print("  - n_args =", n_args)
        print("  - is_mul =", is_mul)
        print("  - acpt_opt =", acpt_opt)

    # Raise an error if there are missing positional arguments.
    if (n_args > 0) and not is_mul:

        # Get the names of missing arguments.
        arg_names_missing: list[str] = [entry.name for entry in arginf.posargs[-n_args:]]

        # Flatten if the number of missing arguments is one.
        arg_names_missing_str: str = arg_names_missing[0] if (len(arg_names_missing) == 1) else str(arg_names_missing)

        raise YadOptError.MissingArgument(missing_args=arg_names_missing_str)

    return argvec


def standardize_option_names(argv: list[str], opt_entries: list[OptEntry]) -> Generator[str, None, None]:
    """
    Standardize option names of argument vector.
    For example, "-h" -> "--help".

    Args:
        argv        (list[str])     : [IN] Argument vector.
        opt_entries (list[OptEntry]): [IN] List of option entries parsed from docstring.

    Yields:
        (str): Standardized option names.
    """
    # Get a map from alternative name to standard name.
    alt_names: dict[str, str] = {opt.name_alt: opt.name for opt in opt_entries if opt.name_alt is not None}

    for token in argv:

        # Skip the non-option tokens.
        if not token.startswith("-"):
            yield token
            continue

        # Split the option token into prefix and name.
        name  : str = token.lstrip("-")
        prefix: str = "-" * (len(token) - len(name))

        yield "--" + alt_names[name] if name in alt_names else prefix + name.replace("-", "_")


#===================================================================================================
# Private classes and functions
#===================================================================================================

def parse_argvec_pos(arg: str, arginf: ArgsInfo, argvec: ArgVector, n_args: int, is_mul: bool) -> tuple[int, bool]:
    """
    Parse a positional argument token and update the argument vector class instance.

    Args:
        arg     (str)       : [IN] Positional argument token.
        arginf  (ArgsInfo)  : [IN] Parsed result of docstring.
        argvec  (ArgVector) : [IN] Parsed user input.
        n_args  (int)       : [IN] Number of remaining argument tokens.
        is_mul  (bool)      : [IN] Whether currently processing multiple positional arguments.

    Returns:
        n_args (int) : Updated number of remaining argument tokens.
        is_mul (bool): Updated flag whether currently processing multiple positional arguments.
    """
    # Raise an error if there are too many positional arguments.
    if n_args == 0:
        raise YadOptError.TooManyArgument(extra_args=arg)

    # Get argument name.
    entry: PosEntry = arginf.posargs[len(arginf.posargs) - n_args]

    # If the target positional argument is a multiple argument, add the argument value to
    # the list of the corresponding argument name in the output variable. In this case,
    # do not decrease the number of remaining argument tokens.
    if entry.is_mult:
        if entry.name not in argvec.posargs:
            argvec.posargs[entry.name] = []
        argvec.posargs[entry.name].append(arg)
        is_mul = True

    # Otherwise, add the argument name and value to the output variable
    # and decrease the number of remaining argument tokens.
    else:
        argvec.posargs[entry.name] = arg
        n_args -= 1

    return (n_args, is_mul)


def parse_argvec_opt(arg: str, argvec: ArgVector, argv_copy: Deque[str], opt_entries: dict[str, OptEntry]) -> None:
    """
    Parse an optional argument token and update the argument vector class instance.

    Args:
        arg         (str)                : [IN] Optional argument token.
        argvec      (ArgVector)          : [IN] Parsed user input.
        argv_copy   (Deque[str])         : [IN] Standardized argument vector. This variable is modified in-place.
        opt_entries (dict[str, OptEntry]): [IN] Map from option name to option entry.
    """
    # Split the option token into option name and value.
    (opt_key, opt_val) = split_option_token_with_equal(arg)

    # Get the corresponding option entry.
    opt_entry: OptEntry = opt_entries[opt_key]

    # Case 1.1: Option with value.
    if opt_entry.val_name is not None:

        # If there is no remaining token, raise an error.
        if opt_val is None and not argv_copy:
            raise YadOptError.NoOptionValue(opt_name=arg)

        # Get the option value.
        opt_value: str = argv_copy.popleft() if opt_val is None else opt_val

        # Treat another known option token as a missing value, but allow arbitrary
        # hyphen-prefixed strings such as "-foo" and "-report.txt" as valid values.
        if opt_val is None and is_option_token(opt_value, opt_entries):
            raise YadOptError.NoOptionValue(opt_name=arg)

        # Add the option name and value to the output variable.
        argvec.optargs[opt_entry.name] = opt_value

    # Case 1.2: Option without value.
    else:

        # Add the option name and "True" to the output variable.
        argvec.optargs[opt_entry.name] = True


def is_option_token(token: str, opt_entries: dict[str, OptEntry]) -> bool:
    """
    Checks whether a given token is an option token.

    Args:
        token       (str)                : [IN] Token to be checked.
        opt_entries (dict[str, OptEntry]): [IN] Map from option name to option entry.

    Returns:
        (bool): True if the given token is an option token, False otherwise.
    """
    (opt_key, _) = split_option_token_with_equal(token)
    return opt_key in opt_entries


def split_option_token_with_equal(arg: str) -> tuple[str, str | None]:
    """
    Split an option token with an equal sign into option name and value.

    Args:
        arg (str): [IN] Option token to be split.

    Returns:
        (tuple[str, str | None]): Option name and value.

    Examples:
        >>> split_option_token_with_equal("--optimizer=adam")
        ('--optimizer', 'adam')
        >>> split_option_token_with_equal("--equation='x=3'")
        ('--equation', "'x=3'")
    """
    # Split the option token into option name and value using regular expression.
    match: re.Match | None = re.fullmatch(r"""^(--?[^='"]+)(=.*)?""", arg)

    # If the given token does not match the regular expression, return the original token and None.
    if match is None:
        return (arg, None)

    # Returns the matched option name and value.
    return (match.group(1), None if match.group(2) is None else match.group(2)[1:])


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
