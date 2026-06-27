"""
Yet another docopt, a human-friendly command line arguments parser.
"""

# Declare published functions and variables.
__all__ = ["parse", "wrap", "to_dict", "to_namedtuple", "get_group"]

# Import standard libraries.
import collections
import copy
import functools
import os
import sys
import textwrap

# For type hinting.
from collections.abc import Callable
from typing          import Any

# Import custom modules.
from .analysis import check_arginf
from .argvec   import ArgVector, parse_argvec
from .color    import colorize_help_message
from .dtypes   import PosEntry, OptEntry, ArgsInfo
from .posopt   import parse_def_line
from .errors   import YadOptError
from .section  import get_section_lines
from .hint     import type_hint


#===================================================================================================
# Public classes and functions
#===================================================================================================

class YadOptArgs:
    """
    Command line arguments parsed by YadOpt.
    """
    def __init__(self, argvec: ArgVector | None = None, arginf: ArgsInfo | None = None,
                 groups: dict[str, list] | None = None) -> None:
        """
        Constructor of YadOptArgs.

        Args:
            argvec (ArgVector | None)      : [IN] Parsed argument vector.
            arginf (ArgsInfo | None)       : [IN] Parsed docstring information.
            groups (dict[str, list] | None): [IN] Group information.
        """
        # Set the value of parsed argument vector as attributes.
        if argvec is not None:
            for name, value in (argvec.posargs | argvec.optargs).items():
                setattr(self, name, value)

        # Add group info.
        if groups is None and arginf is not None:

            # Reset the groups.
            groups = {}

            for entry in arginf.posargs + arginf.optargs:
                groups.setdefault(entry.group, []).append(entry.name)

        # Set the group info as an attribute.
        setattr(self, "_groups_", {} if groups is None else groups)

    def __eq__(self, other: object) -> bool:
        """
        Returns True if equivalent.
        """
        if isinstance(other, self.__class__):
            return self._normal_dict_() == other._normal_dict_()
        return False

    def __len__(self) -> int:
        """
        Returns the number of items.
        """
        return len(self._normal_dict_())

    def __or__(self, other) -> object:
        """
        OR operation.
        """
        # The operand must be an instance of YadOptArgs.
        if not isinstance(other, YadOptArgs):
            raise YadOptError.CannotMerge(cls_name=other.__class__.__name__)

        # Create a deep copy of the left-hand side.
        args_copy = copy.deepcopy(self)

        # Merge normal argument values while keeping internal bookkeeping stable.
        for key, value in other.__dict__.items():
            if not (key.startswith("_") and key.endswith("_")):
                args_copy.__dict__[key] = copy.deepcopy(value)

        # Merge group information without discarding the left-hand side.
        groups_merged: dict[str, list] = copy.deepcopy(getattr(self, "_groups_", {}))
        for group_name, members in getattr(other, "_groups_", {}).items():
            groups_merged[group_name] = list(set(groups_merged.get(group_name, []) + members))
        args_copy.__dict__["_groups_"] = groups_merged

        return args_copy

    def __repr__(self) -> str:
        """
        Representation of this class.
        """
        return str(self._named_tuple_())

    def __str__(self) -> str:
        """
        String expression of this class.
        """
        return self.__repr__()

    def _normal_dict_(self) -> dict[str, Any]:
        """
        Returns "normal" dictionary that contains keys not starting with the underscore.
        """
        return {key:value for key, value in self.__dict__.items() if not (key.startswith("_") and key.endswith("_"))}

    def _named_tuple_(self) -> tuple[Any, ...]:
        """
        Returns a named tuple expression of this class instance.
        """
        dict_data: dict[str, Any] = self._normal_dict_()
        return collections.namedtuple("YadOptArgs", list(dict_data.keys()), rename=True)(**dict_data)


