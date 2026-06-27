"""
yadopt.errors - Custom error classes for YadOpt.
"""
from __future__ import annotations

# Import standard libraries.
import difflib
import os
import textwrap
import traceback

# For type hinting.
from typing import Any

# Import custom modules.
from .color  import colorize_error_message
from .dtypes import Path, Span

# Declare published functions and variables.
__all__ = ["YadOptError", "get_candidate_message", "get_target_and_marker"]


#===================================================================================================
# Base error class
#===================================================================================================

class YadOptErrorBase(Exception):
    """
    Base class of exception in YadOpt.
    """
    EPILOGUE = textwrap.dedent("""
    If you find a bug in YadOpt, please let me know via GitHub issue.
    <https://github.com/tiskw/yadopt/issues>
    """.rstrip())

    def __init__(self, *pargs: Any, **kwargs: Any):
        """
        Constructor.
        """
        self.pargs : Any = pargs
        self.kwargs: Any = kwargs

    def __str__(self) -> str:
        """
        Returns string expression of this error.
        """
        # Get the summary of the error from the traceback.
        summary: traceback.FrameSummary = self.get_user_frame()

        # Get the location of the error.
        location = {
            "filename" : os.path.basename(summary.filename),
            "lineno"   : summary.lineno,
            "funcname" : summary.name,
            "line_text": summary.line,
        }

        # Append the location information.
        location["loc_info"] = 'File "{filename}", L. {lineno}, in {funcname}'.format(**location)

        # Returns colorized error message.
        return colorize_error_message(self.stringify(*self.pargs, **self.kwargs, **location))

    def stringify(self, *pargs: Any, **kwargs: Any) -> str:
        """
        Convert myself to a string.
        """
        # Get a docstring.
        docstr: str = textwrap.dedent(self.__doc__) if (self.__doc__ is not None) else ""

        # Returns a string expression of the error class.
        return "\n" + "-" * 80 + "\n" + docstr.format(*pargs, **kwargs).strip() + "\n" + self.EPILOGUE

    def get_user_frame(self) -> traceback.FrameSummary:
        """
        Get the frame summary of the user code where this error is raised.

        Returns:
            (traceback.FrameSummary | None): The frame summary of the user code if found, or None otherwise.
        """
        list_tbs: list[traceback.FrameSummary] = traceback.extract_tb(self.__traceback__)
        for frame in reversed(list_tbs):
            if Path(frame.filename).parent != Path(__file__).parent:
                return frame
        return list_tbs[-1]


#===================================================================================================
# Runtime errors
#===================================================================================================

class YadOptErrorCannotLoadTomllib(YadOptErrorBase):
    """
    <Error summary>
        {loc_info}
        Failed to load TOML library.

    <Details>
        YadOpt uses "tomllib", a standard library of Python, if Python >= 3.11, and
        uses "tomli" otherwise. The "tomli" library is specified as a dependency of
        YadOpt when Python <= 3.10 and will be installed automatically when users
        install YadOpt on Python<= 3.10. However, this mechanism doesn't seem to
        work well for some reason.

    <Solution>
        Please check the "tomli" library if importable if Python <= 3.10,
        and the "tomllib" otherwise.
    """

class YadOptErrorCannotGetGroup(YadOptErrorBase):
    """
    <Error summary>
        {loc_info}
        Invalid group extraction with unexpected data type.

    <Details>
        The "yadopt.get_group" is called on an unexpected type "{cls_name}".

    <Solution>
        Consider applying "yadopt.get_group" to YadOptArgs.
    """

class YadOptErrorCannotMerge(YadOptErrorBase):
    """
    <Error summary>
        {loc_info}
        Invalid data merge with unexpected data type.

    <Details>
        The merge operation '|' is supported only by YadOptArgs. However, an attempt
        was made to perform a merge on an unexpected type "{cls_name}".

    <Solution>
        Consider converting the instance of type "{cls_name}" to type YadOptArgs,
        or converting both to dictionaries and then merging them.
    """

class YadOptErrorDuplicatedName(YadOptErrorBase):
    """
    <Error summary>
        {loc_info}
        Duplicated name found in the declaration lines.

    <Details>
        The name "{name}" is duplicated in the argument declaration.

    <Solution>
        Please check the argument declaration for duplicated names.
    """

