"""
yadopt.analysis - analyze erroneous user input.
"""

# Import standard libraries.
import enum
import re
import typing

# For type hinting.
from typing import Generator

# Import custom modules.
from .dtypes import Span, ArgsInfo
from .errors import YadOptError, get_target_and_marker
from .utils  import split_after_indent


#===================================================================================================
# Public functions
#===================================================================================================

def analyze_def_pos(docstr: str, span: Span, verbose: bool) -> Exception:
    """
    Analyze the erroneous positional argument definition and return an error instance.

    Args:
        docstr  (str) : [IN] The original docstring containing the declaration line.
        span    (Span): [IN] The span of the declaration line in the original docstring.
        verbose (bool): [IN] Whether to include detailed error messages.

    Returns:
        (Exception): An instance of an error class.
    """
    # Split the declaration line into specification and description parts based on the span and indentation.
    (span_spec, _) = split_after_indent(docstr, span, "  ", verbose)

    # Extract the specification and description parts from the original docstring using the spans.
    spec: str = docstr[span_spec[0]:span_spec[1]]

    # Tokenize the specification part of the declaration line.
    tokens: list[TokenData] = list(tokenize_spec(spec, offset=span_spec[0]))

    # Filter out space tokens for further analysis.
    tokens_non_space: list[TokenData] = [token for token in tokens if token.kind != TokenKind.SPACE]

    # Error: Missing argument name.
    if not tokens_non_space:
        return YadOptError.NoArgNameInPosArgDecl(**get_target_and_marker(docstr, span_spec))

    # Error: Multiple ellipses found in the specification part.
    tokens_ellipsis: list[TokenData] = [token for token in tokens_non_space if token.kind == TokenKind.ELLIPSIS]
    if len(tokens_ellipsis) > 1:
        return YadOptError.MultiEllipsisInPosArgDecl(**get_target_and_marker(docstr, tokens_ellipsis[1].span))

    for idx, token in enumerate(tokens_non_space, start=0):

        # Error: The first token in the specification part must be a word representing the argument name.
        if idx == 0 and token.kind != TokenKind.WORD:
            if token.kind == TokenKind.ELLIPSIS:
                return YadOptError.InvalidEllipsisInPosArgDecl(**get_target_and_marker(docstr, token.span))
            return YadOptError.InvalidArgNameInPosArgDecl(**get_target_and_marker(docstr, token.span),
                                                          arg_name=token.value)

        # Error: An ellipsis token is found in an invalid position.
        if token.kind == TokenKind.ELLIPSIS and idx != 1:
            return YadOptError.InvalidEllipsisInPosArgDecl(**get_target_and_marker(docstr, token.span))

        # Error: Extra argument found in the specification part.
        if token.kind == TokenKind.WORD and idx > 0:
            return YadOptError.ExtraArgsInPosArgDecl(**get_target_and_marker(docstr, token.span))

        # Error: Unexpected token found in the specification part.
        if idx > 0 and token.kind != TokenKind.ELLIPSIS:
            return YadOptError.UnexpectedTokenInPosArgDecl(**get_target_and_marker(docstr, token.span),
                                                           token=token.value)

    return YadOptError.UnknownErrorInPosArgDecl(**get_target_and_marker(docstr, span_spec))


