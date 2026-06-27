"""
yadopt.section - section parser for YadOpt.
"""

# Declare published functions and variables.
__all__ = ["get_section_lines"]

# Import standard libraries.
import re

# For type hinting.
from typing import Generator

# Import custom modules.
from .dtypes import Span


#===================================================================================================
# Public classes and functions
#===================================================================================================

def get_section_lines(docstr: str, verbose: bool) -> Generator[tuple[str, Span], None, None]:
    """
    Get the spans of lines in the docstring.
    """
    if re.search(PATTERN_SECTION, docstr, flags=re.MULTILINE|re.IGNORECASE|re.VERBOSE) is not None:
        yield from get_section_lines_with_section(docstr, verbose)
    else:
        yield from get_section_lines_without_section(docstr, verbose)


#===================================================================================================
# Private classes and functions
#===================================================================================================

# Section patterns.
PATTERN_SECTION: str = r"""
    ^\s*(?:
    (?P<colon>.*):
    |
    \[(?P<bracket>.*)\]
    )\s*$
"""


def get_section_lines_with_section(docstr: str, verbose: bool) -> Generator[tuple[str, Span], None, None]:
    """
    Get the spans of lines in the argument and option sections of the given docstring.

    Args:
        docstr  (str) : [IN] Docstring to be parsed.
        verbose (bool): [IN] Displays verbose messages that are useful for debugging.

    Yields:
        (Span): Span of each line in the original docstring.
    """
    for match in re.finditer(PATTERN_SECTION, docstr, flags=re.MULTILINE|re.IGNORECASE|re.VERBOSE):

        # Get the section name.
        section_name: str = match.group("colon") if match.group("colon") else match.group("bracket")

        # Skip if the section name is not "argument(s)" or "option(s)".
        if "arguments" not in section_name.lower() and "options" not in section_name.lower():
            continue

        # Get the start index of the section in the original docstring.
        section_start: int = match.span(0)[1]

        # Parse the section into lines and yield the spans of each line with the section name.
        for span in parse_section_into_lines(docstr, section_start + 1, verbose):
            yield (section_name, span)


def get_section_lines_without_section(docstr: str, verbose: bool) -> Generator[tuple[str, Span], None, None]:
    """
    Get the spans of lines in the the given docstring.

    Args:
        docstr  (str) : [IN] Docstring to be parsed.
        verbose (bool): [IN] Displays verbose messages that are useful for debugging.

    Yields:
        (Span): Span of each line in the original docstring.
    """
    # Parse the section into lines and yield the spans of each line with the section name.
    for span in parse_section_into_lines(docstr, 0, verbose):
        yield ("", span)


def parse_section_into_lines(text: str, offset: int, verbose: bool) -> Generator[Span, None, None]:
    """
    Split the given section into lines and yields the spans of each line.

    Args:
        text    (str) : [IN] Text to be split.
        offset  (int) : [IN] Start index of the section in the original text.
        verbose (bool): [IN] Displays verbose messages that are useful for debugging.

    Yields:
        (Span): Span of each line in the original text.
    """
    # Tab character will be replaced with TAB_WIDTH spaces.
    tab_width: int = 4

    def get_indent(text: str) -> int:
        """
        Get indent depth of the given text.
        """
        match: re.Match | None = re.match(r"^(\s*)", text)
        return 0 if (match is None) else len(match.group(1).replace("\t", " " * tab_width))

    # Get the section text to parse.
    target: str = text[offset:]

    # Stack to store spans of lines with greater indent than the base indent.
    temp_span_stack: list[Span] = []

    # Initialize the base indent.
    base_indent: int = 0

    if verbose:
        print("In parse_section_into_lines:")

    for idx, match in enumerate(re.finditer(r"^([^\n]*)(?:\n|$)", target, flags=re.MULTILINE)):

        # Get the matched line contents.
        line: str  = match.group(1)
        span: Span = (match.span(1)[0] + offset, match.span(1)[1] + offset)

        # Skip empty lines.
        if line.isspace() or not line:
            continue

        # Get the base indent from the first non-empty line.
        if idx == 0:
            base_indent = get_indent(line)

        # Get the indent of the current line.
        indent: int = get_indent(line)

        if verbose:
            print(f"  - {base_indent}, {indent}, '{line}'")

        # Case 1: If the indent is less than the base indent, it means the section has ended.
        if indent < base_indent:
            break

        # Case 2: If the indent is greater than the base indent, it means the multi-line entry.
        if indent > base_indent:
            temp_span_stack.append(span)

        # Case 3: If the indent is equal to the base indent.
        else:

            # If the indent is equal to the base indent and there are spans in the stack,
            # pop the spans in the stack as a single line and clear the stack.
            if temp_span_stack:
                yield (temp_span_stack[0][0], temp_span_stack[-1][-1])
                temp_span_stack.clear()

            # Yield the span of the current line.
            temp_span_stack.append(span)

    # Before the function ends, if there are spans in the stack, pop the spans in the stack.
    if temp_span_stack:
        yield (temp_span_stack[0][0], temp_span_stack[-1][-1])


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