class YadOptErrorHelpOptionInArgv(YadOptErrorBase):
    """
    <Error summary>
        {loc_info}:
        The reserved option "--help" is found in the argument vector.

    <Details>
        "--help" is a reserved option that displays a help message. By default, it
        shows the message and exits the program. However, if "exit_on_help=False"
        is set in the "yadopt.parse" function, the program will not exit and will
        instead raise this error.

    <Solution>
        To avoid this error and allow the program to exit normally when "--help" is used,
        do not specify "exit_on_help=False" in the "yadopt.parse" function.
    """


class YadOptErrorInvalidBoolValue(YadOptErrorBase):
    """
    <Error summary>
        {loc_info}
        Invalid boolean value.

    <Details>
        The value "{value}" is not a valid boolean value. Acceptable boolean values are:
        "true", "false", "yes", "no", "on", "off", "1", "0", or their uppercases.

    <Solution>
        Please specify a valid boolean value.
    """

class YadOptErrorInvalidFileFormat(YadOptErrorBase):
    """
    <Error summary>
        {loc_info}
        Invalid file format.

    <Details>
        The "yadopt.save" and "yadopt.load" functions does not support "{suffix}" format.

    <Solution>
        Please specify the supported file format, for example, ".toml" or ".json".
    """

class YadOptErrorInvalidHelpOption(YadOptErrorBase):
    """
    <Error summary>
        {loc_info}
        Invalid help option.

    <Details>
        The "--help" option is a reserved option for displaying a help message
        and does not take a value. It cannot be used as a regular option.

    <Solution>
        Please modify the "--help" option to display a help message without taking
        a value, or simply do not explicitly declare the "--help" option.
    """

class YadOptErrorInvalidSourceType(YadOptErrorBase):
    """
    <Error summary>
        {loc_info}
        Invalid source type.

    <Details>
        The first argument of "yadopt.parse" function should be either a string
        instance or a dataclass type, but "{source_type}" is given.

    <Solution>
        Please specify a valid source type. See the quick example in the README for details.
    """

class YadOptErrorInvalidTomlFile(YadOptErrorBase):
    """
    <Error summary>
        {loc_info}
        Invalid TOML file.

    <Details>
        The given TOML file is invalid: {reason}

    <Solution>
        Please check the TOML file for errors.
    """

class YadOptErrorInvalidTypeName(YadOptErrorBase):
    """
    <Error summary>
        {loc_info}
        Invalid type name '{type_name}'.

    <Details>
        Type name '{type_name}' is invalid. Acceptable type names are:
        "int", "integer", "flt", "float", "str", "string", "path",
        or their uppercases.

    <Solution>
      Modify the type name.
    """

class YadOptErrorMissingArgument(YadOptErrorBase):
    """
    <Error summary>
        {loc_info}: The necessary arguments are missing.

    <Details>
        The following positional arguments are missing: {missing_args}

    <Solution>
        Please give the above positional arguments in the user input.
    """

class YadOptErrorNoOptionValue(YadOptErrorBase):
    """
    <Error summary>
        {loc_info}: No value was given for an option that requires a value.

    <Details>
        The option '{opt_name}' requires a value, but not given.

    <Solution>
        Please give a value to the option '{opt_name}'.
    """

class YadOptErrorTooManyArgument(YadOptErrorBase):
    """
    <Error summary>
        {loc_info}: Too many arguments were given.

    <Details>
        Unrecognized extra positional arguments were given: {extra_args}

    <Solution>
        Please remove the above extra positional arguments from the user input.
    """

class YadOptErrorUnknownOption(YadOptErrorBase):
    """
    <Error summary>
        {loc_info}: Unknown option detected in the argument vector.

    <Details>
        Unknown option "{opt_name}" detected in the user input.

    <Solution>
        Please check the option name "{opt_name}" for typos.
        {candidate}
    """


#===================================================================================================
# Errors on analysis phase
#===================================================================================================

class YadOptErrorExtraArgsInPosArgDecl(YadOptErrorBase):
    """
    <Error summary>
        {loc_info}: Extra token is found in positional argument declaration.

    <Details>
        {target}
        {marker}

    <Hint>
        Remove extra tokens from the positional argument name declaration.
        Note that a description starts from a two or more spaces.
    """

class YadOptErrorNoArgNameInPosArgDecl(YadOptErrorBase):
    """
    <Error summary>
        {loc_info}: No argument name is found in positional argument declaration.

    <Details>
        {target}
        {marker}

    <Solution>
        Please specify an argument name in the positional argument declaration.
    """

