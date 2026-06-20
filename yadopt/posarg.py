"""
yadopt.posarg - parser for positional argument specification in docstring.
"""
from __future__ import annotations

# Import standard libraries.
import dataclasses
import re

# For type hinting.
from typing import TypeAlias

# Import custom modules.
from .basearg import BaseArgParser
from .dtypes  import Span
from .errors  import YadOptError, get_target_and_marker

# Declare published functions and variables.
__all__ = ["PosSpec", "PosArgParser"]


@dataclasses.dataclass(frozen=True)
class PosSpec:
    """
    Parsed result of positional argument definition in docstring.
    """
    name   : str   # Positional argument name.
    is_mult: bool  # Indicates whether this argument can be multiple.

    def validate(self) -> None:
        """
        Run extra validation checks. This function is called only when running tests.
        This is a post-condition assertion in the context of DbC methodology.
        """
        # Data type checks.
        assert isinstance(self.name,    str)
        assert isinstance(self.is_mult, bool)

        # Other checks.
        assert re.match(r"[A-Za-z_][A-Za-z0-9_\.-]*", self.name), f"Invalid positional argument name: {self.name}"


class PosArgParser(BaseArgParser):
    """
    Parser for the declaration line of positional argument in the docstring.
    """
    # Regular expression pattern to match the declaration line of positional argument.
    pattern_posarg: re.Pattern = re.compile(r"""^
    \s*                                         # Leading whitespace.
    ([A-Za-z_] |                                # Single character argument name.
     [A-Za-z_][A-Za-z0-9_\.-]*?[A-Za-z0-9_-])   # Multiple character argument name.
    (\.\.\.)?                                   # Optional ellipsis indicating multiple arguments.
    \s*                                         # Optional whitespace after argument name.
    $""", flags=re.VERBOSE)

    def __init__(self, docstr: str, span: Span, verbose: bool) -> None:
        """
        Constructor.

        Args:
            docstr  (str) : [IN] Original docstring to be parsed.
            span    (Span): [IN] Span of the argument specification part in the original docstring.
            verbose (bool): [IN] Displays verbose messages that are useful for debugging.
        """
        self.docstr  = docstr
        self.span    = span
        self.verbose = verbose

    def parse(self) -> PosSpec:
        """
        Parse the declaration line of positional argument and return the parsed result as PosEntry.

        Returns:
            (PosEntry): Parsed result.
        """
        if self.verbose:
            print("PosArgParser.parse():")
            print("  |- argument specification span =", self.span)
            print("  |- original argument specification = '" + self.docstr[self.span[0]:self.span[1]] + "'")

        match: re.Match | None = self.pattern_posarg.match(self.docstr[self.span[0]:self.span[1]])

        # If the match is successful, extract the argument name and the multiple argument flag.
        if match is not None:
            return PosSpec(
                name     = match.group(1) if match.group(1) is not None else "",
                is_mult  = match.group(2) is not None,
            )

        # If it failed to match, it means something is wrong with the positional argument definition.
        self.analyze_and_raise()
        raise RuntimeError("Unreachable code reached in DescriptionParser.parse()")

    def analyze_and_raise(self) -> None:
        """
        Analyze the erroneous positional argument definition and raise an appropriate error.
        """
        # Type aliases for readability.
        TokenKind: TypeAlias = BaseArgParser.TokenKind
        TokenData: TypeAlias = BaseArgParser.TokenData

        # Extract the specification and description parts from the original docstring using the spans.
        spec: str = self.docstr[self.span[0]:self.span[1]]

        # Tokenize the specification part of the declaration line.
        tokens: list[TokenData] = list(self.tokenize_spec(spec, offset=self.span[0]))

        # Filter out space tokens for further analysis.
        tokens_non_space: list[TokenData] = [token for token in tokens if token.kind != TokenKind.SPACE]

        # Error: Missing argument name.
        if not tokens_non_space:
            raise YadOptError.NoArgNameInPosArgDecl(**get_target_and_marker(self.docstr, self.span))

        # Error: Multiple ellipses found in the specification part.
        tokens_ellipsis: list[TokenData] = [token for token in tokens_non_space if token.kind == TokenKind.ELLIPSIS]
        if len(tokens_ellipsis) > 1:
            raise YadOptError.MultiEllipsisInPosArgDecl(**get_target_and_marker(self.docstr, tokens_ellipsis[1].span))

        for idx, token in enumerate(tokens_non_space, start=0):

            # Error: The first token in the specification part must be a word representing the argument name.
            if idx == 0 and token.kind != TokenKind.WORD:
                if token.kind == TokenKind.ELLIPSIS:
                    raise YadOptError.InvalidEllipsisInPosArgDecl(**get_target_and_marker(self.docstr, token.span))
                raise YadOptError.InvalidArgNameInPosArgDecl(**get_target_and_marker(self.docstr, token.span),
                                                             arg_name=token.value)

            # Error: An ellipsis token is found in an invalid position.
            if token.kind == TokenKind.ELLIPSIS and idx != 1:
                raise YadOptError.InvalidEllipsisInPosArgDecl(**get_target_and_marker(self.docstr, token.span))

            # Error: Extra argument found in the specification part.
            if token.kind == TokenKind.WORD and idx > 0:
                raise YadOptError.ExtraArgsInPosArgDecl(**get_target_and_marker(self.docstr, token.span))

            # Error: Unexpected token found in the specification part.
            if idx > 0 and token.kind != TokenKind.ELLIPSIS:
                raise YadOptError.UnexpectedTokenInPosArgDecl(**get_target_and_marker(self.docstr, token.span),
                                                              token=token.value)

        raise YadOptError.UnknownErrorInPosArgDecl(**get_target_and_marker(self.docstr, self.span))


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
