<div align="center">
  <img src="figures/yadopt_logo.svg" width="90%">
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
and docopt-ng, however, **YadOpt also supports date type hinting and conversion
to dictionaries and data classes**.

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
# Parse sys.argv
args = yadopt.parse(__doc__)

# Parse the given argv.
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
In that case, please try `.to_dict` and `.to_namedtuple` functions.

```python
# Convert the returned value to dictionary.
args = yadopt.parse(__doc__).to_dict()

# Convert the returned value to namedtuple.
args = yadopt.parse(__doc__).to_namedtuple()
```


API
--------------------------------------------------------------------------------

### `yadopt.parse`

```python
yadopt.parse(
    docstr: str,
    argv: list[str] = None,
    default_type: str = "auto",
    force_continue: bool = False,
) -> YadOptArgs
```

### Args

| Name             | Type        | Default value | Description |
|:-----------------|:-----------:|:-------------:|:------------|
| `docstr`         | `str`       | -             | A help message string that will be parsed to create an object of command line arguments. We recommend to write a help message in the docstring of your Python script and use `__doc__` here. |
| `argv`           | `list[str]` | `None`        | An argument vector to be parsed. YadOpt uses the command line arguments passed to your Python script, `sys.argv[1:]`, by default. |
| `default_type`   | `str\|type` | `"auto"`      | Default data type of arguments and options. The default value `"auto"` means automatic determination. |
| `force_continue` | `bool`      | `False`       | If `True`, do not exit the software regardless of whether YadOpt succeeds command line parsing or not. |

### Returns

The returned value is an instance of the `YadOptArgs` class that represents parsed
command line arguments. The `YadOptArgs` class is a normal mutable Python
class and users can access to parsed command line arguments by the dot notation.
If you wish to convert `YadOptArgs` to dictionary type, please use `.to_dict()`
function. Likewise, if you prefer an immutable data type, please try
`.to_namedtuple()` function.

### `yadopt.wrap`

```python
yadopt.wrap(*pargs, **kwargs) -> Callable
```

### Args

The same as the arguments of `yadopt.parse` function.

### Returns

The `yadopt.wrap` is a Python decorator function that allows users to modify
the behavior of functions or methods, therefore the returned value of this
function is a callable object. The first argument of the target function of
this decorator is curried by the result of `yadopt.parse` and the curried
object will be returned.
