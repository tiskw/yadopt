"""
Docstring parser.
"""

# Declare published functions and variables.
__all__ = ["parse_arg", "parse_opt"]

# Import standard libraries.
import re

# Import custom modules.
from .dtypes   import ArgEntry, OptEntry
from .errors   import YadOptError
from .hints    import DTYPE_HINTS
from .matchers import match_arg, match_opt
from .utils    import get_default


def parse_arg(line: str) -> ArgEntry | OptEntry | None:
    """
    Parse an entry of argument section.
    Now `parse_opt` can manage both arguments and options.

    Examples:
        >>> parse_arg("  arg1 msg")
        ArgEntry(name='arg1', dtype_str='unknown', desc='msg', default=None)
        >>> parse_arg("  arg1  (INT) msg  [default: 10]")
        ArgEntry(name='arg1', dtype_str='int', desc='msg', default='10')
    """
    return parse_opt(line)


def parse_opt(line: str) -> ArgEntry | OptEntry | None:
    """
    Parse an entry of argument and option sections.

    Args:
        line (str): Input line.

    Returns:
        (ArgEntry | OptEntry | None): Parsed result.

    Examples:
        >>> parse_opt("  -o   msg")
        OptEntry(name='o', name_alt=None, has_value=False, dtype_str='bool', desc='msg', default='False')
        >>> parse_opt("  --opt   msg")
        OptEntry(name='opt', name_alt=None, has_value=False, dtype_str='bool', desc='msg', default='False')
        >>> parse_opt("  -o, --opt   msg")
        OptEntry(name='opt', name_alt='o', has_value=False, dtype_str='bool', desc='msg', default='False')
        >>> parse_opt("  -o, --opt INT   msg")
        OptEntry(name='opt', name_alt='o', has_value=True, dtype_str='int', desc='msg', default=None)
    """
    # Try to parse as argument line.
    outputs, description, _ = match_arg(line)

    if len(outputs) > 0:

        # Get matched argument name.
        name = outputs[0]

        # The name should not be None.
        if not isinstance(name, str):
            raise YadOptError["internal_error"]()

        # Get data type.
        dtype_str, description = get_dtype_str(name, description)

        # Get default value.
        description, default = get_default(description)

        return ArgEntry(name, dtype_str, description, default)

    # Try to parse as option line.
    outputs, description, has_value = match_opt(line)

    if len(outputs) > 0:

        # Unpack matched results.
        name, name_alt, value = outputs

        # The name should be a string.
        if not isinstance(name, str):
            raise YadOptError["internal_error"]()

        # Get data type.
        dtype_str, description = get_dtype_str(value, description)

        # Get default value.
        description, default = get_default(description)

        # If the option has no value (i.e. has_value is False),
        # then the data type and defualt value should be bool and False, respectively.
        if has_value is False:
            dtype_str, default = "bool", "False"

        return OptEntry(name, name_alt, has_value, dtype_str, description, default)

    return None


def get_dtype_str(var_name: str | None, description: str) -> tuple[str, str]:
    """
    Returns appropriate data type.

    Args:
        var_name (str): Variable name.

    Returns:
        (tuple): A tuple of appropriate Python data type and the rest of description.

    Examples:
        >>> get_dtype_str("x_int", "Integer value.")
        ('int', 'Integer value.')
        >>> get_dtype_str("x", "(INT) Integer value.")
        ('int', 'Integer value.')
    """
    # Try to get type from the description.
    if (m := re.match(r"^\s*\((\w+)\)\s*", description)) is not None:

        # Get matched data type name and description.
        dtype_str = m.group(1).strip().lower()
        description = description[len(m.group(0)):]

        # If the matched data type name is valid, then return them.
        if dtype_str in DTYPE_HINTS:
            return (dtype_str, description)

    # Returns unknown type if variable name is None.
    if var_name is None:
        return ("unknown", description)

    # Try to get type from the variable name.
    for key in DTYPE_HINTS:
        if var_name.lower().endswith(key):
            return (key, description)

    return ("unknown", description)


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
