"""
yadopt.optarg - parser for optional argument declaration in docstring.
"""
from __future__ import annotations

# Import standard libraries.
import enum
import dataclasses
import re

# For type hinting.
from typing import TypeAlias

# Import custom modules.
from .basearg import BaseArgParser
from .dtypes  import Span
from .errors  import YadOptError, get_target_and_marker

# Declare published functions and variables.
__all__ = ["OptSpec", "OptArgParser"]


@dataclasses.dataclass(frozen=True)
class OptSpec:
    """
    Parsed result of optional argument definition in docstring.
    """
    name    : str         # Option name.
    name_alt: str | None  # Alternative option name.
    val_name: str | None  # Name of option value (used for type hinting).
    is_short: bool        # True if this option is a short option only.

    def __post_init__(self) -> None:
        """
        Run minimum validation checks.
        This is a post-condition assertion in the context of DbC methodology.
        """
        # The option "--help" should be an option without a value.
        if self.name == "help" and self.val_name is not None:
            raise YadOptError.InvalidHelpOption()

    def validate(self) -> None:
        """
        Run extra validation checks. This function is called only when running tests.
        This is a post-condition assertion in the context of DbC methodology.
        """
        # Check the option names.
        assert re.match(r"[A-Za-z_][A-Za-z0-9_\.-]*", self.name), f"Invalid optional argument name: {self.name}"
        if self.name_alt is not None:
            assert re.match(r"[A-Za-z_][A-Za-z0-9_\.-]*", self.name_alt), f"Invalid optional argument name: {self.name}"

        # The "is_short" flag should be True if and only if the "name_alt" is None.
        assert (not self.is_short) or (self.name_alt is None), "Short option cannot have an alternative name."


