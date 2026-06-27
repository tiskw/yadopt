"""
yadopt.utils - collections of utility functions
"""

# Declare published functions and variables.
__all__ = ["is_python_value", "retokenize", "split_after_indent"]

# Import standard libraries.
import ast
import re

# For type hinting.
from collections.abc import Generator

# Import custom modules.
from .dtypes import Span


#===================================================================================================
# Public classes and functions
#===================================================================================================

def is_python_value(text: str) -> bool:
    """
    Returns true if the given string can be interpreted as a Python literal.

    Args:
        text (str): Input text.

    Returns:
        (bool): True if the given text is a Python literal.

    Examples:
        >>> is_python_value("-1")
        True
        >>> is_python_value("-h")
        False
    """
    try:
        ast.literal_eval(text)
    except (SyntaxError, TypeError, ValueError):
        return False
    return True


def retokenize(argv: list[str]) -> Generator[str]:
    """
    Tokenize the argument vector.
    This function split a token like "--option=value" into two tokens ["--option", "value].

    Args:
        argv (list[str]): [IN] Argument vector to be tokenized.

    Returns:
        (Generator[str]): Re-tokenized tokens.

    Examples:
        >>> list(retokenize(["--option=value", "hoge=fuga"]))
        ['--option', 'value', 'hoge=fuga']
        >>> list(retokenize(["--option=hoge=fuga"]))
        ['--option', 'hoge=fuga']
    """
    for token in argv:

        if re.fullmatch(r"(--?\w[\w-]*)(=(.+))?", token) is not None:
            yield from token.split("=", maxsplit=1)

        else:
            yield token


def split_after_indent(text: str, span: Span, delim: str, verbose: bool) -> tuple[Span, Span]:
    """
    Split the given string by the first occurrence of a delimiter while ignoring indent.

    Args:
        docstr  (str) : [IN] Original string to be parsed.
        span    (Span): [IN] Span of the target line to be split.
        delim   (str) : [IN] Delimiter between the declaration part and the description part.
        verbose (bool): [IN] Displays verbose messages that are useful for debugging.

    Returns:
        span_spec (Span): Span of the first part in the original string.
        span_desc (Span): Span of the second part in the original string.

    Examples:
        >>> split_after_indent("    -a int", (0, 10), "  ", False)
        ((0, 10), (10, 10))
        >>> split_after_indent("    -a int  Description.", (0, 24), "  ", False)
        ((0, 10), (10, 24))
    """
    # Get the indent of the original string.
    indent: int = len(text[span[0]:span[1]]) - len(text[span[0]:span[1]].lstrip())

    # If there is no delim, it means there is no second part.
    if delim not in text[span[0]+indent:span[1]]:
        return (span, (span[1], span[1]))

    # Find the position of the delimiter between the first and second part.
    pos_delim: int = text[span[0]+indent:span[1]].find(delim) + span[0] + indent

    # If there is no double space, it means there is no description part.
    span_spec: Span = (span[0], pos_delim)
    span_desc: Span = (pos_delim, span[1])

    return (span_spec, span_desc)


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
