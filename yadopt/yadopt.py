"""
Yet another docopt, a human-friendly command line arguments parser.
"""
from __future__ import annotations

# Import standard libraries.
import collections
import dataclasses
import functools
import inspect
import sys
import textwrap
import typing

# For type hinting.
from collections.abc import Callable
from typing          import Any

# Import custom modules.
from .argvec      import ArgVecParser, ParsedArgVec
from .datacls     import dataclass_to_help_message
from .datamodel   import YadOptArgs, make_yadoptargs_data
from .declaration import DeclarationContentsParser, ParsedDecls
from .default     import DefaultValueResolver, DefaultResolvedArgVec
from .dtypes      import Path
from .errors      import YadOptError
from .helpmsg     import has_help_option_in_argv, print_help_message_and_exit
from .section     import DeclarationContents, SectionLineSplitter
from .typehint    import TypeAssigner, TypedArgVec

# Declare published functions and variables.
__all__ = ["parse", "wrap", "to_dict", "to_namedtuple", "get_group", "YadOptArgs"]


# Type definition for yadopt.parse function.
T = typing.TypeVar("T")
@typing.overload
def parse(source: str | None, argv: list[str] | None = None, exit_on_help: bool = True, verbose: bool = False) -> YadOptArgs: ...
@typing.overload
def parse(source: type[T], argv: list[str] | None = None, exit_on_help: bool = True, verbose: bool = False) -> T: ...

def parse(source: str | type[T] | None = None, argv: list[str] | None = None,
          exit_on_help: bool = True, verbose: bool = False) -> YadOptArgs | T:
    """
    Parse a given docstring and an argument vector, and return a YadoptArgs instance.

    Args:
        source       (str | type[T] | None): [IN] Help message string or a dataclass type to be parsed.
        argv         (list[str] | None)    : [IN] Argument vector.
        exit_on_help (bool)                : [IN] If True, prints the help message and exits when "--help" is specified.
        verbose      (bool)                : [IN] Displays verbose messages that are useful for debugging.

    Returns:
        (YadOptArgs): Parsed command line arguments.

    Notes:
        This function relies heavily on the Design by Contract (DbC) paradigm.
    """
    # If the "source" is None, get the docstring of the caller module.
    if source is None:

        # Get the caller module by traversing the call stack.
        module = inspect.currentframe()
        while module is not None and Path(module.f_code.co_filename).parent == Path(__file__).parent:
            module = module.f_back

        # Get the docstring of the caller module.
        source = getattr(module, "f_locals", {}).get("__doc__", "")

    # Validate the type of the given "source" data.
    if not (isinstance(source, str) or dataclasses.is_dataclass(source)):
        raise YadOptError.InvalidSourceType(source_type=source.__class__.__name__)

    # Get the docstring from the given source.
    docstr: str = dataclass_to_help_message(source) if dataclasses.is_dataclass(source) else source

    # Use sys.argv if the input vector is None.
    if argv is None:
        argv = sys.argv[1:]

    # Dedent the given docstring.
    docstr = textwrap.dedent(docstr)

    # Parse the docstring and get declaration lines in target sections.
    # Note: Automatic minimum validation will be performed for the "decl_conts" (in the context of DbC).
    decl_conts: DeclarationContents = SectionLineSplitter(docstr, verbose).parse()

    if verbose:

        print(decl_conts)

        # Run extra validation checks if "verbose" is True (in the context of DbC).
        decl_conts.validate(len_docstr=len(docstr))

    # Parse the declaration lines and get parsed declaration entries.
    # Note: Automatic minimum validation will be performed for the "parsed_decl" (in the context of DbC).
    parsed_decls: ParsedDecls = DeclarationContentsParser(docstr, decl_conts, verbose).parse()

    if verbose:

        print(parsed_decls)

        # Run extra validation checks if "verbose" is True (in the context of DbC).
        parsed_decls.validate()

    # Print help message and exit if --help is specified, or if the short option of help is specified.
    if has_help_option_in_argv(argv, parsed_decls.optargs):
        print_help_message_and_exit(docstr.strip(), parsed_decls, exit_on_help=exit_on_help)

    # Parse the given command line arguments.
    argvec: ParsedArgVec = ArgVecParser(argv, parsed_decls, verbose).parse()

    if verbose:

        print("argvec (before assigning types) =", argvec)

        # Run extra validation checks if "verbose" is True (in the context of DbC).
        argvec.validate()

    # Resolve default values of options in the argument vector based on the option declarations.
    argvec_default_resolved: DefaultResolvedArgVec = DefaultValueResolver(argvec, parsed_decls.optargs, verbose).resolve()

    if verbose:

        print("argvec_default_resolved =", argvec_default_resolved)

        # Run extra validation checks if "verbose" is True (in the context of DbC).
        argvec_default_resolved.validate(pos_args=parsed_decls.posargs, opt_args=parsed_decls.optargs)

    # Apply type hints. This function also fill default values.
    typed_argvec: TypedArgVec = TypeAssigner(argvec_default_resolved, parsed_decls, verbose).assign_types()

    if verbose:

        print("typed_argvec =", typed_argvec)

        # Run extra validation checks if "verbose" is True (in the context of DbC).
        typed_argvec.validate(pos_args=parsed_decls.posargs, opt_args=parsed_decls.optargs)

    # Get group information.
    groups: dict[str, list[str]] = {}
    for pos_arg_decl in parsed_decls.posargs:
        groups.setdefault(pos_arg_decl.group, []).append(pos_arg_decl.spec.name)
    for opt_arg_decl in parsed_decls.optargs:
        groups.setdefault(opt_arg_decl.group, []).append(opt_arg_decl.spec.name)
        if opt_arg_decl.spec.name_alt is not None:
            groups.setdefault(opt_arg_decl.group, []).append(opt_arg_decl.spec.name_alt)

    # Determine the base class for the dynamically created YadOptArgs class.
    base_cls: type = source if dataclasses.is_dataclass(source) else YadOptArgs

    # Returns YadOptArgs instance.
    return make_yadoptargs_data(typed_argvec.pos_args | typed_argvec.opt_args, groups, base_cls)


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
    if dataclasses.is_dataclass(args):
        return dataclasses.asdict(args)
    raise NotImplementedError


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
    if not isinstance(args, YadOptArgs):
        raise YadOptError.CannotGetGroup(cls_name=args.__class__.__name__)

    # Get the list of keys in the group.
    set_keys: list[str] = getattr(args, "_groups_").get(group, [])

    # Get the filtered dictionary by the group.
    data_group: dict = {key: value for key, value in to_dict(args).items() if key in set_keys}

    return make_yadoptargs_data(data_group, groups={"group": set_keys}, base_cls=YadOptArgs)


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