class YadOptErrorInvalidArgNameInPosArgDecl(YadOptErrorBase):
    """
    <Error summary>
        {loc_info}
        Invalid argument name in positional argument declaration.

    <Details>
        {target}
        {marker}

    <Solution>
        Please modify the argument name "{arg_name}" to a valid identifier.
        Note that digit-starting names are not allowed as positional argument names.
    """

class YadOptErrorMultiEllipsisInPosArgDecl(YadOptErrorBase):
    """
    <Error summary>
        {loc_info}: Multiple ellipses are found in positional argument declaration.

    <Details>
        {target}
        {marker}

    <Solution>
        Please specify at most one ellipsis in the positional argument declaration.
    """

class YadOptErrorInvalidEllipsisInPosArgDecl(YadOptErrorBase):
    """
    <Error summary>
        {loc_info}: Invalid ellipsis in positional argument declaration.

    <Details>
        {target}
        {marker}

    <Solution>
        Please specify the ellipsis "..." at the end of the positional argument declaration.
    """

class YadOptErrorUnexpectedTokenInPosArgDecl(YadOptErrorBase):
    """
    <Error summary>
        {loc_info}: Unexpected token is found in positional argument declaration.

    <Details>
        {target}
        {marker}

    <Solution>
        Please remove the unexpected token "{token}" from the positional argument declaration.
    """

class YadOptErrorUnknownErrorInPosArgDecl(YadOptErrorBase):
    """
    <Error summary>
        {loc_info}
        Unknown error is found in positional argument declaration.

    <Details>
        {target}
        {marker}

    <Solution>
        Please check the positional argument declaration for errors.
    """

class YadOptErrorNoOptNameInOptArgDecl(YadOptErrorBase):
    """
    <Error summary>
        {loc_info}
        No option name is found in optional argument declaration.

    <Details>
        {target}
        {marker}

    <Solution>
        Please specify an option name in the optional argument declaration.
    """

class YadOptErrorInvalidCommaPosInOptArgDecl(YadOptErrorBase):
    """
    <Error summary>
        {loc_info}
        Invalid comma position is found in optional argument declaration.

    <Details>
        {target}
        {marker}

    <Solution>
        Please check the comma position in the optional argument declaration.
    """

class YadOptErrorInvalidCommaUsageInOptArgDecl(YadOptErrorBase):
    """
    <Error summary>
        {loc_info}
        Invalid comma usage is found in optional argument declaration.

    <Details>
        {target}
        {marker}

    <Solution>
        Please check the comma usage in the optional argument declaration.
    """

class YadOptErrorInvalidEqualUsageInOptArgDecl(YadOptErrorBase):
    """
    <Error summary>
        {loc_info}
        Invalid equal sign usage is found in optional argument declaration.

    <Details>
        {target}
        {marker}

    <Solution>
        Please check the equal sign usage in the optional argument declaration.
    """

class YadOptErrorPosArgAfterMult(YadOptErrorBase):
    """
    <Error summary>
        {loc_info}
        Positional argument is declared after a multiple positional argument.

    <Solution>
        The positional argunment "{name}" is not achievable because it is
        declared after a multiple positional argument. Please declare the positional
        argument before the multiple positional argument.
    """

class YadOptErrorUnexpectedTokenInOptArgDecl(YadOptErrorBase):
    """
    <Error summary>
        {loc_info}
        Unexpected token is found in optional argument declaration.

    <Details>
        {target}
        {marker}

    <Solution>
        Please remove the unexpected token "{token}" from the optional argument declaration.
    """

class YadOptErrorUnknownErrorInOptArgDecl(YadOptErrorBase):
    """
    <Error summary>
        {loc_info}
        Unknown error is found in optional argument declaration.

    <Details>
        {target}
        {marker}

    <Solution>
        Please check the optional argument declaration for errors.
    """


#===================================================================================================
# Wrapper class
#===================================================================================================