def analyze_def_opt(docstr: str, span: Span, verbose: bool) -> Exception:
    """
    Analyze the erroneous optional argument definition and return an error instance.

    Args:
        docstr  (str) : [IN] The original docstring containing the declaration line.
        span    (Span): [IN] The span of the declaration line in the original docstring.
        verbose (bool): [IN] Whether to include detailed error messages.

    Returns:
        (Exception): An instance of an error class.
    """
    # Split the declaration line into specification and description parts based on the span and indentation.
    (span_spec, _) = split_after_indent(docstr, span, "  ", verbose)

    # Extract the specification and description parts from the original docstring using the spans.
    spec: str = docstr[span_spec[0]:span_spec[1]]

    # Tokenize the specification part of the declaration line.
    tokens: list[TokenData] = list(tokenize_spec(spec, offset=span_spec[0]))

    # Filter out space tokens for further analysis.
    tokens_non_space: list[TokenData] = [token for token in tokens if token.kind != TokenKind.SPACE]

    for idx, token in enumerate(tokens_non_space):

        # Error: Option name is missing after the hyphen(s).
        if token.kind == TokenKind.SHORT and len(token.value) < 2:
            return YadOptError.NoOptNameInOptArgDecl(**get_target_and_marker(docstr, token.span), token=token.value)
        if token.kind == TokenKind.LONG and len(token.value) < 3:
            return YadOptError.NoOptNameInOptArgDecl(**get_target_and_marker(docstr, token.span), token=token.value)

        # Error: A comma must appear between short and long option names.
        if token.kind == TokenKind.COMMA:
            if idx in (0, len(tokens_non_space) - 1):
                return YadOptError.InvalidCommaPosInOptArgDecl(**get_target_and_marker(docstr, token.span))
            if tokens_non_space[idx - 1].kind not in (TokenKind.SHORT, TokenKind.LONG) \
            or tokens_non_space[idx + 1].kind not in (TokenKind.SHORT, TokenKind.LONG):
                return YadOptError.InvalidCommaUsageInOptArgDecl(**get_target_and_marker(docstr, token.span))

        # Error: Unexpected character found in the specification part.
        if token.kind == TokenKind.OTHER:
            return YadOptError.UnexpectedTokenInOptArgDecl(**get_target_and_marker(docstr, token.span),
                                                           token=token.value)

        # Error: '=' sign used in an unsupported place.
        if token.kind == TokenKind.EQUAL:
            return YadOptError.InvalidEqualUsageInOptArgDecl(**get_target_and_marker(docstr, token.span))

    return YadOptError.UnknownErrorInOptArgDecl(**get_target_and_marker(docstr, span_spec))


def analyze_desc(docstr: str, span: Span, verbose: bool) -> Exception:
    """
    Analyze the erroneous description and return an error instance.

    Args:
        docstr  (str) : [IN] The original docstring containing the declaration line.
        span    (Span): [IN] The span of the declaration line in the original docstring.
        verbose (bool): [IN] Whether to include detailed error messages.

    Returns:
        (Exception): An instance of an error class.
    """
    raise NotImplementedError("Description analysis is not implemented yet.")


def check_arginf(arginf: ArgsInfo, verbose: bool) -> None:
    """
    Check the consistency of the parsed result of docstring and raise an error if it is inconsistent.

    Args:
        arginf  (ArgsInfo): [IN] The parsed result of docstring.
        verbose (bool)    : [IN] Whether to include detailed error messages.
    """
    # Check for duplicate argument names.
    arg_names: set[str] = set()
    for entry in arginf.posargs + arginf.optargs:

        # Check for duplicate names in the parsed entries.
        if entry.name in arg_names:
            raise YadOptError.DuplicatedName(name=entry.name)
        if hasattr(entry, "name_alt") and entry.name_alt in arg_names:
            raise YadOptError.DuplicatedName(name=entry.name_alt)

        # Add the names of the current entry to the set of seen names.
        arg_names.add(entry.name)
        if hasattr(entry, "name_alt") and entry.name_alt is not None:
            arg_names.add(entry.name_alt)

    # Check the existance of positional argument after the multiple positional argument.
    has_mult_pos_arg: bool = False
    for entry in arginf.posargs:
        if has_mult_pos_arg:
            raise YadOptError.PosArgAfterMult(name=entry.name)
        if entry.is_mult:
            has_mult_pos_arg = True

    # The option "--help" should be an option without a value.
    for entry in arginf.optargs:
        if entry.name == "help" and entry.val_name is not None:
            raise YadOptError.InvalidHelpOption()


#===================================================================================================
# Private classes and functions
#===================================================================================================

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
    kind : TokenKind
    value: str
    span : Span


def tokenize_spec(text: str, offset: int = 0) -> Generator[TokenData, None, None]:
    """
    Tokenize a declaration specification.

    Args:
        text   (str) : [IN] The specification part of a declaration line.
        offset (int) : [IN] The offset of the specification part in the original docstring.

    Yields:
        TokenData: A named tuple containing the kind, value, and span of each token.
    """
    # pattern: str = r"\.\.\.|--[A-Za-z0-9_]+|-[A-Za-z0-9_]{1}|[A-Za-z0-9_]+|,|=|\s+|--|-|."
    pattern: str = r"""
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
    """

    for match in re.finditer(pattern, text, flags=re.VERBOSE):

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
