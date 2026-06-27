"""
yadopt.basearg - Base class for positional and optional arguments parser.
"""
from __future__ import annotations

# Import standard libraries.
import enum
import re
import typing

# For type hinting.
from typing import Generator, TypeAlias

# Import custom modules.
from .dtypes import Span

# Declare published functions and variables.
__all__ = ["BaseArgParser"]


class BaseArgParser:
    """
    Base class for positional and optional arguments parser.
    """
    # Regular expression pattern to tokenize the declaration line of positional argument.
    pattern_tokenize: re.Pattern = re.compile(r"""
        \.\.\.           |   # Ellipsis token.
        --[A-Za-z0-9_]+  |   # Long option token.
        -[A-Za-z0-9_]{1} |   # Short option token.
        [A-Za-z0-9_]+    |   # Word token.
        ,                |   # Comma token.
        =                |   # Equal sign token.
        \s+              |   # Space token.
        --               |   # Long option prefix without name.  (invalid)
        -                |   # Short option prefix without name. (invalid)
        .                    # Any other single character.       (invalid)
    """, flags=re.VERBOSE)

    class TokenKind(enum.Enum):
        """
        Enumeration of token kinds in a specification of declaration line.
        """
        SPACE    = enum.auto()
        ELLIPSIS = enum.auto()
        COMMA    = enum.auto()
        EQUAL    = enum.auto()
        LONG     = enum.auto()
        SHORT    = enum.auto()
        WORD     = enum.auto()
        OTHER    = enum.auto()

    class TokenData(typing.NamedTuple):
        """
        Information of token in a specification of declaration line.
        """
        kind : BaseArgParser.TokenKind
        value: str
        span : Span

    @staticmethod
    def tokenize_spec(text: str, offset: int = 0) -> Generator[TokenData, None, None]:
        """
        Tokenize a declaration specification.

        Args:
            text   (str) : [IN] The specification part of a declaration line.
            offset (int) : [IN] The offset of the specification part in the original docstring.

        Yields:
            TokenData: A named tuple containing the kind, value, and span of each token.
        """
        # Type aliases for readability.
        TokenKind: TypeAlias = BaseArgParser.TokenKind
        TokenData: TypeAlias = BaseArgParser.TokenData

        for match in BaseArgParser.pattern_tokenize.finditer(text):

            token: str = match.group(0)

            if token.isspace():
                kind = TokenKind.SPACE
            elif token == "...":
                kind = TokenKind.ELLIPSIS
            elif token == ",":
                kind = TokenKind.COMMA
            elif token == "=":
                kind = TokenKind.EQUAL
            elif token.startswith("--"):
                kind = TokenKind.LONG
            elif token.startswith("-"):
                kind = TokenKind.SHORT
            elif re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", token):
                kind = TokenKind.WORD
            else:
                kind = TokenKind.OTHER

            yield TokenData(kind, token, (match.start() + offset, match.end() + offset))






# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