class YadOptError:
    """
    General Error class for YadOpt.
    """
    # Runtime errors.
    CannotLoadTomllib = YadOptErrorCannotLoadTomllib
    CannotGetGroup    = YadOptErrorCannotGetGroup
    CannotMerge       = YadOptErrorCannotMerge
    DuplicatedName    = YadOptErrorDuplicatedName
    HelpOptionInArgv  = YadOptErrorHelpOptionInArgv
    InvalidBoolValue  = YadOptErrorInvalidBoolValue
    InvalidFileFormat = YadOptErrorInvalidFileFormat
    InvalidHelpOption = YadOptErrorInvalidHelpOption
    InvalidSourceType = YadOptErrorInvalidSourceType
    InvalidTomlFile   = YadOptErrorInvalidTomlFile
    InvalidTypeName   = YadOptErrorInvalidTypeName
    MissingArgument   = YadOptErrorMissingArgument
    NoOptionValue     = YadOptErrorNoOptionValue
    TooManyArgument   = YadOptErrorTooManyArgument
    UnknownOption     = YadOptErrorUnknownOption

    # Errors on analysis phase (positional argument declaration).
    ExtraArgsInPosArgDecl       = YadOptErrorExtraArgsInPosArgDecl
    NoArgNameInPosArgDecl       = YadOptErrorNoArgNameInPosArgDecl
    InvalidArgNameInPosArgDecl  = YadOptErrorInvalidArgNameInPosArgDecl
    MultiEllipsisInPosArgDecl   = YadOptErrorMultiEllipsisInPosArgDecl
    InvalidEllipsisInPosArgDecl = YadOptErrorInvalidEllipsisInPosArgDecl
    PosArgAfterMult             = YadOptErrorPosArgAfterMult
    UnexpectedTokenInPosArgDecl = YadOptErrorUnexpectedTokenInPosArgDecl
    UnknownErrorInPosArgDecl    = YadOptErrorUnknownErrorInPosArgDecl

    # Errors on analysis phase (optional argument declaration).
    NoOptNameInOptArgDecl         = YadOptErrorNoOptNameInOptArgDecl
    InvalidCommaPosInOptArgDecl   = YadOptErrorInvalidCommaPosInOptArgDecl
    InvalidCommaUsageInOptArgDecl = YadOptErrorInvalidCommaUsageInOptArgDecl
    InvalidEqualUsageInOptArgDecl = YadOptErrorInvalidEqualUsageInOptArgDecl
    UnexpectedTokenInOptArgDecl   = YadOptErrorUnexpectedTokenInOptArgDecl
    UnknownErrorInOptArgDecl      = YadOptErrorUnknownErrorInOptArgDecl


#===================================================================================================
# Private classes and functions
#===================================================================================================

def get_candidate_message(target: str, texts: list[str]) -> str:
    """
    Get the candidate message for the target string from the given string list.

    Args:
        target (str)      : [IN] Target string.
        texts  (list[str]): [IN] Candidate strings.

    Returns:
        (str): Candidate message if the candidate string is found, or empty string otherwise.

    Examples:
        >>> get_candidate_message("hlep", [])
        ''
        >>> get_candidate_message("verion", ["help", "version", "verbose"])
        'Do you mean "version"?'
        >>> get_candidate_message("verbse", ["help", "version", "verbose"])
        'Do you mean "verbose"?'
        >>> get_candidate_message("hlep", ["help", "version", "verbose"])
        'Do you mean "help"?'
    """
    if not texts:
        return ""

    return 'Do you mean "' + difflib.get_close_matches(target, texts, n=1, cutoff=0.0)[0] + '"?'


def get_target_and_marker(text: str, span: Span) -> dict[str, str]:
    """
    Get the target line and the marker to highlight it.

    Args:
        text (str) : [IN] Original text.
        span (Span): [IN] Span of the target position.

    Examples:
        >>> get_target_and_marker("this is a pen", (5, 7))
        {'target': 'L.1: this is a pen', 'marker': '          ^^      '}
        >>> get_target_and_marker("Arguments:\\n    arg  description\\n    -l   description", (15, 18))
        {'target': 'L.2:     arg  description', 'marker': '         ^^^             '}
    """
    # Get the position of the beginning and the end of the line that contains the target span.
    pos_line_bgn: int = text.rfind("\n", 0, span[0])
    pos_line_end: int = text.find("\n", span[1])

    # Adjust the positions to be within the text.
    pos_line_bgn = pos_line_bgn + 1 if (pos_line_bgn >= 0) else 0
    pos_line_end = pos_line_end     if (pos_line_end >= 0) else len(text)

    # Get the target line.
    target: str = text[pos_line_bgn:pos_line_end]

    # Get the marker to highlight the target span.
    marker: str = " " * (span[0] - pos_line_bgn) + "^" * (span[1] - span[0]) + " " * (pos_line_end - span[1])

    # Get the line number of the target line.
    lineno: int = 1 + text[:span[0]].count("\n")
    header: str = "L." + str(lineno) + ": "

    return {"target": header + target, "marker": " " * len(header) + marker}


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
