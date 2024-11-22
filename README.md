<div align="center">
  <img src="docs/images/yadopt_logo.svg" width="90%">
</div>

<div align="center">
  <img src="https://img.shields.io/badge/PYTHON-%3E%3D3.9-blue.svg?style=for-the-badge&logo=python&logoColor=white">
  &nbsp;
  <img src="https://img.shields.io/badge/LICENSE-MIT-orange.svg?style=for-the-badge">
  &nbsp;
  <img src="https://img.shields.io/badge/COVERAGE-96%25-green.svg?style=for-the-badge">
  &nbsp;
  <img src="https://img.shields.io/badge/QUALITY-9.95/10.0-yellow.svg?style=for-the-badge">
</div>

YadOpt - Yet another docopt
================================================================================

YadOpt is a Python re-implementation of [docopt](https://github.com/docopt/docopt)
and [docopt-ng](https://github.com/jazzband/docopt-ng), a human-friendly
command-line argument parser with type hinting and utility functions.
YadOpt helps you to create beautiful command-line interfaces, just like docopt
and docopt-ng, however, **YadOpt also supports: (1) date type hinting,
(2) conversion to dictionaries and namedtuples, and (3) saving and loading functions**.

The following is the typical usage of YadOpt:

```python
"""
Usage:
    train.py <config_path> [--epochs INT] [--model STR] [--lr FLT]
    train.py --help

Train a neural network model.

Arguments:
    config_path     Path to config file.

Training options:
    --epochs INT    The number of training epochs.   [default: 100]
    --model STR     Neural network model name.       [default: mlp]
    --lr FLT        Learning rate.                   [default: 1.0E-3]

Other options:
    -h, --help      Show this help message and exit.
"""

import yadopt

if __name__ == "__main__":
    args = yadopt.parse(__doc__)
    print(args)
```

Please save the above code as `sample.py`, and run it as follows:

```console
$ python3 sample.py config.toml --epochs 10 --model=cnn
YadOptArgs(config_path=config.toml, epochs=10, model=cnn, lr=0.001, help=False)
```

In the above code, the parsed command-line arguments are stored in the `arg`
and you can access each argument using dot notation, like `arg.config_path`.
Also, the parsed command-line arguments are typed, in other words,
the `arg` variable satisfies the following assertions:

```python
assert isinstance(args.config_path, pathlib.Path)
assert isinstance(args.epochs, int)
assert isinstance(args.model, str)
assert isinstance(args.lr, float)
assert isinstance(args.help, bool)
```

More realistic examples can be found in the [examples](./examples/README.md)
directory.


Installation
--------------------------------------------------------------------------------

Please install from [pip](https://pip.pypa.io/en/stable/).

```console
$ pip install yadopt
```


Usage
--------------------------------------------------------------------------------

### Use `parse` function

The `yadopt.parse` function allows you to parse command-line arguments based on
your docstring. The function is designed to parse `sys.argv` by default, but
you can explicitly specify the argument vector by using the second argument
of the function, just like as follows:

```python
# Parse "sys.argv" (default behaviour).
args = yadopt.parse(__doc__)

# Parse the given argument vector "argv".
args = yadopt.parse(__doc__, argv)
```

### Use `wrap` function

YadOpt supports the decorator approach for command-line parsing by the decorator
`@yadopt.wrap` which takes the same arguments as the function `yadopt.parse`.

```python
@yadopt.wrap(__doc__)
def main(args: yadopt.YadOptArgs, real_arg: str):
    ...

if __name__ == "__main__":
    main("real argument")
```

### Dictionary and namedtuple support

The returned value of `yadopt.parse` is an instance of `YadOptArgs` that is
a normal mutable Python class. However, sometimes a dictionary that has
the `get` accessor, or an immutable namedtuple, may be preferable.
In that case, please try `yadopt.to_dict` and `yadopt.to_namedtuple` functions.

```python
# Convert the returned value to dictionary.
args = yadopt.to_dict(yadopt.parse(__doc__))

# Convert the returned value to namedtuple.
args = yadopt.to_namedtuple(yadopt.parse(__doc__))
```

### Restore arguments from dictionary or JSON file

YadOpt has a function to save parsed argument instances as a JSON or pickle
format, and to restore the argument instances from the JSON and pickle files.

```python
# At first, create a parsed arguments (i.e. YadOptArgs instance).
args = yadopt.parse(__doc__)

# Save the parsed arguments as a JSON file.
yadopt.save("args.json", args, indent=4)

# Resotre parsed YadOptArgs instance from the JSON file.
args_restored = yadopt.load("args.json")
```

These functions are useful when recalling the arguments to previously executed
commands, especially ML code.

```python
"""
Usage:
    train.py <config_path> [--epochs INT] [--model STR] [--lr FLT]
    train.py --help

Train a neural network model.

Training options:
    --epochs INT   The number of training epochs.   [default: 100]
    --lr FLT       Learning rate.                   [default: 1.0E-3]

Restore options:
    --restore      Restore command options.         [default: None]

Other options:
    -h, --help     Show this help message and exit.
"""

import yadopt

if __name__ == "__main__":

    # Parse the docstring and command line arguments.
    args = yadopt.parse(__doc__)

    # Restore command options if specified.
    if args.restore is not None:
        args = yadopt.load(args.restore)

    print(args)
```


API
--------------------------------------------------------------------------------

See [API reference](https://tiskw.github.io/yadopt/index.html#sec4).
