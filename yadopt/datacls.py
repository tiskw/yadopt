"""
yadopt.datacls - converter of a dataclass to a help message string.
"""
from __future__ import annotations

# Import standard libraries.
import ast
import dataclasses
import inspect
import io
import tokenize

# For type hinting.
from typing import Iterator

# Declare published functions and variables.
__all__ = ["dataclass_to_help_message"]


def dataclass_to_help_message(cls: type, indent: int = 4) -> str:
    """
    Convert a dataclass to a help message string.

    Args:
        cls    (type): The data class type.
        indent (int) : The depth of indentation for the help message.

    Returns:
        (str): The help message string.
    """
    assert dataclasses.is_dataclass(cls), f"{cls.__name__} is not a dataclass."

    # Get the source code of the dataclass.
    source: str = inspect.getsource(cls)

    # Parse the source code into an AST and visit it to extract field information.
    visitor = DataclassVisitor()
    visitor.visit(ast.parse(source))

    # Get the source code lines for easier access to comments.
    lines_source: list[str] = source.splitlines()

    # Extract comments for each field from the source code.
    for field in visitor.fields:
        line: str = lines_source[field.endline - 1]
        for token in tokenize.generate_tokens(io.StringIO(line).readline):
            if token.type == tokenize.COMMENT:
                field.comment = token.string.lstrip("#").strip()

    # Separate fields into positional and optional arguments (based on default values).
    pos_args: Iterator[DataClassFieldInfo] = filter(lambda field: field.default is None,     visitor.fields)
    opt_args: Iterator[DataClassFieldInfo] = filter(lambda field: field.default is not None, visitor.fields)

    # Generate the help message for positional and optional arguments.
    help_message  = align_help_message(list(pos_args), False, indent)
    help_message += "\n\n"
    help_message += align_help_message(list(opt_args), True,  indent)
    return help_message


@dataclasses.dataclass
class DataClassFieldInfo:
    """
    Information about a dataclass field.
    """
    name   : str        = ""
    dtype  : str        = ""
    default: str | None = None
    endline: int        = -1
    comment: str        = ""


class DataclassVisitor(ast.NodeVisitor):
    """
    AST visitor for dataclass definitions
    """
    def __init__(self) -> None:
        """
        Constructor.
        """
        # Initialize the list of fields.
        self.fields: list[DataClassFieldInfo] = []

    def visit_ClassDef(self, node) -> None:
        """
        Visit a class definition node.
        """
        # Loop for each item in the dataclass body.
        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):

                # Extract field information from the annotated assignment.
                field: DataClassFieldInfo = DataClassFieldInfo(
                    name    = item.target.id,
                    dtype   = ast.unparse(item.annotation),
                    default = ast.unparse(item.value) if item.value else None,
                    endline = item.end_lineno if item.end_lineno is not None else -1,
                    comment = "",
                )

                # Normalize the data type for path-like fields.
                if field.dtype.lower() in ("path", "yadopt.path", "pathlib.path"):
                    field.dtype = "Path"

                # Append the field information to the list of fields.
                self.fields.append(field)


def align_help_message(fields: list[DataClassFieldInfo], is_opt: bool, indent: int) -> str:
    """
    Align the help message for a list of dataclass fields.

    Args:
        fields (list[DataClassFieldInfo]): List of dataclass field information.
        is_opt (bool)                    : True if the fields are optional arguments, False if positional.
        indent (int)                     : The depth of indentation for the help message.

    Returns:
        (str): The aligned help message string.
    """
    # Create a list of tuples (argument name, data type, description, default value).
    help_message_structure: list[tuple[str, str, str, str]] = []

    for field in fields:

        # Case 1: Optional argument without a value.
        if is_opt and field.dtype.lower() == "bool" and field.default is not None and field.default.lower() == "false":
            help_message_structure.append((
                f"--{field.name}",
                f"({field.dtype})",
                field.comment,
                "[default: False]",
            ))

        # Case 2: Other optional argument.
        elif is_opt:
            help_message_structure.append((
                f"--{field.name} VALUE",
                f"({field.dtype})",
                field.comment,
                "" if field.default is None else f"[default: {field.default}]",
            ))

        # Case 3: Positional argument.
        else:
            help_message_structure.append((
                field.name,
                f"({field.dtype})",
                field.comment,
                "" if field.default is None else f"[default: {field.default}]",
            ))

    # Calculate the maximum lengths of the argument name, data type, and description for alignment.
    max_length_spec: int = max(len(spec)  for spec, dtype, desc, _ in help_message_structure)
    max_length_type: int = max(len(dtype) for spec, dtype, desc, _ in help_message_structure)
    max_length_desc: int = max(len(desc)  for spec, dtype, desc, _ in help_message_structure)

    # Initialize the output help message with the appropriate header.
    help_message = "Options:\n" if is_opt else "Arguments:\n"

    for spec, dtype, desc, default in help_message_structure:

        # Create a line of the help message.
        line  = " " * indent
        line += spec.ljust(max_length_spec)  + " " * 3
        line += dtype.ljust(max_length_type) + " " * 1
        line += desc.ljust(max_length_desc)  + " " * 1
        line += default

        # Append the line to the help message.
        help_message += line.rstrip() + "\n"

    return help_message.strip()


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
