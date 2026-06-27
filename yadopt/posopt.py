"""
yadopt.declaration - declaration line parser for YadOpt.
"""

# Declare published functions and variables.
__all__ = ["parse_def_line"]

# Import standard libraries.
import enum
import re

# For type hinting.
from collections.abc import Callable

# Import custom modules.
from .analysis import analyze_def_pos, analyze_def_opt, analyze_desc
from .dtypes   import Match, Span, PosEntry, OptEntry
from .utils    import split_after_indent


#===================================================================================================
# Public classes and functions
#===================================================================================================

def parse_def_line(docstr: str, span: Span, group: str, verbose: bool) -> PosEntry | OptEntry:
    """
    Parse the definition line of an argument or option in the docstring and return the parsed result.

    Args:
        docstr  (str) : [IN] Original docstring to be parsed.
        span    (Span): [IN] Span of the declaration line in the original docstring.
        group   (str) : [IN] Group name of this entry.
        verbose (bool): [IN] Displays verbose messages that are useful for debugging.

    Returns:
        (PosEntry | OptEntry): Parsed result.
    """
    # Split the declaration line into the declaration part and the description part.
    (span_spec, span_desc) = split_after_indent(docstr, span, "  ", verbose)

    # Option declaration line starts with a hyphen.
    is_opt: bool = docstr[span_spec[0]:span_spec[1]].strip().startswith("-")

    # Parse the declaration line
    parse_def_func: Callable = parse_def_opt if is_opt else parse_def_arg
    entry: PosEntry | OptEntry = parse_def_func(docstr, span_spec, group, verbose)

    # Parse the description part of the declaration line.
    (desc, type_dsc, default) = parse_description(docstr, span_desc, verbose)

    # Assign the parsed description, type description, and default value to the entry.
    entry.desc     = desc
    entry.type_dsc = type_dsc
    entry.default  = default
    entry.group    = group

    return entry


#===================================================================================================
# Private classes and functions
#===================================================================================================

def parse_def_arg(docstr: str, span: Span, group: str, verbose: bool) -> PosEntry:
    """
    Parse the declaration line as an argument line and return the parsed result as PosEntry.

    Args:
        docstr  (str) : [IN] Original docstring to be parsed.
        span    (Span): [IN] Span of the argument specification part in the original docstring.
        group   (str) : [IN] Group name of this entry.
        verbose (bool): [IN] Displays verbose messages that are useful for debugging.

    Returns:
        (PosEntry): Parsed result.
    """
    if verbose:
        print("In parse_def_arg:")
        print("  |- argument specification span =", span)
        print("  |- original argument specification = '" + docstr[span[0]:span[1]] + "'")

    # The argument declaration line is expected to be in the format "arg_name  description...".
    regex: str = r"""^
    \s*             # Leading whitespace.
    ([A-Za-z_]\w*)  # Argument name (digit-starting names are not allowed).
    (\.\.\.)?       # Optional ellipsis indicating multiple arguments.
    \s*             # Optional whitespace after argument name.
    $"""
    match: Match | None = re.match(regex, docstr[span[0]:span[1]], flags=re.VERBOSE)

    # If it failed to match, it means the positional argument line is invalid.
    if match is None:
        raise analyze_def_pos(docstr, span, verbose)

    return PosEntry(
        name     = match.group(1),
        is_mult  = match.group(2) is not None,
        type_dsc = None,
        desc     = "",
        default  = None,
        group    = group,
    )


