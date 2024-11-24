"""
Generate YadoptArgument data class.
"""

# Declare published functions and variables.
__all__ = ["generate_dat", "YadOptArgs"]

# Import standard libraries.
import ast
import copy
import itertools

# Import custom modules.
from .argopt import ArgEntry, OptEntry
from .argvec import UserInput
from .docstr import DocStrInfo


class YadOptArgs:
    """
    Command line arguments parsed by YadOpt.
    """
    def __init__(self, args_dict=None):
        """
        Constructor.
        """
        if args_dict is not None:
            for key, value in args_dict.items():
                setattr(self, key, value)

    @property
    def __normal_dict__(self):
        """
        Returns "normal" dictionary that contains keys not starting with the underscore.
        """
        return {key:value for key, value in self.__dict__.items() if not key.startswith("_")}

    def __repr__(self):
        """
        Representation of this class.
        """
        contents = ", ".join(f"{key}={val}" for key, val in self.__normal_dict__.items())
        return f"{self.__class__.__name__}({contents})"

    def __str__(self):
        """
        String expression of this class.
        """
        return self.__repr__()

    def __eq__(self, other):
        """
        Returns True if equivarent.
        """
        return self.__normal_dict__ == other.__normal_dict__


def generate_dat(user_input: UserInput, docinfo: DocStrInfo, argv: list[str]) -> YadOptArgs:
    """
    Create YadOptArgs instance, fill the values, and return it.
    """
    # Create data instance.
    data = YadOptArgs()

    # Get a map from argument/option name to data type.
    data_types = {item.name:item.data_type for item in itertools.chain(docinfo.args, docinfo.opts)}

    # Fill user input preceding values.
    for name, value in user_input.pres.items():
        setattr(data, name, bool(value))

    # Set default values.
    for item in itertools.chain(docinfo.args, docinfo.opts):

        # Get typed default value.
        default = None if (item.default is None) else get_typed_data(item.default, item.data_type)

        # Set the default value.
        setattr(data, item.name, default)

    # Fill user input arguments and options.
    for name, value in (user_input.args | user_input.opts).items():

        # If the target value is list.
        if isinstance(value, list):
            setattr(data, name, [get_typed_data(v, data_types[name]) for v in value])

        # Otherwise.
        else:
            setattr(data, name, get_typed_data(value, data_types[name]))

    # Append extra data.
    setattr(data, "_info_", copy.deepcopy(docinfo))
    setattr(data, "_user_", copy.deepcopy(user_input))
    setattr(data, "_argv_", copy.deepcopy(argv))

    return data


def get_typed_data(value, data_type):
    """
    Returns typed value.

    Args:
        value     (str) : Value string.
        data_type (type): Data type, or None.

    Returns:
        (object): Typed value.
    """
    # Automatically determine the data type if the data_type is None.
    if data_type is None:
        try:
            return ast.literal_eval(value)
        except ValueError:
            return str(value)

    return data_type(value)


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
