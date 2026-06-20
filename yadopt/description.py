"""
yadopt.description - description parser for the declaration line in the docstring.
"""
from __future__ import annotations

# Import standard libraries.
import dataclasses
import re

# Import custom modules.
from .dtypes   import Span, DTYPE_NAMES
from .errors   import YadOptError

# Declare published functions and variables.
__all__ = ["ParsedDesc", "DescriptionParser"]


@dataclasses.dataclass(frozen=True)
class ParsedDesc:
    """
    Parsed result of the description part in the declaration line of the docstring.
    """
    desc   : str         # Description text with type and default value removed.
    type_dh: str | None  # Data type written in the description head.
    default: str | None  # Default value if it exists, otherwise None.

    def __post_init__(self) -> None:
        """
        Run minimum validation checks.
        This is a post-condition assertion in the context of DbC methodology.
        """
        # Validation of the type name in the description head.
        if self.type_dh is not None:
            if self.type_dh.lower() not in DTYPE_NAMES:
                raise YadOptError.InvalidTypeName(type_name=self.type_dh)

    def validate(self) -> None:
        """
        Run extra validation checks. This function is called only when running tests.
        This is a post-condition assertion in the context of DbC methodology.
        """


class DescriptionParser:
    """
    Parser for the description part of the declaration line in the docstring.
    """
    # Regular expression pattern to extract type description, description text, and default value.
    pattern_desc: re.Pattern = re.compile(r"""^
    \s*                              # Leading whitespace.
    (?:\((\w+)\))?                   # Optional type description in parentheses.
    \s*                              # Optional whitespace after type description.
    (.+?)                            # Description text (non-greedy).
    (?:\s+\[default:\s*(.+?)\s*\])?  # Optional default value in the format "[default: ...]".
    \s*                              # Trailing whitespace.
    $""", flags=re.VERBOSE)

    def __init__(self, docstr: str, span: Span, verbose: bool) -> None:
        """
        Constructor.

        Args:
            docstr  (str) : [IN] Original docstring to be parsed.
            span    (Span): [IN] Span of the description part in the original docstring
            verbose (bool): [IN] Displays verbose messages that are useful for debugging.
        """
        self.docstr  = docstr
        self.span    = span
        self.verbose = verbose

    def parse(self) -> ParsedDesc:
        """
        Parse the description part of the declaration line.

        Returns:
            description (str)     : Description text with type and default value removed.
            type_dsc    (str|None): Type description if it exists, otherwise None.
            default     (str|None): Default value if it exists, otherwise None.
        """
        # Get the target description text from the original docstring using the given span.
        target: str = self.docstr[self.span[0]:self.span[1]]

        # If the description is multi-line, join the lines.
        if "\n" in target:
            target = " ".join(line.strip() for line in target.split("\n"))

        if self.verbose:
            print("In parse_description:")
            print("  |- description span =", self.span)
            print("  |- original description = '" + self.docstr[self.span[0]:self.span[1]] + "'")
            print("  |- joined description = '" + target + "'")

        # Search for the default value in the description.
        match: re.Match | None = self.pattern_desc.match(target)

        # If the match is successful, extract the description, type, and default value.
        if match is not None:
            return ParsedDesc(
                desc    = match.group(2).strip() if match.group(2) is not None else "",
                type_dh = match.group(1)         if match.group(1) is not None else None,
                default = match.group(3)         if match.group(3) is not None else None,
            )

        # If it failed to match, it means something is wrong with the description.
        self.analyze_and_raise()
        raise RuntimeError("Unreachable code reached in DescriptionParser.parse()")

    def analyze_and_raise(self) -> None:
        """
        Analyze the erroneous description and raise an error instance.
        """
        raise NotImplementedError("Description analysis is not implemented yet.")


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
