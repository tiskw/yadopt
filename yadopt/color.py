"""
yadopt.color - colorize strings
"""

# Declare published functions and variables.
__all__ = ["colorize_help_message", "colorize_error_message"]

# Import standard libraries.
import re
import sys

# For type hinting.
from typing import TypeAlias

# Alias for data type annotations.
PatternType: TypeAlias = tuple[str, list[int], bool]
MatchedType: TypeAlias = tuple[tuple[str | None, ...], str, bool]


####################################################################################################
# Public classes and functions
####################################################################################################

def colorize_help_message(help_message: str) -> str:
    """
    Returns colored help message.

    Args:
        help_message (str): [IN] Help message.

    Returns:
        (str): Colorized string.
    """
    def colorize_arg(line: str, key: str | None) -> str:
        """
        Colorize argument.
        """
        if key is not None:
            return line.replace(f" {key} ", f" {COLOR_ARG}{key}{COLOR_NON} ", 1)
        return line

    def colorize_opt(line: str, key: str | None) -> str:
        """
        Colorize options.
        """
        if (key is not None) and (f" --{key}" in line):
            return line.replace(f" --{key}", f" {COLOR_LNG}--{key}{COLOR_NON}", 1)
        if (key is not None) and (f" -{key}" in line):
            return line.replace(f" -{key}", f" {COLOR_SHT}-{key}{COLOR_NON}", 1)
        return line

    def colorize_sec(line: str) -> str:
        """
        Colorize section.
        """
        return COLOR_SEC + line[:-1] + COLOR_NON + ":"

    def colorize_arg_line(line: str) -> str:
        """
        Colorize argument tokens in a line.
        """
        # Parse the line as an argument line, and do nothing if not matched.
        match_info = match_arg(line)[0]
        if len(match_info) == 0:
            return line

        line = colorize_arg(line, match_info[0])
        return line

    def colorize_opt_line(line: str) -> str:
        """
        Colorize option tokens in a line.
        """
        # Parse the line as an option line, and do nothing if not matched.
        match_info = match_opt(line)[0]
        if len(match_info) == 0:
            return line

        line = colorize_opt(line, match_info[0])
        line = colorize_opt(line, match_info[1])
        line = colorize_arg(line, match_info[2])
        return line

    def colorize_usg_line(line: str) -> str:
        """
        Colorize usage line.
        """
        line = re.sub(r"<(\w+)>", f"<{COLOR_ARG}\\1{COLOR_NON}>", line)
        line = re.sub(r"(--\w+)( |\]|$)", F"{COLOR_LNG}\\1{COLOR_NON}\\2", line)
        line = re.sub(r"(-\w+)( |\]|$)", f"{COLOR_SHT}\\1{COLOR_NON}\\2", line)
        line = re.sub(r"\[([^\]]*) (\w+)\]", f"[\\1 {COLOR_ARG}\\2{COLOR_NON}]", line)
        return line

    # Do nothing if the output is not a TTY.
    if not sys.stdout.isatty():
        return help_message

    # Initialize the output lines.
    output_lines: list[str] = []

    # Initialize section flags.
    is_usg: bool = False
    is_arg: bool = False
    is_opt: bool = False

    # Initialize the output lines.
    for line in help_message.split("\n"):

        # Colorize the line.
        if is_usg:
            line = colorize_usg_line(line)
        elif is_arg:
            line = colorize_arg_line(line)
        elif is_opt:
            line = colorize_opt_line(line)

        # Update section flags.
        if line.endswith(":") or (line.startswith("[") and line.endswith("]")):
            is_usg = "usage"     in line.lower()
            is_arg = "arguments" in line.lower()
            is_opt = "options"   in line.lower()
            line = colorize_sec(line)

        output_lines.append(line)

    return "\n".join(output_lines)


def colorize_error_message(error_message: str) -> str:
    """
    Colorize error message.

    Args:
        error_message (str): [IN] Help message.

    Returns:
        (str): Colorized string.
    """
    # Do nothing if the output is not a TTY.
    if not sys.stdout.isatty():
        return error_message

    # Colorize section header.
    error_message = re.sub(r"^(<[a-zA-Z ]+>)\s*$", f"{COLOR_SEC}\\1{COLOR_NON}", error_message, flags=re.MULTILINE)

    # Colorize string literal.
    error_message = re.sub(r"('[^\']*')", f"{COLOR_STR}\\1{COLOR_NON}", error_message)
    error_message = re.sub(r'("[^\"]*")', f"{COLOR_STR}\\1{COLOR_NON}", error_message)

    return error_message


