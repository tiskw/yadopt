"""
Initialize yadopt module.
"""

# Import functions.
from .yadopt import parse, wrap
from .gendat import YadOptArgs

# Version information.
__version__ = "2024.11.02"

# Declare published functions and variables.
__all__ = ["parse", "wrap", "YadOptArgs", "__version__"]

# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
