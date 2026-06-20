"""
Test for TOML in the save/load function.

Regular cases are covered in run_test_dataclass.py, however, broken TOML and
legacy TOML cannot be tested in run_test_dataclass.py. This script is for
testing those cases instead.
"""

# Import standard libraries.
import pathlib
import sys

# For type hinting.
from typing import TypeAlias

# Import Yadopt.
sys.path.append(".")
import yadopt

# Data type aliases.
Path: TypeAlias = pathlib.Path


def test_broken_json():
    """
    Test for broken JSON format.
    """
    root: Path = Path(__file__).parent

    # Load config from JSON file.
    try:
        config = yadopt.load(root / "files" / "broken_json_file1.json")
    except yadopt.YadOptError.InvalidTomlFile:
        print("PASSED: Caught InvalidTomlFile error")


def test_broken_toml():
    """
    Test for broken TOML format.
    """
    root: Path = Path(__file__).parent

    # Load config from TOML file.
    for idx in range(1, 4):
        try:
            config = yadopt.load(root / "files" / f"broken_toml_file{idx}.toml")
        except yadopt.YadOptError.InvalidTomlFile:
            print("PASSED: Caught InvalidTomlFile error")

 
def test_legacy_toml():
    """
    Test for legacy TOML format.
    """
    root: Path = Path(__file__).parent

    # Load config from TOML file.
    args = yadopt.load(root / "files" / "args_20260105.toml")

    # Values in argv.
    assert args.model == "resnet34"
    assert args.num_epochs == 500
    assert args.optimizer == "radam"
    assert args.use_amp == True

    # Values not in argv (i.e. default values).
    assert args.dataset == "tiny-imagenet"
    assert args.weights is None
    assert args.lr == 1.0E-4


if __name__ == "__main__":

    # Test for broken JSON/TOML format.
    test_broken_json()
    test_broken_toml()

    # Test for legacy TOML format.
    test_legacy_toml()


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