#===================================================================================================
# Private classes and functions
#===================================================================================================

# Define colors.
COLOR_ARG: str = "\x1B[33;1m"
COLOR_SHT: str = "\x1B[32;1m"
COLOR_LNG: str = "\x1B[34;1m"
COLOR_SEC: str = "\x1B[35;1m"
COLOR_STR: str = "\x1B[31;1m"
COLOR_NON: str = "\x1B[0m"

# Define matching patterns.
PATTERNS_AND_INDICES_ARG: list[PatternType] = [
    # regular expression, [name index], optional flag
    # ------------------------------------------------
    (r"\s+(\w+)",         [1],          False),
]
PATTERNS_AND_INDICES_OPT: list[PatternType] = [
    # regular expression,        (name, alt, value), has_value # | type  | value  | delim |
    # -------------------------------------------------------- # --------------------------
    (r"\s+-(\w+)=(\w+), --(\w+)=(\w+)", [3,  1,  2], True ),   # | both  | double | equal |
    (r"\s+-(\w+) (\w+), --(\w+) (\w+)", [3,  1,  2], True ),   # | both  | double | space |
    (r"\s+-(\w+), --(\w+)=(\w+)",       [2,  1,  3], True ),   # | both  | single | equal |
    (r"\s+-(\w+), --(\w+) (\w+)",       [2,  1,  3], True ),   # | both  | single | space |
    (r"\s+-(\w+), --(\w+)",             [2,  1, -1], False),   # | both  | none   | -     |
    (r"\s+--(\w+)=(\w+)",               [1, -1,  2], True ),   # | long  | single | equal |
    (r"\s+--(\w+) (\w+)",               [1, -1,  2], True ),   # | long  | single | space |
    (r"\s+--(\w+)",                     [1, -1, -1], False),   # | long  | none   | -     |
    (r"\s+-(\w+)=(\w+)",                [1, -1,  2], True ),   # | short | single | equal |
    (r"\s+-(\w+) (\w+)",                [1, -1,  2], True ),   # | short | single | space |
    (r"\s+-(\w+)",                      [1, -1, -1], False),   # | short | none   | -     |
]
PATTERNS_AND_INDICES_SEC: list[PatternType] = [
    # regular expression,  [section_name_index], Dummy flag #
    # ----------------------------------------------------- #
    (r"^([\w ]+):\s*$",    [1,],                 False),    # SectionName:
    (r"^\[([\w ]+)\]\s*$", [1,],                 False),    # [SectionName]
]


def match_and_get(line: str, patterns_and_indices: list[PatternType]) -> MatchedType:
    """
    Parse the given string and returns specified matched strings.

    Args:
        line                 (str)              : [IN] The target line.
        patterns_and_indices (list[PatternType]): [IN] List of patterns and index of returned values.

    Returns:
        (tuple[str]): A tuple of matched strings corresponding to the indices,
                      and the rest of matched strings.

    Examples:
        >>> match_and_get("-h, --help", [(r"-(\\w+), --(\\w+)", (2, 1), None)])
        (('help', 'h'), '', None)
    """
    for pattern, indices, optional_flag in patterns_and_indices:

        # Compute regular expression match, and continue the loop if not matched.
        if (m := re.match(pattern, line, re.ASCII)) is None:
            continue

        # Get the required matched strings.
        output: list[str | None] = [None if idx < 0 else m[idx] for idx in indices]

        # Get the rest of the matched strings.
        rest: str = line[len(m.group(0)):]

        return (tuple(output), rest, optional_flag)

    return ((), line, False)


def match_arg(line: str) -> MatchedType:
    """
    Parse arguments line.

    Args:
        line (str): [IN] Target string.

    Returns:
        (MatchedType): A tuple of matched strings.

    Examples:
        >>> match_arg("  config_path   Path to config file.")
        (('config_path',), '   Path to config file.', False)
    """
    return match_and_get(line, PATTERNS_AND_INDICES_ARG)


def match_opt(line: str) -> MatchedType:
    """
    Parse arguments line.

    Args:
        line (str): [IN] Target string.

    Returns:
        (MatchedType): A tuple of matched strings.

    Examples:
        >>> match_opt("  -h, --help   show this message and exit.")
        (('help', 'h', None), '   show this message and exit.', False)
    """
    return match_and_get(line, PATTERNS_AND_INDICES_OPT)


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
