"""
Collection of utility functions.
"""

# Import standard libraries.
import re

# For type hinting.
from collections.abc import Generator


def get_default(description: str) -> tuple:
    """
    Get default value.

    Args:
        description (str): Description message contains default value.

    Returns:
        (tuple): A tuple of (rest of description, default value string).

    Examples:
        >>> get_default("sample description [default: value]")
        ('sample description', 'value')
    """
    default_pattern = r"^(.*)\s+\[default:\s*([^\]]+)\]\s*$"

    # Search default string.
    m = re.fullmatch(default_pattern, description)

    # Returns entire description and None if no default string found.
    if m is None:
        return (description.strip(), None)

    # Otherwise, returns rest of descriptions and default string.
    return (m.group(1).strip(), m.group(2).strip())


def get_error_marker(line: str, token: str) -> str:
    """
    Args:
        line  (str): Entire line.
        token (str): Target token.

    Returns:
        (str): Error marker string like.

    Examples:
        >>> get_error_marker("this is a pen", "pen")
        '          ^^^'
        >>> get_error_marker("this is a pen", "pencil")
        '             '
    """
    pos = line.find(token)

    # Returns whitespace if the token not found in the line.
    if pos < 0:
        return " " * len(line)

    return " " * pos + "^" * len(token) + " " * (len(line) - len(token) - pos)


def remove_indent(text: str | None) -> str:
    """
    Remove common indent from the given text.
    If the input text is None then this function returns empty string.

    Args:
        text (str): Input text.

    Returns:
        (str): Text after removing the common indent.

    Examples:
        >>> remove_indent("  A\\n  B\\n  C")
        'A\\nB\\nC'
    """
    # Returns None if the input text is None.
    if isinstance(text, str):

        # Get non-empty lines.
        lines = [line for line in text.split("\n") if line.strip()]

        # Compute minimum indent of the non-empty lines.
        min_indent = min(len(line) - len(line.lstrip()) for line in lines)

        return "\n".join(line[min_indent:] for line in text.split("\n"))

    return ""


def strtobool(s: str) -> bool | None:
    """
    Convert the given string to bool instance. The function `bool(...)` is not suitable
    for this purpose, because `bool("False")` returns `True`.

    Args:
        s (str): Input string.

    Returns:
        (bool): Corresponding boolean value.

    Examples:
        >>> strtobool("True")
        True
        >>> strtobool("False")
        False
    """
    if s.lower() in {"t", "true", "y", "yes", "on", "1"}:
        return True
    if s.lower() in {"f", "false", "n", "no", "off", "0"}:
        return False
    return None


def retokenize(argv: list[str]) -> Generator[str]:
    """
    Tokenize the argument vector.

    Args:
        target (str): Target string to be tokenized.

    Returns:
        (Generator[str]): Re-tokenized tokens.

    Examples:
        >>> list(retokenize(["A=a", "B=b"]))
        ['A', 'a', 'B', 'b']
    """
    for token in argv:
        yield from token.split("=", maxsplit=1)


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
