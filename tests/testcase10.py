"""
Testcase 10: test for validation functions
"""

# Import standard libraries.
import sys

# Import Yadopt.
sys.path.append(".")
import yadopt


class Testcase10_01:
    """
    Usage:
        sample.py [--alice INT] [--bob FLOAT]

    Options:
        -a, --alice INT  Option with integer value.  [default: 1]
        -b, --bob FLOAT  Option with float value.    [default: 1]
    """
    commands = [
        "sample.py --rob 1",
        "sample.py -a 1 -c 1",
    ]

    @staticmethod
    def check(index, args, command):
        """
        Checker function for testcases.

        Args:
            index   (int)       : Index of testcases.
            args    (YadOptArgs): Parsed command line arguments.
            command (str)       : Command string (source of `args`).
        """
        if index == 0:
            assert args.__class__.__name__ == "YadOptErrorUnknownOption"
            assert str(args).strip().startswith("Error summary:\n  ")
            print(str(args).strip())

        elif index == 1:
            assert args.__class__.__name__ == "YadOptErrorUnknownOption"
            assert str(args).strip().startswith("Error summary:\n  ")
            print(str(args).strip())

        else:
            raise ValueError(f"Check function for index={index} not found")


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
