"""
yadopt.argvec - argument vector parser.
"""
from __future__ import annotations

# Import standard libraries.
import dataclasses
import re

# For type hinting.
from typing import Generator

# Import custom modules.
from .dtypes      import Deque
from .declaration import ParsedDecls, OptArgDecl
from .optarg      import OptSpec
from .posarg      import PosSpec
from .errors      import YadOptError, get_candidate_message
from .utils       import is_python_value

# Declare published functions and variables.
__all__ = ["ParsedArgVec", "ArgVecParser"]


@dataclasses.dataclass(frozen=True)
class ParsedArgVec:
    """
    Parsed argument vector.
    """
    posargs: dict[str, str | list[str]]
    optargs: dict[str, str]

    def __str__(self) -> str:
        text  = self.__class__.__name__ + ":\n"
        text += " |- posargs = " + str(self.posargs) + "\n"
        text += " |- optargs = " + str(self.optargs)
        return text.strip()

    def validate(self) -> None:
        """
        Run extra validation checks. This function is called only when running tests.
        This is a post-condition assertion in the context of DbC methodology.
        """
        # All variables are not typed yet, that is, all values are strings or lists of strings.
        for value in self.posargs.values():
            assert isinstance(value, (list, str))
            if isinstance(value, list) and len(value) > 0:
                assert all(isinstance(item, str) for item in value)
        for value in self.optargs.values():
            assert isinstance(value, str)


