"""
Train a convolutional neural network model on an image classification dataset.

Mandatory arguments:
    output_dir_path           Path to output directory.

Training options:
    --optimizer STR           Optimizer name.                     [default: sgdm]
    --lr FLOAT                Learning rate.                      [default: 1.0E-3]
    --epochs INT              The number of training epochs.      [default: 100]
"""

# Import standard libraries.
import sys

# Import YadOpt.
import yadopt

if __name__ == "__main__":
    argv = ["sample.py", "mlruns", "--optimizer", "adam", "--lr", "1.0E-3", "--epochs", "10"]
    args = yadopt.parse(__doc__, argv)
    print(args)

# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
