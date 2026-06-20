"""
yadopt.typehint - assign types based on type hinting string.
"""
from __future__ import annotations

# Import standard libraries.
import ast
import dataclasses

# For type hinting.
from typing          import Any
from collections.abc import Callable

# Import custom modules.
from .default import DefaultResolvedArgVec
from .declaration import ParsedDecls, PosArgDecl, OptArgDecl
from .dtypes import Path
from .errors import YadOptError
from .description import ParsedDesc
from .posarg import PosSpec
from .optarg import OptSpec

# Declare published functions and variables.
__all__ = ["TypedArgVec", "TypeAssigner", "DTYPE_HINTS"]


@dataclasses.dataclass
class TypedArgVec:
    """
    Argument vector with typed values.
    """
    pos_args: dict[str, Any]
    opt_args: dict[str, Any]

    def validate(self, pos_args: list[PosArgDecl], opt_args: list[OptArgDecl]) -> None:
        """
        Run extra validation checks. This function is called only when running tests.
        This is a post-condition assertion in the context of DbC methodology.
        """
        # All positional arguments appear in the pos_args.
        for pos_arg_decl in pos_args:
            name = pos_arg_decl.spec.name
            assert name in self.pos_args, f"Positional argument '{name}' is missing in pos_args."

        # All option arguments appear in the optargs.
        for opt_arg_decl in opt_args:
            n1 = opt_arg_decl.spec.name
            n2 = opt_arg_decl.spec.name_alt
            assert n1 in self.opt_args or n2 in self.opt_args, f"Optional argument '{n1}' is missing in opt_args."


class TypeAssigner:
    """
    Class for assigning types to the parsed argument vector.
    """
    def __init__(self, argvec: DefaultResolvedArgVec, parsed_decls: ParsedDecls, verbose: bool) -> None:
        """
        Constructor.

        Args:
            argvec      (DefaultResolvedArgVec): [IN] Argument vector with default values filled in.
            parsed_decls (ParsedDecls)         : [IN] Parsed declaration information.
        """
        self.argvec     : DefaultResolvedArgVec = argvec
        self.parsed_decls: ParsedDecls           = parsed_decls
        self.verbose     : bool                   = verbose

    def assign_types(self) -> TypedArgVec:
        """
        Assign types to the argument vector.

        Returns:
            (TypedArgVec): Argument vector with typed values.
        """
        return TypedArgVec(
            pos_args = self.set_typed_value(self.argvec.pos_args, self.parsed_decls.posargs, self.verbose),
            opt_args = self.set_typed_value(self.argvec.opt_args, self.parsed_decls.optargs, self.verbose),
        )

    @staticmethod
    def set_typed_value(src_dict: dict, arg_decls: list[PosArgDecl] | list[OptArgDecl], verbose: bool) -> dict:
        """
        Get typed value.
        """
        if verbose:
            print("TypeAssigner.set_typed_value():")

        # Make a copy of the source dictionary to avoid modifying the original.
        dst_dict: dict = src_dict.copy()

        for arg_decl in arg_decls:

            if verbose:
                print(" |- arg_decl =", arg_decl)

            #
            spec: PosSpec | OptSpec = arg_decl.spec
            desc: ParsedDesc        = arg_decl.desc

            # Do nothing if the entry is not in the value dictionary.
            if spec.name not in dst_dict:
                continue

            # Case 1: Option without value.
            if isinstance(spec, OptSpec) and (spec.val_name is None):
                dst_dict[spec.name] = strtobool(dst_dict[spec.name])
                continue

            # Case 2: None value (occurs by default value resolver).
            if dst_dict[spec.name] is None:
                continue

            # Case 3: If the value looks like None, set real None.
            if dst_dict[spec.name] == "None":
                dst_dict[spec.name] = None
                continue

            # Get type function.
            func_dtype: Callable = TypeAssigner.type_func(spec.name,
                                                          spec.val_name if isinstance(spec, OptSpec) else None,
                                                          desc.type_dh)

            # If the target value is list of string, then apply the type function to the list contents.
            if isinstance(dst_dict[spec.name], list):
                dst_dict[spec.name] = [func_dtype(v) for v in dst_dict[spec.name]]

            # Else, normally apply type function to the value.
            else:
                dst_dict[spec.name] = func_dtype(dst_dict[spec.name])

        return dst_dict

    @staticmethod
    def type_func(name: str, val_name: str | None, type_dsc: str | None) -> Callable:
        """
        Determine data type of arguments/options.

        Args:
            name     (str)       : Argument/option name.
            val_name (str | None): Option value name.
            type_dsc (str | None): Type name written in description head.

        Returns:
            (Callable): Appropriate type function.
        """
        # Case 1: description head.
        if type_dsc is not None:

            # Raise an error if type name is unknown.
            if type_dsc.lower() not in DTYPE_HINTS:
                raise YadOptError.InvalidTypeName(type_name=type_dsc)

            return DTYPE_HINTS[type_dsc.lower()]

        # Case 2: value name suffix.
        if val_name is not None:

            # Get the type name candidate from the value name.
            val_type_name: str = val_name.rsplit("_", maxsplit=1)[-1]

            # Returns the type if the type name is valid.
            if val_type_name.lower() in DTYPE_HINTS:
                return DTYPE_HINTS[val_type_name.lower()]

        # Case 3: argument/option name suffix.
        if name:

            # Returns the type if the name ends with the type name.
            for key, dtype in DTYPE_HINTS.items():
                if name.lower().endswith(key):
                    return dtype

        # Otherwise, returns default type.
        return str