def parse_def_opt(docstr: str, span: Span, group: str, verbose: bool) -> OptEntry:
    """
    Parse the declaration line as an option line and return the parsed result as OptEntry.

    Args:
        docstr  (str) : [IN] Original docstring to be parsed.
        span    (Span): [IN] Span of the description part in the original docstring
        group   (str) : [IN] Group name of this entry.
        verbose (bool): [IN] Displays verbose messages that are useful for debugging.

    Returns:
        (OptEntry): Parsed result.
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

    def to_type(token: str) -> TokenType:
        """
        Convert a token to a token type.
        """
        if token.startswith("--") and len(token) > 2 and token[2] != "-":
            return TokenType.LONG
        if token.startswith("-") and len(token) > 1 and token[1] != "-":
            return TokenType.SHORT
        if token == ",":
            return TokenType.COMMA
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", token):
            return TokenType.ARG
        return TokenType.OTHER

    # Tokenize the option specification part of the declaration line.
    tokens: tuple[str, ...] = tuple(token for token in re.split(r"\s+|=|(,)", docstr[span[0]:span[1]]) if token)

    # Convert the tokens to token types.
    token_types: tuple[TokenType, ...] = tuple(to_type(token) for token in tokens)

    if verbose:
        print("Parsing option declaration line:")
        print("  |- original line = '" + docstr[span[0]:span[1]] + "'")
        print("  |- tokens =", tokens)
        print("  |- token types =", token_types)

    # Initialize the parsed entry with default values.
    entry: OptEntry = OptEntry(
        name      = "",
        name_alt  = None,
        val_name  = None,
        raw_names = [],
        type_dsc  = None,
        desc      = "",
        default   = None,
        group     = group,
    )

    # Case 1: Short flag only.
    if token_types in ((TokenType.SHORT,), (TokenType.SHORT, TokenType.ARG)):

        # Set the option name.
        entry.name = tokens[0][1:]

        # Set the option argument name if it exists.
        entry.val_name = tokens[1] if len(tokens) == 2 else None

        # Set the raw name as the original short flag.
        entry.raw_names = [tokens[0]]

    # Case 2: Long flag only.
    elif token_types in ((TokenType.LONG,), (TokenType.LONG, TokenType.ARG)):

        # Set the option name.
        entry.name = tokens[0][2:]

        # Set the option argument name if it exists.
        entry.val_name = tokens[1] if len(tokens) == 2 else None

        # Set the raw name as the original long flag.
        entry.raw_names = [tokens[0]]

    # Case 3: Short flag and long flag.
    elif token_types in ((TokenType.SHORT, TokenType.COMMA, TokenType.LONG),
                         (TokenType.SHORT, TokenType.COMMA, TokenType.LONG, TokenType.ARG)):

        # Set the option name and alternative name.
        entry.name     = tokens[2][2:]
        entry.name_alt = tokens[0][1:]

        # Set the option argument name if it exists.
        entry.val_name = tokens[3] if len(tokens) == 4 else None

        # Set the raw name as the original short flag and long flag.
        entry.raw_names = [tokens[0], tokens[2]]

    # Case 4: Short flag and long flag with extra argument name.
    elif token_types == (TokenType.SHORT, TokenType.ARG, TokenType.COMMA, TokenType.LONG, TokenType.ARG):

        # Set the option name and alternative name.
        entry.name     = tokens[3][2:]
        entry.name_alt = tokens[0][1:]

        # Set the option argument name if it exists.
        entry.val_name = tokens[1]

        # Set the raw name as the original short flag and long flag.
        entry.raw_names = [tokens[0], tokens[3]]

    # Otherwise, the declaration line is invalid.
    else:
        raise analyze_def_opt(docstr, span, verbose)

    # Make sure the hyphens in the option names are replaced with underscores for valid Python identifiers.
    entry.name = entry.name.replace("-", "_")
    if entry.name_alt is not None:
        entry.name_alt = entry.name_alt.replace("-", "_")

    return entry


def parse_description(docstr: str, span: Span, verbose: bool) -> tuple[str, str|None, str|None]:
    """
    Parse the description part of the declaration line.

    Args:
        docstr  (str) : [IN] Original docstring to be parsed.
        span    (Span): [IN] Span of the description part in the original docstring
        verbose (bool): [IN] Displays verbose messages that are useful for debugging.

    Returns:
        description (str)     : Description text with type and default value removed.
        type_dsc    (str|None): Type description if it exists, otherwise None.
        default     (str|None): Default value if it exists, otherwise None.
    """
    # Get the target description text from the original docstring using the given span.
    target: str = docstr[span[0]:span[1]]

    # If the description is multi-line, join the lines.
    if "\n" in target:
        target = " ".join(line.strip() for line in target.split("\n"))

    if verbose:
        print("In parse_description:")
        print("  |- description span =", span)
        print("  |- original description = '" + docstr[span[0]:span[1]] + "'")
        print("  |- joined description = '" + target + "'")

    # Search for the default value in the description.
    pattern: str = r"""^
    \s*                              # Leading whitespace.
    (?:\((\w+)\))?                   # Optional type description in parentheses.
    \s*                              # Optional whitespace after type description.
    (.+?)                            # Description text (non-greedy).
    (?:\s+\[default:\s*(.+?)\s*\])?  # Optional default value in the format "[default: ...]".
    \s*                              # Trailing whitespace.
    $"""
    match: Match | None = re.match(pattern, target, flags=re.VERBOSE)

    # If it failed to match, it means the optional argument line is invalid.
    if match is None:
        raise analyze_desc(docstr, span, verbose)

    return (match.group(2).strip(), match.group(1), match.group(3))


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
