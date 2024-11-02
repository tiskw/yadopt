"""
"""

# Import standard libraries.
import importlib
import pathlib
import shlex
import sys

# Import Yadopt.
sys.path.append(".")
import yadopt


# Define color code.
COLOR_GREEN = "\x1b[32m"
COLOR_NONE  = "\x1b[0m"


def main():
    """
    Main function of test.
    """
    # Run all test cases.
    for path_py in sorted(pathlib.Path(__file__).parent.glob("testcase??.py")):

        # Get the module name.
        module_name = path_py.with_suffix("").name

        # Import testcase module.
        testcase = importlib.import_module(module_name)

        for idx, command in enumerate(testcase.commands):

            print(f"Test: {module_name} - {idx}")

            # Run the testcase.
            try:
                args = yadopt.parse(testcase.docstring, shlex.split(command), force_continue=True)
            except Exception as error:
                testcase.check_error(idx, error)
            else:
                testcase.check(idx, args, command)

            print(f"  -> {COLOR_GREEN}Passed{COLOR_NONE}")

    # Test wrap function.
    print(f"Test: testcase_wrap")
    testcase = importlib.import_module("testcase_wrap")
    testcase.test()
    print(f"  -> {COLOR_GREEN}Passed{COLOR_NONE}")


if __name__ == "__main__":
    main()


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
