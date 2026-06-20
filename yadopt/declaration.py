"""
yadopt.declaration - declaration line parser for YadOpt.
"""
from __future__ import annotations

# Import standard libraries.
import dataclasses
import itertools
import textwrap
import pprint

# Import custom modules.
from .description import DescriptionParser, ParsedDesc
from .errors      import YadOptError
from .optarg      import OptArgParser, OptSpec
from .posarg      import PosArgParser, PosSpec
from .dtypes      import Span
from .section     import DeclarationContents

# Declare published functions and variables.
__all__ = ["PosArgDecl", "OptArgDecl", "ParsedDecls", "DeclarationContentsParser"]


@dataclasses.dataclass(frozen=True)
class PosArgDecl:
    """
    Parsed result of positional argument declaration in docstring.
    """
    spec : PosSpec     # Parsed positional argument specification.
    desc : ParsedDesc  # Parsed description of this argument.
    group: str         # Group name of this entry.


@dataclasses.dataclass(frozen=True)
class OptArgDecl:
    """
    Parsed result of positional argument declaration in docstring.
    """
    spec : OptSpec     # Parsed positional argument specification.
    desc : ParsedDesc  # Parsed description of this argument.
    group: str         # Group name of this entry.


@dataclasses.dataclass(frozen=True)
class ParsedDecls:
    """
    Parsed result of docstring.
    """
    posargs: list[PosArgDecl]   # Positional argument entries.
    optargs: list[OptArgDecl]   # Optional argument entries.

    def __str__(self) -> str:
        text = self.__class__.__name__ + ":\n"
        for idx, item in enumerate(itertools.chain(self.posargs, self.optargs)):
            text += f" |-({idx:02d}) " + textwrap.indent(pprint.pformat(item), " |      ")[8:] + "\n"
        return text.strip()

    def __post_init__(self) -> None:
        """
        Run minimum validation checks.
        This is a post-condition assertion in the context of DbC methodology.
        """
        # Check for duplicate argument names.
        arg_names: set[str] = set()
        for arg_decl in self.posargs + self.optargs:

            # Get the argument specification and its name.
            spec: PosSpec | OptSpec = arg_decl.spec
            name: str = arg_decl.spec.name.replace("-", "_").replace(".", "_")

            # Check for duplicate names in the parsed entries.
            if name in arg_names:
                raise YadOptError.DuplicatedName(name=spec.name)
            if isinstance(spec, OptSpec) and spec.name_alt is not None:
                name_alt: str = spec.name_alt.replace("-", "_").replace(".", "_")
                if spec.name_alt in arg_names:
                    raise YadOptError.DuplicatedName(name=spec.name_alt)

            # Add the names of the current entry to the set of seen names.
            arg_names.add(name)
            if isinstance(spec, OptSpec) and spec.name_alt is not None:
                arg_names.add(name_alt)

        # Check the existance of positional argument after the multiple positional argument.
        has_mult_pos_arg: bool = False
        for pos_arg_decl in self.posargs:

            # Raise an error if there is a positional argument after the multiple positional argument,
            # since it is ambiguous to parse the command line arguments in this case.
            if has_mult_pos_arg:
                raise YadOptError.PosArgAfterMult(name=pos_arg_decl.spec.name)

            # Update the multiple argument flag.
            has_mult_pos_arg |= pos_arg_decl.spec.is_mult

    def validate(self) -> None:
        """
        Run extra validation checks. This function is called only when running tests.
        This is a post-condition assertion in the context of DbC methodology.
        """
        # Data type checks.
        assert isinstance(self.posargs, list)
        assert isinstance(self.optargs, list)
        for pos_arg_decl in self.posargs:
            assert isinstance(pos_arg_decl, PosArgDecl)
        for opt_arg_decl in self.optargs:
            assert isinstance(opt_arg_decl, OptArgDecl)

        # Call all validation functions of the contained entries.
        for arg_decl in self.posargs + self.optargs:
            arg_decl.spec.validate()
            arg_decl.desc.validate()


class DeclarationContentsParser:
    """
    Parser for declaration contents in the docstring.
    This class is very simple, just instancuate the "DeclarationLineParser" class,
    call it for each declaration line, and collect the results.
    """
    def __init__(self, docstr: str, decl_conts: DeclarationContents, verbose: bool) -> None:
        """
        Constructor.

        Args:
            docstr     (str)                : [IN] Original docstring to be parsed.
            decl_conts (DeclarationContents): [IN] Declaration contents to be parsed.
            verbose    (bool)               : [IN] Displays verbose messages that are useful for debugging.
        """
        self.docstr     = docstr
        self.decl_conts = decl_conts
        self.verbose    = verbose

    def parse(self) -> ParsedDecls:
        """
        Parse the declaration contents and return the parsed result.
        """
        # Disorganized list of entries, where both positional and optional arguments are mixed together.
        entries: list[tuple[PosSpec | OptSpec, ParsedDesc, str]] = []

        for section_name, span_decl in self.decl_conts.lines:
            (spec, desc) = DeclarationLineParser(self.docstr, span_decl, self.verbose).parse()
            entries.append((spec, desc, section_name))

        return ParsedDecls(
            posargs=[PosArgDecl(spec, desc, grp) for spec, desc, grp in entries if isinstance(spec, PosSpec)],
            optargs=[OptArgDecl(spec, desc, grp) for spec, desc, grp in entries if isinstance(spec, OptSpec)],
        )


class DeclarationLineParser:
    """
    Parser for declaration lines in the docstring.
    """
    def __init__(self, docstr: str, span: Span, verbose: bool) -> None:
        """
        Constructor.

        Args:
            docstr  (str) : [IN] Original docstring to be parsed.
            span    (Span): [IN] Span of the declaration line in the original docstring.
            verbose (bool): [IN] Displays verbose messages that are useful for debugging.
        """
        self.docstr  = docstr
        self.span    = span
        self.verbose = verbose

    def parse(self) -> tuple[PosSpec | OptSpec, ParsedDesc]:
        """
        Parse the definition line of an argument or option in the docstring and return the parsed result.

        Returns:
            (PosEntry | OptEntry): Parsed result.
        """
        # Split the declaration line into the declaration part and the description part.
        (span_spec, span_desc) = self.split_after_indent(self.docstr, self.span, "  ", self.verbose)

        # Option declaration line starts with a hyphen.
        is_opt: bool = self.docstr[span_spec[0]:span_spec[1]].strip().startswith("-")

        # Parse the declaration line
        spec: PosSpec | OptSpec = (OptArgParser(self.docstr, span_spec, self.verbose).parse()
                                   if is_opt else
                                   PosArgParser(self.docstr, span_spec, self.verbose).parse())

        # Parse the description part of the declaration line.
        desc: ParsedDesc = DescriptionParser(self.docstr, span_desc, self.verbose).parse()

        return (spec, desc)

    @staticmethod
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
            >>> DeclarationLineParser.split_after_indent("    -a int", (0, 10), "  ", False)
            ((0, 10), (10, 10))
            >>> DeclarationLineParser.split_after_indent("    -a int  Description.", (0, 24), "  ", False)
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
