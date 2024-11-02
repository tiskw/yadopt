"""
usage parser
"""

# Declare published functins and variables.
__all__ = ["parse_usage", "UsageEntry"]

# Import standard libraries.
import copy
import dataclasses
import re

# Import custom modules.
from .errors import YadOptError


@dataclasses.dataclass
class UsageEntry:
    """
    Usage pattern info.
    """
    pres: list[str]  # Preceding tokens.
    args: list[str]  # Argument tokens.
    opts: dict       # Option tokens.


def tokenize(usage: str, strip: bool = True, drop_empty_token: bool = True):
    """
    Tokenize usage string.

    Args:
        usage             (str) : Usage string.
        strip             (bool): Strip whitespace from returned tokens if true.
        drop_empty_token  (bool): Drop empty token if True.

    Examples:
    >>> list(tokenize("sample.py <arg1> [--opt1]"))
    ['sample.py', '<arg1>', '[--opt1]']
    >>> list(tokenize("sample.py subcmd <arg1> <arg2> [--opt1] [--opt2 val2]"))
    ['sample.py', 'subcmd', '<arg1>', '<arg2>', '[--opt1]', '[--opt2 val2]']
    """
    token_patterns = [
        r"\s+",                    # Whitespace
        r"[\w\.-]+",               # Preceding token
        r"<\w+>",                  # Argument token
        r"<\w+\.\.\.>",            # Argument token
        r"\[[\w\.-]+\]",           # Optional token
        r"\[[\w\.-]+ [\w\.-]+\]",  # Optional token with value (space)
        r"\[[\w\.-]+=[\w\.-]+\]",  # Optional token with value (equal)
    ]

    # Copy the input usage string for safety.
    usage_line = copy.deepcopy(usage)

    while usage_line:

        # Find matched patterns.
        for pattern in token_patterns:
            if (m := re.match(pattern, usage_line)) is not None:
                break

        # Raise an error if no pattern matched.
        if m is None:
            raise YadOptError["usage_parse"](usage_line, usage)

        # Get matched substring.
        token = m.group(0)

        # Returns token as generator.
        if (not drop_empty_token) or (len(token.strip()) > 0):
            yield token.strip() if strip else token

        # Remove the returned token.
        usage_line = usage_line[len(token):]


def parse_usage(line: str) -> UsageEntry:
    """
    Parse usage string.

    Args:
        line (str): Input usage string.

    Examples:
    >>> parse_usage("sample.py <arg1> <arg2> [--opt1]")
    UsageEntry(pres=['sample.py'], args=['arg1', 'arg2'], opts={'opt1': None})
    >>> parse_usage("sample.py subcmd <arg1> [--opt1] [--opt2 val2]")
    UsageEntry(pres=['sample.py', 'subcmd'], args=['arg1'], opts={'opt1': None, 'opt2': 'val2'})
    """
    def is_arg(token):
        return token.startswith("<") and token.endswith(">")

    def is_opt(token):
        return token.startswith("-") or (token.startswith("[") and token.endswith("]"))

    def parse_arg(token):
        return token.strip("<>")

    def parse_opt(token):
        for delim in [" ", "="]:
            if delim in token:
                return tuple(token.strip("[]").lstrip("-").split(delim, maxsplit=1))
        return (token.strip("[]").lstrip("-"), None)

    # Initialize output variable.
    pattern = UsageEntry([], [], {})

    # Tokenize usage string.
    tokens = list(tokenize(line))

    # Extract preceding tokens until arguments or options appears.
    while tokens and (not is_arg(tokens[0])) and (not is_opt(tokens[0])):
        pattern.pres.append(tokens.pop(0))

    # Process arguments and options.
    for token in tokens:
        if   is_arg(token): pattern.args += [parse_arg(token)]
        elif is_opt(token): pattern.opts |= [parse_opt(token)]
        else              : raise YadOptError["invalid_constant"](token, line)

    return pattern


if __name__ == "__main__":
    import doctest
    doctest.testmod()


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