def parse(docstr: str, argv: list[str] | None = None, verbose: bool = False) -> YadOptArgs:
    """
    Parse a given docstring and an argument vector, and return a YadoptArgs instance.

    Args:
        docstr  (str)             : [IN] Docstring to be parsed.
        argv    (list[str] | None): [IN] Argument vector.
        verbose (bool)            : [IN] Displays verbose messages that are useful for debugging.

    Returns:
        (YadOptArgs): Parsed command line arguments.
    """
    # Use sys.argv if the input vector is None.
    explicit_argv: bool = argv is not None
    if argv is None:
        argv = sys.argv

    # Dedent the given docstring.
    docstr = textwrap.dedent(docstr)

    # Initialize the parsed docstring data structure.
    arginf: ArgsInfo = ArgsInfo(posargs=[], optargs=[], docstr=docstr)

    # Parse the docstring and get declaration entries.
    for section_name, span_decl in get_section_lines(docstr, verbose):

        # Parse one declaration line.
        entry: PosEntry | OptEntry = parse_def_line(docstr, span_decl, section_name, verbose)

        # Append the parsed entry to the corresponding list in arginf.
        if isinstance(entry, PosEntry):
            arginf.posargs.append(entry)
        else:
            arginf.optargs.append(entry)

    # DEBUG: Print the parsed docstring if verbose is True.
    if verbose:
        print(arginf)

    # Check the parsed docstring for consistency and raise an error if invalid.
    check_arginf(arginf, verbose)

    # Normalize explicitly supplied argv for option-only CLIs so that both
    # ["prog", "--flag"] and ["--flag"] are accepted. Positional-argument CLIs
    # still require the conventional program name element to avoid ambiguity.
    if explicit_argv and argv and (not arginf.posargs) and argv[0].startswith("-"):
        argv = ["<argv>", *argv]

    # Print help message and exit if --help is specified, and exit.
    # You can stop exiting the software by catching the SystemExit error.
    help_alt: str | None = next((entry.name_alt for entry in arginf.optargs if entry.name == "help"), None)
    if ("--help" in argv) or (help_alt is not None and ("-" + help_alt) in argv):
        print(colorize_help_message(docstr.strip()))
        sys.exit(os.EX_OK)

    # Parse the given command line arguments.
    argvec: ArgVector = parse_argvec(argv, arginf, verbose)

    # DEBUG: Print the parsed argument vector if verbose is True.
    if verbose:
        print("argvec (before assigning types) =", argvec)

    # Fill default values of options if not specified in the input vector.
    for opt_entry in arginf.optargs:
        if opt_entry.name not in argvec.optargs:
            argvec.optargs[opt_entry.name] = opt_entry.default

    # Apply type hints. This function also fill default values.
    type_hint(argvec, arginf, verbose)

    # DEBUG: Print the parsed argument vector if verbose is True.
    if verbose:
        print("argvec =", argvec)

    # Create data instance.
    args: YadOptArgs = YadOptArgs(argvec=argvec, arginf=arginf)

    # Returns YadOptArgs instance.
    return args


def wrap(*pargs: Any, **kwargs: Any) -> Callable:
    """
    Wrapper function for the command line parsing.

    Args:
        pargs  (Any): [IN] Positional arguments for 'yadopt.parse' function.
        kwargs (Any): [IN] Keyword arguments for 'yadopt.parse' function.

    Returns:
        (Callable): Decorator function.

    Note:
        This function actually returns a function because this function
        is designed as a decorator function with argument (= docstr).
    """
    def decorate(func: Callable) -> Callable:
        """
        Decorate the given function.
        """
        @functools.wraps(func)
        def wrapper_func(*pargs_func: Any, **kwargs_func: Any) -> Any:
            args: YadOptArgs = parse(*pargs, **kwargs)
            return func(args, *pargs_func, **kwargs_func)

        return wrapper_func

    return decorate


def to_dict(args: YadOptArgs) -> dict[str, Any]:
    """
    Convert YadOptArgs instance to a dictionary.

    Args:
        args (YadOptArgs): [IN] Parsed command line arguments.

    Returns:
        (dict[str, Any]): Dictionary of the given parsed arguments.
    """
    return args._normal_dict_()


def to_namedtuple(args: YadOptArgs) -> tuple[Any, ...]:
    """
    Convert YadOptArgs instance to a named tuple.

    Args:
        args (YadOptArgs): [IN] Parsed command line arguments.

    Returns:
        (tuple[Any, ...]): Namedtuple of the given parsed arguments.
    """
    args_d: dict = to_dict(args)
    fields: list = list(args_d.keys())
    return collections.namedtuple("YadOptArgsNt", fields, rename=True)(**args_d)


def get_group(args: YadOptArgs, group: str) -> YadOptArgs:
    """
    Returns the parsed result of the specified section.

    Args:
        args  (YadOptArgs): [IN] Parsed command line arguments.
        group (str)       : [IN] Name of group to extract.

    Returns:
        (YadOptArgs): Parsed command line arguments of the group.
    """
    # Get the list of keys in the group.
    list_keys: list[str] = getattr(args, "_groups_").get(group, [])

    # Create a copy of the given YadOptArgs instance.
    data: YadOptArgs = YadOptArgs(groups={group: list_keys})

    # Append group members.
    for key in to_dict(args).keys():
        if key in list_keys:
            setattr(data, key, getattr(args, key))

    return data


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