class ArgVecParser:
    """
    Argument vector parser.
    """
    def __init__(self, argv: list[str], parsed_decls: ParsedDecls, verbose: bool) -> None:
        """
        Constructor.

        Args:
            argv         (list[str])  : [IN] Argument vector.
            parsed_decls (ParsedDecls): [IN] Parsed result of declaration line in docstring.
            verbose      (bool)       : [IN] Displays verbose messages that are useful for debugging.
        """
        self.argv   : Deque[str]  = Deque(argv)
        self.decls  : ParsedDecls = parsed_decls
        self.verbose: bool        = verbose

        # Generate a list of positional argument specifications in the order of declaration.
        self.pos_specs: list[PosSpec] = [entry.spec for entry in self.decls.posargs]

        # Generate a map from option name (with "-" or "--") to option specification.
        self.opt_specs: dict[str, OptSpec] = dict(self.get_opt_specs(self.decls.optargs))

        # Parse results.
        self.pos_args: dict[str, str | list[str]] = {}
        self.opt_args: dict[str, str]             = {}

    def parse(self) -> ParsedArgVec:
        """
        Parse a given argument vector and return an ArgVector instance.

        Returns:
            (ArgVector): Parsed argument vector.
        """
        # Initialize the output variables.
        self.pos_args.clear()
        self.opt_args.clear()

        # Initialize the state variables.
        n_args  : int  = len(self.decls.posargs) # Number of remaining positional argument tokens.
        is_mul  : bool = False                   # Whether currently processing multiple positional arguments.
        acpt_opt: bool = True                    # Whether option tokens are acceptable.

        if self.verbose:
            print("ArgVecParser.parse():")

        while self.argv:

            # Get the next token.
            arg: str = self.argv.popleft()

            if self.verbose:
                print(f" |- arg = {arg}, n_args = {n_args}, is_mul = {is_mul}, acpt_opt = {acpt_opt}")

            # Case 1: Double delimiter makes the following tokens be treated as argument tokens.
            if arg == "--":
                acpt_opt = False

            # Case 2: Multiple short options.
            elif acpt_opt and arg.startswith("-") and self.is_multiple_short_option(arg):
                for char in arg[1:]:
                    self.process_opt_arg(f"-{char}")

            # Case 3: Long or short option.
            elif acpt_opt and arg.startswith("-") and self.is_option_token(arg):
                self.process_opt_arg(arg)

            # Case 3: Unknown option token.
            elif acpt_opt and arg.startswith("-") and not is_python_value(arg):

                # Get the candidate option names.
                cands: list[str] = list(self.opt_specs.keys())

                raise YadOptError.UnknownOption(opt_name=arg, candidate=get_candidate_message(arg, cands))

            # Case 4: Argument token.
            else:
                (n_args, is_mul) = self.process_pos_arg(arg, n_args, is_mul)

        # Raise an error if there are missing positional arguments.
        if (n_args > 0) and not is_mul:

            # Get the names of missing arguments.
            arg_names_missing: list[str] = [entry.name for entry in self.pos_specs[-n_args:]]

            # Flatten if the number of missing arguments is one.
            arg_names_missing_str: str = arg_names_missing[0] if (len(arg_names_missing) == 1) else str(arg_names_missing)

            raise YadOptError.MissingArgument(missing_args=arg_names_missing_str)

        return ParsedArgVec(posargs=self.pos_args, optargs=self.opt_args)

    def process_pos_arg(self, arg: str, n_args: int, is_mul: bool) -> tuple[int, bool]:
        """
        Process a positional argument token and update the argument vector class instance.

        Args:
            arg    (str) : [IN] Positional argument token.
            n_args (int) : [IN] Number of remaining positional argument tokens.
            is_mul (bool): [IN] Whether currently processing multiple positional arguments.

        Returns:
            n_args (int) : Updated number of remaining positional argument tokens.
            is_mul (bool): Updated flag whether currently processing multiple positional arguments.
        """
        # Raise an error if there are too many positional arguments.
        if n_args == 0:
            raise YadOptError.TooManyArgument(extra_args=arg)

        # Get argument name.
        pos_spec: PosSpec = self.pos_specs[len(self.pos_specs) - n_args]

        # Case 1: Multiple positional arguments.
        if pos_spec.is_mult:

            # Add the argument value to the list of the corresponding argument name.
            if isinstance(data := self.pos_args.setdefault(pos_spec.name, []), list):
                data.append(arg)

            # In this case, do not decrease the number of remaining argument tokens.
            return (n_args, True)

        # Case 2: Single positional argument.
        self.pos_args[pos_spec.name] = arg
        return (n_args - 1, is_mul)

    def process_opt_arg(self, arg: str):
        """
        Process an optional argument token and update the argument vector class instance.

        Args:
            arg (str): [IN] Optional argument token.
        """
        # Split the option token into option name and value.
        (opt_key, opt_val) = self.split_option_token_with_equal(arg)

        # Get the corresponding option entry.
        opt_spec: OptSpec = self.opt_specs[opt_key]

        # Case 1: Option with value.
        if opt_spec.val_name is not None:

            # If there is no remaining token, raise an error.
            if opt_val is None and not self.argv:
                raise YadOptError.NoOptionValue(opt_name=arg)

            # Update the option value with the next token only when the option value is None.
            updated_opt_val: str = self.argv.popleft() if opt_val is None else opt_val

            # Check the validity of the option value when the option value starts with a hyphen.
            # The token "--opt=-v" is allowed, but the token "--opt -v" is not allowed if
            # "-v" is an existing option name.
            if opt_val is None and self.is_option_token(updated_opt_val):
                raise YadOptError.NoOptionValue(opt_name=arg)

            # Add the option name and value to the output variable.
            self.opt_args[opt_spec.name] = updated_opt_val

        # Case 2: Option without value.
        else:

            # Add the option name and assign a string "True" as a value.
            self.opt_args[opt_spec.name] = "True"

    def is_option_token(self, token: str) -> bool:
        """
        Checks whether a given token is an option token.

        Args:
            token (str): [IN] Token to be checked.

        Returns:
            (bool): True if the given token is an option token, False otherwise.
        """
        (opt_key, _) = self.split_option_token_with_equal(token)
        return opt_key in self.opt_specs

    def is_multiple_short_option(self, token: str) -> bool:
        """
        Checks whether a given token is a multiple short option.

        Args:
            token (str): [IN] Token to be checked.

        Returns:
            (bool): True if the given token is a multiple short option, False otherwise.
        """
        # Split the option token into option name and value.
        (opt_key, _) = self.split_option_token_with_equal(token)

        # Check if the given token is a valid short option token.
        if opt_key.startswith("--") or (not opt_key.startswith("-")) or (len(opt_key) <= 2):
            return False

        # Check if all characters after the first hyphen are valid short option names.
        for char in opt_key[1:]:
            if f"-{char}" not in self.opt_specs:
                return False

        return True

    @staticmethod
    def get_opt_specs(optargs: list[OptArgDecl]) -> Generator[tuple[str, OptSpec], None, None]:
        """
        Returns a map from option name (with "-" or "--") to option specification.
        """
        for opt_arg_decl in optargs:

            spec: OptSpec = opt_arg_decl.spec

            # Case 1: Short option only.
            if spec.is_short:
                yield (f"-{spec.name}", spec)

            # Case 2: Long option only or both long and short options.
            else:
                yield (f"--{spec.name}", spec)

                if opt_arg_decl.spec.name_alt is not None:
                    yield(f"-{spec.name_alt}", spec)

    @staticmethod
    def split_option_token_with_equal(arg: str) -> tuple[str, str | None]:
        """
        Split an option token with an equal sign into option name and value.

        Args:
            arg (str): [IN] Option token to be split.

        Returns:
            (tuple[str, str | None]): Option name and value.

        Examples:
            >>> ArgVecParser.split_option_token_with_equal("-o=adam")
            ('-o', 'adam')
            >>> ArgVecParser.split_option_token_with_equal("--optimizer=adam")
            ('--optimizer', 'adam')
            >>> ArgVecParser.split_option_token_with_equal("--equation='x=3'")
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
