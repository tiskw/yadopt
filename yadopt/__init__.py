"""
yadopt.__init__ - initialize yadopt module
"""

# Import functions.
from .dtypes  import Path
from .hint    import type_func
from .persist import load, save
from .yadopt  import YadOptArgs, parse, wrap, to_dict, to_namedtuple, get_group

# Version information.
__version__ = "2026.01.05"

# Declare published functions and variables.
__all__ = ["parse", "wrap", "to_dict", "to_namedtuple", "save", "load", "get_group",
           "type_func", "YadOptArgs", "Path", "__version__"]

# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
