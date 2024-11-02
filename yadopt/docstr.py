"""
Docstring parser.
"""

# Declare published functions and variables.
__all__ = ["parse_docstr", "DocStrInfo"]

# Import standard libraries.
import dataclasses
import re

# Import custom modules.
from .argopt import parse_argopt, ArgEntry, OptEntry
from .usage  import parse_usage, UsageEntry
from .utils  import match_and_get


@dataclasses.dataclass
class DocStrInfo:
    """
    Parse result of docstring.
    """
    usages: list[UsageEntry]  # Information of usages.
    args  : list[ArgEntry]    # Information of argument.
    opts  : list[OptEntry]    # Information of option.


def split_section(docstr: str) -> tuple[str, list]:
    """
    Parse docstring and split it to sections.

    Args:
        docstr (str): Input docstring.

    Returns:
        (tuple): A tuple of section name and section contents.
    """
    section_patterns_and_indices = [
        # regular expression, section_name_index, None
        # --------------------------------------------
        (r"([\w ]+):\s*$",       (1,), None),  # SectionName:
        (r"\[([\w ]+)\]\s*$",    (1,), None),  # [SectionName]
    ]

    sec_name, sec_contents = None, []

    for line in docstr.split("\n"):

        # Ignore empty line.
        if len(line.strip()) == 0:
            continue

        # Try to match the section name patterns.
        matched_sec_name, *_ = match_and_get(line, section_patterns_and_indices)

        # Case 1: New section found.
        if matched_sec_name is not None:

            # Returns previous section contents (if exists).
            if sec_name and sec_contents:
                yield (sec_name, sec_contents)

            # Initialize section contents.
            sec_name, sec_contents = matched_sec_name, []

        # Case 2: If not the beginning of section, try to match as section contents.
        elif re.match(r'\s', line):
            sec_contents.append(line.rstrip())

    if sec_contents:
        yield (sec_name, sec_contents)


def parse_docstr(docstr: str):
    """
    Parse the given docstring and create a data class.

    Args:
        docstr (str) : The target docstring.
    """
    # Initialize output variable.
    dsinfo = DocStrInfo([], [], [])
    usages = ["Usage:"]

    # Parse each section.
    for sec_name, sec_contents in split_section(docstr):

        # Process the usage section.
        if sec_name.lower().endswith("usage"):

            # Store the parsed usage to the output variable.
            dsinfo.usages += [parse_usage(line) for line in sec_contents]

            # Store the raw usage strings.
            usages += sec_contents

        # Process the other sections.
        else:

            # Parse section lines to ArgInfo/OptInfo.
            items = [parse_argopt(line) for line in sec_contents]

            # Append to docinfo arguments and options.
            dsinfo.args += [item for item in items if isinstance(item, ArgEntry)]
            dsinfo.opts += [item for item in items if isinstance(item, OptEntry)]

    # Adjust data type and default values. If n_args == 0, then the data type
    # and defualt value should be bool and False, respectively.
    for item in dsinfo.opts:
        if item.n_args == 0:
            item.data_type = bool
            item.default   = False

    return (dsinfo, "\n".join(usages))


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
