<div align="center">
  <img src="docs/images/yadopt_logo.svg" width="80%">
</div>

<div align="center">
  <img src="https://img.shields.io/badge/PYTHON-%3E%3D3.10-blue.svg?style=for-the-badge&logo=python&logoColor=white">
  &nbsp;
  <img src="https://img.shields.io/badge/LICENSE-MIT-orange.svg?style=for-the-badge">
  &nbsp;
  <img src="https://img.shields.io/badge/COVERAGE-97.1%25-green.svg?style=for-the-badge">
  &nbsp;
  <img src="https://img.shields.io/badge/QUALITY-10.0/10.0-yellow.svg?style=for-the-badge">
</div>

YadOpt - Yet another docopt
========================================================================================================================

YadOpt is a modernized [docopt](https://github.com/docopt) for Python with static typing, serialization,
and reproducibility support. Define your CLI once as a human-readable help message. YadOpt does the rest.


Quick example
------------------------------------------------------------------------------------------------------------------------

```python
"""
Train a convolutional neural network model on an image classification dataset.

Mandatory arguments:
    output_dir_path           Path to output directory.

Training options:
    --optimizer STR           Optimizer name.                     [default: sgdm]
    --lr FLOAT                Learning rate.                      [default: 1.0E-3]
    --epochs INT              The number of training epochs.      [default: 100]

Other options:
    -h, --help                Show this help message and exit.
"""

import yadopt

# Parse as a custom class (yadopt.YadOptArgs) instance.
args = yadopt.parse(__doc__)
print(args)

# You can save the parsed arguments to a file and restore them later.
yadopt.save("args.toml", args)
```

Save the above code as `sample.py` and run it as follows:

```console
$ python3 sample.py mlruns --optimizer adam --lr 1.0E-3 --epochs 10
YadOptArgs(output_dir_path=mlruns, optimizer=adam, lr=0.001, epochs=10, help=False)
```

Unlike libraries such as [Click](https://github.com/pallets/click) and [Typer](https://github.com/fastapi/typer),
where the CLI is defined in Python code, YadOpt treats a human-readable specification itself as the single source
of truth.

You can view the help message using the `-h` or `--help` option. YadOpt always treats the `--help` option as a special
option to display the help message and exit, regardless of whether it is defined in the docstring. In the example above,
the short option `-h` is bound to the `--help` option, so you can also view the help message with `-h`.


Installation
------------------------------------------------------------------------------------------------------------------------

You can install YadOpt via [pip](https://pip.pypa.io/en/stable/):

```console
$ pip install yadopt
```


Usage
------------------------------------------------------------------------------------------------------------------------

### Use `parse` function

The `yadopt.parse` function allows you to parse command-line arguments based on your docstring. By default, the function
parses `sys.argv`, but you can explicitly specify the argument vector by using the second argument of the function,
as shown below.

```python
# Parse "sys.argv" (default behaviour).
args = yadopt.parse(__doc__)

# Parse the given argument vector "argv".
args = yadopt.parse(__doc__, argv)
```

### Use `wrap` function

YadOpt also supports decorator-style command-line parsing through the `@yadopt.wrap` decorator.
The decorator takes the same arguments as the function `yadopt.parse`.

```python
@yadopt.wrap(__doc__)
def main(args: yadopt.YadOptArgs, arg1: int, arg2: str):
    ...

if __name__ == "__main__":
    main(arg1=1, arg2="2")
```

### How to specify argument and option types

YadOpt provides two ways to specify argument and option types:
(1) type suffix and (2) type declaration in the description head.

**(1) Type suffix**: Users can specify argument and option types by appending a type name to
the argument or option name, as in the following examples:

```
Options:
    --opt1 FLT    Option with floating-point type.
    --opt2 STR    Option with string type.
```

**(2) Type declaration in the description head**: An alternative way to specify argument and option types
is to precede the description with the type name in parentheses.

```
Options:
    --opt1 VAL1    (float) Option with floating-point type.
    --opt2 VAL2    (str)   Option with string type.
```

YadOpt currently supports the following types. Note that the type names are case-insensitive,
and data types other than those listed below, such as list and enumeration, are not supported.

| Data type in Python | Type name in YadOpt          |
|---------------------|------------------------------|
| `bool`              | bool, BOOL, boolean, BOOLEAN |
| `int`               | int, INT, integer, INTEGER   |
| `float`             | flt, FLT, float FLOAT        |
| `str`               | str, STR, string, STRING     |
| `pathlib.Path`      | path, PATH                   |


### Dictionary and named tuple support

The return value of `yadopt.parse` is an instance of `YadOptArgs`, a regular mutable Python class.
However, sometimes a dictionary with the `get` accessor, or an immutable named tuple, may be preferable.
In such cases, you can use `yadopt.to_dict` or `yadopt.to_namedtuple` function.

```python
# Convert the return value to dictionary.
args = yadopt.to_dict(yadopt.parse(__doc__))

# Convert the return value to namedtuple.
args = yadopt.to_namedtuple(yadopt.parse(__doc__))
```

### Restore arguments from a file

YadOpt has the ability to save parsed argument instances to a file and load them back later. These features are
useful, for example, in machine learning code, when you want to reuse exactly the same arguments after a previous
execution. Supported file formats include TOML and JSON.

```python
# First, parse the command line arguments and create an instance of YadOptArgs.
args = yadopt.parse(__doc__)

# Save the parsed arguments as a TOML file.
yadopt.save("args.toml", args)

# Restore parsed YadOptArgs instance from the TOML file.
args_restored = yadopt.load("args.toml")
```

The structure of the TOML and JSON files is simple &mdash; the command-line input is stored in the `"argv"` key,
and the docstring is stored in the `"docstr"` key in the TOML/JSON file. If users want to write the TOML/JSON file
manually, the author recommends generating a TOML/JSON file using the `yadopt.save` function first and investigating
the contents of the file.


Motivation
------------------------------------------------------------------------------------------------------------------------

Why is command-line argument parsing for CLI programs still so unnecessarily cumbersome? In machine learning workflows,
engineers frequently write short-lived scripts with many command-line parameters:

```sh
python3 train.py --model resnet50 --optimizer adam --lr 1.0E-4 --epochs 300 ...
```

Despite their simplicity, many command-line parsers, including third-party solutions such as
[Click](https://github.com/pallets/click) and [Typer](https://github.com/fastapi/typer),
still require developers to describe the same information repeatedly across parser definitions, help messages,
configuration files, and type declarations. While [docopt](https://github.com/docopt) addressed part of this problem
by treating the help message as the CLI definition. However, it does not provide native support for modern Python
features such as type hints, configuration management, and reproducibility. YadOpt extends this idea: define your CLI
once as a human-readable specification, and it becomes a parser, a typed interface, and a reproducible configuration
source all in one place.

Ultimately, YadOpt aims to make command-line argument parsing simple enough that, if someone sitting next to you
is struggling with it, you can simply say:

<p align="center"><i>
    Try writing something that looks like a normal help message and feed it into YadOpt
    &mdash; it just works!
</i></p>


API reference
------------------------------------------------------------------------------------------------------------------------

See [API reference page](https://tiskw.github.io/yadopt/index.html#sec4) of the online document.


Tips
------------------------------------------------------------------------------------------------------------------------

### Merge two YadOptArgs objects

The `YadOptArgs` class, which is the return value of the `yadopt.parse` function, supports the merge operator `|`,
similar to Python dictionaries. This operator combines the two given YadOptArgs objects into a new one. In case
of a key conflict, the values from the right-hand operand are used.

This merge operator is particularly useful for implementing a feature to read an existing configuration file
(for example, a file specified with the `--config` argument) and then overwrite those settings with values explicitly
provided in the command line arguments. For example:

```python
"""
Usage:
    train.py <config_path> [--epochs INT] [--model STR] [--lr FLT]
    train.py --help

Train a neural network model.

Arguments:
    config_path     Path to base config file.

Training options:
    --epochs INT    The number of training epochs.   [default: 100]
    --model STR     Neural network model name.       [default: mlp]
    --lr FLT        Learning rate.                   [default: 1.0E-3]

Other options:
    -h, --help      Show this help message and exit.
"""

import yadopt

if __name__ == "__main__":

    # Parse the command line arguments.
    args = yadopt.parse(__doc__)

    # Load the base config file.
    args_base = yadopt.load(args.config_path)

    # Update the parsed command line arguments.
    args_updated = args | args_base
    print(args_updated)
```

### Notes on explicit `argv` values

When `argv` is explicitly supplied to `yadopt.parse`, the canonical form is the same as `sys.argv`,
i.e. the first element is the program name. For option-only CLIs, YadOpt also accepts the shortened
form without the program name.

### Multiple positional arguments

A positional argument declared with `...` must be the last positional argument.

### Comparison with other similar libraries

| Functions / Features    | argparse                            | click                   | docopt                                      | Typer                      | YadOpt (this repository)                          |
|-------------------------|-------------------------------------|-------------------------|---------------------------------------------|----------------------------|---------------------------------------------------|
| Basic style             | Object-Oriented                     | Decorators              | Docstring                                   | Type hints and decorators  | Docstring                                         |
| Standard library        | Yes                                 | No (pip)                | No (pip)                                    | No (pip)                   | No (pip)                                          |
| Data type specification | Yes                                 | Yes                     | No                                          | Yes                        | Yes                                               |
| Config file integration | Not native                          | Not native              | Not native                                  | Not native                 | Yes                                               |
| User experience         | Standard, sometimes verbose         | Widely used, modern API | Innovative, requires manual type conversion | Widely used, modern API    | Unique, integrates docs, types, and configuration |

Please note that qualitative metrics (e.g., user experience) are based on the author's subjective evaluation.


Developer's note
------------------------------------------------------------------------------------------------------------------------

### Preparation

Additional commands and Python packages are required for developers to measure the number of lines in the code,
code quality, etc. Please run the following command (the author recommends using
[venv](https://docs.python.org/3/library/venv.html) to avoid polluting your development environment).

```console
$ apt install cloc docker.io
$ pip install -r requirements-dev.txt
```

### Utility commands for developers

The Makefile provides several utility commands. Please run `make` at the root directory of this repository to see
the details of the subcommands in the Makefile.

```console
$ make
Usage:
    make <command>

Build commands:
    build         Build package
    testpypi      Upload package to TestPyPi
    pypi          Upload package to PyPi
    install-test  Install from TestPyPi

Test and code check commands:
    check         Check the code quality
    count         Count the lines of code
    coverage      Measure code coverage
	test          Run test on this device
	testall       Run test on Docker

Other commands:
    clean         Cleanup cache files
    help          Show this message
```

### Architecture diagram

![software\_architecture](./docs/images/software_architecture.svg)

