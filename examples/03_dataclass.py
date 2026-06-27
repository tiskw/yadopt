# Import standard libraries.
import dataclasses

import sys
sys.path.append(".")

# Import YadOpt.
import yadopt


@dataclasses.dataclass
class Config:
    """
    Configuration for the script.
    """
    output_dir: yadopt.Path    # Path to output directory.
    optimizer : str  = "sgdm"  # Optimizer name.
    num_epochs: int  = 100     # The number of training epochs.
    cpu_only  : bool = False   # Whether to use CPU only.


if __name__ == "__main__":
    argv = ["mlruns", "--optimizer", "adam", "--num_epochs", "10"]
    args = yadopt.parse(Config, argv)
    print(args)


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