class OptArgParser(BaseArgParser):
    """
    Parser for the declaration line of optional argument in the docstring.
    """
    class TokenType(enum.IntEnum):
        """
        Enumeration of token types in the option declaration line.
        """
        SHORT = enum.auto()
        LONG  = enum.auto()
        ARG   = enum.auto()
        COMMA = enum.auto()
        OTHER = enum.auto()

    # Regular expression pattern to split the option declaration line into tokens.
    pattern_split = re.compile(r"\s+|=|(,)")

    def __init__(self, docstr: str, span: Span, verbose: bool) -> None:
        """
        Constructor.

        Args:
            docstr  (str) : [IN] Original docstring to be parsed.
            span    (Span): [IN] Span of the description part in the original docstring
            verbose (bool): [IN] Displays verbose messages that are useful for debugging.
        """
        self.docstr  = docstr
        self.span    = span
        self.verbose = verbose

    def parse(self) -> OptSpec:
        """
        Parse the declaration line as an option line and return the parsed result as OptEntry.

        Returns:
            (OptEntry): Parsed result.
        """
        # Type alias for readability.
        TokenType: TypeAlias = OptArgParser.TokenType

        # Get the target string.
        target: str = self.docstr[self.span[0]:self.span[1]]

        # Tokenize the option specification part of the declaration line.
        tokens: tuple[str, ...] = tuple(token for token in self.pattern_split.split(target) if token)

        # Convert the tokens to token types.
        token_types: tuple[TokenType, ...] = tuple(self.to_type(token) for token in tokens)

        if self.verbose:
            print("Parsing option declaration line:")
            print("  |- original line = '" + target + "'")
            print("  |- tokens =", tokens)
            print("  |- token types =", token_types)

        # Case 1: Short flag only.
        if token_types in ((TokenType.SHORT,), (TokenType.SHORT, TokenType.ARG)):
            return OptSpec(
                name     = tokens[0][1:],
                name_alt = None,
                val_name = tokens[1] if len(tokens) == 2 else None,
                is_short = True
            )

        # Case 2: Long flag only.
        if token_types in ((TokenType.LONG,), (TokenType.LONG, TokenType.ARG)):
            return OptSpec(
                name     = tokens[0][2:],
                name_alt = None,
                val_name = tokens[1] if len(tokens) == 2 else None,
                is_short = False
            )

        # Case 3: Short flag and long flag.
        if token_types in ((TokenType.SHORT, TokenType.COMMA, TokenType.LONG),
                           (TokenType.SHORT, TokenType.COMMA, TokenType.LONG, TokenType.ARG)):
            return OptSpec(
                name     = tokens[2][2:],
                name_alt = tokens[0][1:],
                val_name = tokens[3] if len(tokens) == 4 else None,
                is_short = False
            )

        # Case 4: Long flag and short flag (strange order, but acceptable).
        if token_types in ((TokenType.LONG, TokenType.COMMA, TokenType.SHORT),
                           (TokenType.LONG, TokenType.COMMA, TokenType.SHORT, TokenType.ARG)):
            return OptSpec(
                name     = tokens[0][2:],
                name_alt = tokens[2][1:],
                val_name = tokens[3] if len(tokens) == 4 else None,
                is_short = False
            )

        # Case 5: Short flag and long flag with extra argument name.
        if token_types == (TokenType.SHORT, TokenType.ARG, TokenType.COMMA, TokenType.LONG, TokenType.ARG):

            # TODO: Type check for tokens[1] and tokens[4], because some error should be raised
            #       when the inferred type of tokens[1] and tokens[4] is not the same.
            #       But this is not easy, because if type is defined on the description head,
            #       not necessary to raise an error even if the inferred type of tokens[1] and tokens[4] does not match.

            return OptSpec(
                name     = tokens[3][2:],
                name_alt = tokens[0][1:],
                val_name = tokens[1],
                is_short = False
            )

        # Case 6: Long flag and short flag with extra argument name (strange order, but acceptable).
        if token_types == (TokenType.LONG, TokenType.ARG, TokenType.COMMA, TokenType.SHORT, TokenType.ARG):

            # TODO: Type check for tokens[1] and tokens[4], because some error should be raised
            #       when the inferred type of tokens[1] and tokens[4] is not the same.
            #       But this is not easy, because if type is defined on the description head,
            #       not necessary to raise an error even if the inferred type of tokens[1] and tokens[4] does not match.

            return OptSpec(
                name     = tokens[0][2:],
                name_alt = tokens[3][1:],
                val_name = tokens[1],
                is_short = False
            )

        # Otherwise, the declaration line is invalid.
        self.analyze_and_raise()
        raise RuntimeError("Unreachable code reached in DescriptionParser.parse()")

    @staticmethod
    def to_type(token: str) -> OptArgParser.TokenType:
        """
        Convert a token to a token type.
        """
        # Type alias for readability.
        TokenType: TypeAlias = OptArgParser.TokenType

        if token.startswith("--") and len(token) > 2 and token[2] != "-":
            return OptArgParser.TokenType.LONG
        if token.startswith("-") and len(token) > 1 and token[1] != "-":
            return OptArgParser.TokenType.SHORT
        if token == ",":
            return OptArgParser.TokenType.COMMA
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_\.-]*", token):
            return OptArgParser.TokenType.ARG
        return TokenType.OTHER

    def analyze_and_raise(self) -> None:
        """
        Analyze the erroneous optional argument definition and raise an appropriate error.
        """
        # Type aliases for readability.
        TokenKind: TypeAlias = BaseArgParser.TokenKind
        TokenData: TypeAlias = BaseArgParser.TokenData

        # Get the target string.
        target: str = self.docstr[self.span[0]:self.span[1]]

        # Tokenize the specification part of the declaration line.
        tokens: list[TokenData] = list(self.tokenize_spec(target, offset=self.span[0]))

        # Filter out space tokens for further analysis.
        tokens_non_space: list[TokenData] = [token for token in tokens if token.kind != TokenKind.SPACE]

        for idx, token in enumerate(tokens_non_space):

            # Error: Option name is missing after the hyphen(s).
            if token.kind == TokenKind.SHORT and len(token.value) < 2:
                raise YadOptError.NoOptNameInOptArgDecl(**get_target_and_marker(self.docstr, token.span),
                                                        token=token.value)
            if token.kind == TokenKind.LONG and len(token.value) < 3:
                raise YadOptError.NoOptNameInOptArgDecl(**get_target_and_marker(self.docstr, token.span),
                                                        token=token.value)

            # Error: A comma must appear between short and long option names.
            if token.kind == TokenKind.COMMA:
                if idx in (0, len(tokens_non_space) - 1):
                    raise YadOptError.InvalidCommaPosInOptArgDecl(**get_target_and_marker(self.docstr, token.span))
                if tokens_non_space[idx - 1].kind not in (TokenKind.SHORT, TokenKind.LONG) \
                or tokens_non_space[idx + 1].kind not in (TokenKind.SHORT, TokenKind.LONG):
                    raise YadOptError.InvalidCommaUsageInOptArgDecl(**get_target_and_marker(self.docstr, token.span))

            # Error: Unexpected character found in the specification part.
            if token.kind == TokenKind.OTHER:
                raise YadOptError.UnexpectedTokenInOptArgDecl(**get_target_and_marker(self.docstr, token.span),
                                                               token=token.value)

            # Error: '=' sign used in an unsupported place.
            if token.kind == TokenKind.EQUAL:
                raise YadOptError.InvalidEqualUsageInOptArgDecl(**get_target_and_marker(self.docstr, token.span))

        raise YadOptError.UnknownErrorInOptArgDecl(**get_target_and_marker(self.docstr, self.span))


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