def auto_type(value: str) -> Any:
    """
    Automatically determine the data type using.

    Args:
        value (str): [IN] String expression of value.

    Returns:
        Any: Parsed value.

    Notes:
        Path values are not inferred automatically because there is no reliable way to distinguish
        a plain string from a file system path.
    """
    try:
        return ast.literal_eval(value)
    except (SyntaxError, TypeError, ValueError):
        return str(value)


def strtobool(s: str | None) -> bool:
    """
    Convert the given string to bool instance. The function `bool(...)` is not suitable
    for this purpose, because `bool("False")` returns `True`.

    Args:
        s (str | None): [IN] Input string.

    Returns:
        (bool | None): Corresponding boolean value.

    Examples:
        >>> strtobool("True")
        True
        >>> strtobool("False")
        False
        >>> strtobool(None)
        False
    """
    if s is None:
        return False

    if s.lower() in {"t", "true", "y", "yes", "on", "1"}:
        return True
    if s.lower() in {"f", "false", "n", "no", "off", "0"}:
        return False

    raise YadOptError.InvalidBoolValue(value=s)


def strtostr(s: str) -> str:
    """
    Convert string expression to string.

    Args:
        s (str): [IN] Input string.

    Returns:
        (str): Corresponding string value.

    Examples:
        >>> strtostr("this is a pen")
        'this is a pen'
        >>> strtostr("'this is a pen'")
        'this is a pen'
        >>> strtostr("'''this is a pen'''")
        'this is a pen'
        >>> strtostr("'1'")
        '1'
        >>> strtostr("'1.0'")
        '1.0'
    """
    try:
        return str(ast.literal_eval(s))
    except (SyntaxError, ValueError):
        return str(s)


# Define a map from data type string to data type.
DTYPE_HINTS: dict[str, Callable] = {
    # Booleans.
    "bool": strtobool, "boolean": strtobool,
    # Integers.
    "int": int, "integer": int,
    # Floating numbers.
    "flt": float, "float": float,
    # Strings.
    "str": strtostr, "string": strtostr,
    # Path.
    "path": Path,
    # Auto type.
    "auto": auto_type,
    # None.
    "nonetype": lambda x: None,
}


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
