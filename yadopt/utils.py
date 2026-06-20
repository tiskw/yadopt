"""
yadopt.utils - collections of utility functions.
"""
from __future__ import annotations

# Import standard libraries.
import ast

# Declare published functions and variables.
__all__ = ["is_python_value"]


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


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
