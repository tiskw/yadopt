"""
yadopt.helpmsg - print help message.
"""
from __future__ import annotations

# Import standard libraries.
import os
import re
import sys

# Import custom modules.
from .color       import colorize_help_message
from .declaration import ParsedDecls, OptArgDecl
from .errors      import YadOptError

# Declare published functions and variables.
__all__ = ["has_help_option_in_argv", "print_help_message_and_exit"]


def has_help_option_in_argv(argv: list[str], opt_args: list[OptArgDecl]) -> bool:
    """
    Check if the command line arguments contain a help option.

    Args:
        argv     (list[str])       : [IN] Command line arguments.
        opt_args (list[OptArgDecl]): [IN] List of optional argument declarations.

    Returns:
        (bool): True if a help option is found, False otherwise.
    """
    # Immediately return True if the "--help" option is present.
    if "--help" in argv:
        return True

    # Search for the alternative name of the "--help" option.
    help_alt: str | None = None
    for opt_arg_decl in opt_args:
        if opt_arg_decl.spec.name == "help":
            help_alt = opt_arg_decl.spec.name_alt
            break

    # If the alternative name is not found, return False.
    if help_alt is None:
        return False

    # Check if the alternative name of the "--help" option is present.
    if f"-{help_alt}" in argv:
        return True

    # Otherwise, return False.
    return False


def print_help_message_and_exit(docstr: str, parsed_decls: ParsedDecls, exit_on_help: bool = True) -> None:
    """
    Print the colorized help message and exit with a success code.

    Args:
        docstr       (str)        : [IN] Help message to be printed.
        parsed_decls (ParsedDecls): [IN] Parsed declaration contents.
        exit_on_help (bool)       : [IN] If True, exit after printing the help message.
    """
    # Print the colorized help message.
    help_message: str = generate_usage_section(docstr.strip(), parsed_decls).strip()
    print(colorize_help_message(help_message))

    # Exit with success code if "exit_on_help" is True.
    if exit_on_help:
        sys.exit(os.EX_OK)

    # Otherwise, raise a custom error.
    raise YadOptError.HelpOptionInArgv()


def generate_usage_section(docstr: str, parsed_decls: ParsedDecls, indent: int = 4, width: int = 80) -> str:
    """
    Generate the usage section of the help message automatically.

    Args:
        docstr       (str)        : [IN] Help message to be parsed.
        parsed_decls (ParsedDecls): [IN] Parsed declaration contents.
        indent       (int)        : [IN] Indentation level for the usage section.
        width        (int)        : [IN] Maximum width of the usage section.

    Returns:
        (str): Usage section of the help message.
    """
    # Do nothing if the docstring already contains a "Usage:" section.
    if re.search(r"^\s*Usage:\s*$", docstr, re.MULTILINE):
        return docstr

    # Initialize the specification part of the usage.
    usage_specs: list[str] = []

    # Create the usage specification of the optional arguments.
    for spec_opt in (opt_arg_decl.spec for opt_arg_decl in parsed_decls.optargs):

        # Initialize the option item string.
        item_opt: str = ""

        # Case 1: Short option only.
        if spec_opt.name_alt is None and spec_opt.is_short:
            item_opt += "-" + spec_opt.name

        # Case 2: Long option only.
        elif spec_opt.name_alt is None:
            item_opt += "--" + spec_opt.name

        # Case 3: Both short and long options.
        else:
            item_opt += f"-{spec_opt.name_alt}|--{spec_opt.name}"

        # Append the value placeholder if exists.
        if spec_opt.val_name is not None:
            item_opt += f" {spec_opt.val_name}"

        usage_specs.append(f"[{item_opt}]")

    # Create the usage specification of the positional arguments.
    for spec_pos in (pos_arg_decl.spec for pos_arg_decl in parsed_decls.posargs):

        # Initialize the option item string.
        item_pos: str = spec_pos.name

        # Append "..." if the positional argument is multi-valued.
        if spec_pos.is_mult:
            item_pos += "..."

        usage_specs.append(f"<{item_pos}>")

    # Compute the width of the specification part of the usage section.
    fname: str = os.path.basename(sys.argv[0])

    # Initialize the usage string with the program name.
    usage: str = "Usage:\n" + " " * indent + fname

    # Append each item in the usage specification to the usage string, wrapping lines as necessary.
    for item in usage_specs:

        # If the item fits in the current line, append it.
        if len(usage.splitlines()[-1]) + 1 + len(item) <= width:
            usage += " " + item

        # Otherwise, start a new line and append the item.
        else:
            usage += "\n" + " " * (indent + len(fname) + 1) + item

    # If no usage section is found, return an empty string.
    return usage + "\n\n" + docstr


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
