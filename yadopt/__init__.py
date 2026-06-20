"""
yadopt.__init__ - initialize yadopt module
"""

# Import custom modules.
from .errors    import YadOptError
from .datamodel import YadOptArgs
from .dtypes    import Path
from .serialize import load, save
from .yadopt    import parse, wrap, to_dict, to_namedtuple, get_group

# Version information.
__version__ = "2026.1.5"

# Declare published functions and variables.
__all__ = ["parse", "wrap", "to_dict", "to_namedtuple", "save", "load", "get_group",
           "YadOptArgs", "YadOptError", "Path", "__version__"]


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
