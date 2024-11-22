"""
Testcase 11: save and load
"""

# Import standard libraries.
import os
import pathlib
import sys
import traceback

# Import Yadopt.
sys.path.append(".")
import yadopt


docstring = """
Usage:
    train.py subcmd1 [--bool BOOL] [--int INT] [--float FLOAT] [--str STR] [--path PATH]
    train.py subcmd2 [--bool BOOL] [--int INT] [--float FLOAT] [--str STR] [--path PATH]
    train.py subcmd3 [--bool BOOL] [--int INT] [--float FLOAT] [--str STR] [--path PATH]

Options:
    --bool BOOL    An option of type boolean.
    --int INT      An option of type integer.
    --float FLOAT  An option of type float.
    --str STR      An option of type string.
    --path PATH    An option of type path.
"""

commands = [
    "train.py subcmd1 --bool True --int 6 --float 3.1416 --str hello --path ./dir",
]


def check(index, args, command):
    """
    Checker function for testcases.

    Args:
        index   (int)       : Index of testcases.
        args    (YadOptArgs): Parsed command line arguments.
        command (str)       : Command string (source of `args`).
    """
    print("  ->", args)

    if index == 0:
        print(args)
        assert args.subcmd1 == True
        assert args.subcmd2 == False
        assert args.subcmd3 == False
        assert args.bool == True
        assert args.int == 6
        assert abs(args.float - 3.1416) < 1.0E-5
        assert args.str == "hello"
        assert args.path == pathlib.Path("./dir")

        for suffix in ["json", "json.gz", "pkl", "pkl.gz"]:
            yadopt.save(f"/tmp/yadopt_test_args.{suffix}", args)
            args_restore = yadopt.load(f"/tmp/yadopt_test_args.{suffix}")
            assert args == args_restore

    else:
        raise ValueError(f"Check function for index={index} not found")


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
