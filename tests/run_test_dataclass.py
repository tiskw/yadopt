"""
Test for datacalss in the parse function.
"""

# Import standard libraries.
import dataclasses
import sys

# Import Yadopt.
sys.path.append(".")
import yadopt


@dataclasses.dataclass
class Config:
    """
    Configuration for the script.
    """
    output_dir: yadopt.Path            # Path to output directory.
    optimizer : str          = "sgdm"  # Optimizer name.
    lr        : float        = 1.0E-3  # Learning rate.
    num_epochs: int          = 100     # The number of training epochs.
    cpu_only  : bool         = False   # Whether to use CPU only.


if __name__ == "__main__":

    # Parse the command line arguments.
    args = yadopt.parse(Config, ["mlruns", "--lr", "0.01", "--num_epochs", "50"])

    # Save and load the parsed arguments to/from a TOML file.
    yadopt.save("/tmp/yadopt_test_dataclass.toml", args)
    args_restored = yadopt.load("/tmp/yadopt_test_dataclass.toml")
    assert args == args_restored

    # Print the help message and exit.
    yadopt.parse(Config, ["--help"])


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
