"""
yadopt.section - section parser for YadOpt.
"""
from __future__ import annotations

# Import standard libraries.
import dataclasses
import re

# For type hinting.
from typing import Generator

# Import custom modules.
from .dtypes import Span

# Declare published functions and variables.
__all__ = ["DeclarationContents", "SectionLineSplitter"]


@dataclasses.dataclass(frozen=True)
class DeclarationContents:
    """
    Data class for declaration lines of target sections in the docstring.
    """
    lines: list[tuple[str, Span]]

    def validate(self, len_docstr: int) -> None:
        """
        Run extra validation checks. This function is called only when running tests.
        This is a post-condition assertion in the context of DbC methodology.

        Args:
            len_docstr (int): [IN] Length of the original docstring (required for span validation).
        """
        spans: list[Span] = [span         for _, span in self.lines]
        names: list[str]  = [name.lower() for name, _ in self.lines]

        # Assertion 1: All spans are within the bounds of the docstring.
        for span in spans:
            assert span[0] >= 0,          f"Negative span: {span}"
            assert span[1] >= 0,          f"Negative span: {span}"
            assert span[0] < span[1],     f"Invalid span: {span}"
            assert span[1] <= len_docstr, f"Span {span} is out of bounds for docstr of length {len_docstr}"

        # Assertion 2: No overlapping spans in the declaration lines.
        for span1, span2 in zip(spans[:-1], spans[1:]):
            assert span1[1] <= span2[0], f"Overlapping spans: {span1} and {span2}"

        # Assertion 3: All section names are non-empty and seem like valid section names.
        for name in names:
            assert ("arguments" in name) or ("options" in name), f"Invalid section name: {name}"


class SectionLineSplitter:
    """
    Split lines in the target sections.

    Examples:
        >>> sec_line_splitter = SectionLineSplitter(docstr='''
        ... Usage:
        ...     sample.py [--help]
        ... 
        ... Options:
        ...     --multiline        First line.
        ...                        Second line.
        ...     -h, --help Show    Show this message and exit.
        ... ''')
        >>> sec_line_splitter.parse().lines
        [('Options', (41, 111)), ('Options', (112, 162))]
    """
    def __init__(self, docstr: str, verbose: bool = False) -> None:
        """
        Constructor.

        Args:
            docstr  (str) : [IN] Docstring to be parsed.
            verbose (bool): [IN] Displays verbose messages that are useful for debugging.
        """
        self.docstr : str  = docstr
        self.verbose: bool = verbose

        # Compile a regular expression pattern for section header matching.
        self.pattern_section: re.Pattern = re.compile(r"""
            ^\s*(?:               # Ignore whitespaces at the beginning.
            (?P<colon>.*):        # Colon-style section name. (e.g. "Arguments:")
            |                     # OR operator for connecting colon and bracket style.
            \[(?P<bracket>.*)\]   # Bracket-style section name. (e.g. "[Arguments]")
            )\s*$                 # Ignore whitespaces at the end.
        """, flags=re.MULTILINE|re.IGNORECASE|re.VERBOSE)

        # Compile a regular expression pattern for line matching.
        self.pattern_line: re.Pattern = re.compile(r"""
            ^       # Beginning of the line.
            (.*?)   # Line contents.
            $       # End of the line.
        """, flags=re.MULTILINE|re.VERBOSE)

    def parse(self) -> DeclarationContents:
        """
        Parse the target sections in the docstring and yields the spans of each line with the section name.

        Returns:
            (DeclarationContents): Declaration lines of target sections in the docstring.
        """
        # Initialize the list to store the section name and span of each line.
        lines: list[tuple[str, Span]] = []

        for match in self.pattern_section.finditer(self.docstr):

            # Get the section name.
            section_name: str = match.group("colon") if match.group("colon") else match.group("bracket")

            # Skip if the section name is out of target.
            if not self.is_target_section(section_name):
                continue

            # Get the start index of the section in the original docstring.
            section_start: int = match.span(0)[1]

            # Parse the section into lines and yield the spans of each line with the section name.
            for span in self.split_section_into_lines(section_start + 1):
                lines.append((section_name, span))

        return DeclarationContents(lines=lines)

    def split_section_into_lines(self, offset: int) -> Generator[Span, None, None]:
        """
        Split the given section into lines and yields the spans of each line.

        Args:
            offset (int): [IN] Start index of the section in the original text.

        Yields:
            (Span): Span of each line in the original text.
        """
        # Get the section text to parse.
        target: str = self.docstr[offset:]

        # Stack to store spans of lines with greater indent than the base indent.
        temp_span_stack: list[Span] = []

        # Initialize the base indent.
        base_indent: int = 0

        if self.verbose:
            print("In parse_section_into_lines:")

        for idx, match in enumerate(self.pattern_line.finditer(target)):

            # Get the matched line contents.
            line: str  = match.group(1)
            span: Span = (match.span(1)[0] + offset, match.span(1)[1] + offset)

            # Skip empty lines.
            if line.isspace() or not line:
                continue

            # Get the base indent from the first non-empty line.
            if idx == 0:
                base_indent = self.get_indent(line)

            # Get the indent of the current line.
            indent: int = self.get_indent(line)

            if self.verbose:
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

    @staticmethod
    def get_indent(text: str, tab_width: int = 4) -> int:
        """
        Get indentation depth of the given text.

        Args:
            text      (str): [IN] Input test.
            tab_width (int): [IN] Width of a tab character in whitespaces.

        Returns:
            (int): Depth of indentation.

        Examples:
            >>> SectionLineSplitter.get_indent('   text')
            3
        """
        depth_indent_before_replace_tag: int = len(text) - len(text.lstrip())
        return len(text[:depth_indent_before_replace_tag].replace("\t", " " * tab_width))

    @staticmethod
    def is_target_section(section_name: str) -> bool:
        """
        Returns true if the given section name is a target section.

        Args:
            section_name (str): [IN] Section name to check.

        Returns:
            (bool): True if the section name is a target section, False otherwise.

        Examples:
            >>> SectionLineSplitter.is_target_section('Arguments and Options')
            True
            >>> SectionLineSplitter.is_target_section('Other Section')
            False
        """
        section_name_lower: str = section_name.lower()
        if section_name_lower in ("arguments", "options"):
            return True
        if any(section_name_lower.startswith(keyword) for keyword in ("arguments ", "options ")):
            return True
        if any(section_name_lower.endswith(keyword) for keyword in (" arguments", " options")):
            return True
        return False


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
