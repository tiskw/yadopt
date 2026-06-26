---
layout: minimal
title: "API Reference"
parent: "Overview"
nav_order: 4
---

YadOpt Documentation
====================================================================================================

API Reference
----------------------------------------------------------------------------------------------------

### yadopt.parse

```python
def parse(source: str | None,
          argv: list[str] | None = None,
          exit_on_help: bool = True,
          verbose: bool = False) -> YadOptArgs:
```

```python
def parse(source: type[T],
          argv: list[str] | None = None,
          exit_on_help: bool = True,
          verbose: bool = False) -> T:
```

Parse the input source and return the parsed arguments. This function is overloaded. When `source`
is a help message string, YadOpt uses the help-message-driven style and returns a `YadOptArgs`
instance. When `source` is a dataclass type, YadOpt uses the dataclass-driven style and returns
an instance of a dynamically generated dataclass that inherits from both `source` and `YadOptArgs`.
The input dataclass itself does not need to inherit from `YadOptArgs`. If `source` is `None`,
YadOpt uses the caller's module docstring as the help message.


### yadopt.wrap

```python
def wrap(*pargs: Any,
         **kwargs: Any) -> Callable
```

The `yadopt.wrap` decorator enables decorator-based command-line parsing. It wraps a function
so that command-line arguments are automatically parsed and passed to the function when it is
invoked. This function accepts the same arguments as `yadopt.parse`. The decorated function must
take a YadOptArgs instance as its first parameter. When the decorated function is called, YadOpt
parses the command-line arguments and injects the parsed arguments object into the first parameter
of the decorated function.

### yadopt.save

```python
def save(path: str | Path,
         args: YadOptArgs,
         metadata: bool = True,
         indent: int = 4) -> None
```

The `yadopt.save` function serializes a parsed `YadOptArgs` instance and writes it to the file
specified by `path`. Supported file formats include TOML (`.toml`) and JSON (`.json`), as well
as their compressed variants (`.toml.gz` and `.json.gz`). The saved file contains the parsed
argument values along with their type information, organized into groups. By default, the output
file includes execution metadata such as the hostname, username, platform information, Python
version, Git commit hash, and timestamp. To suppress most of this metadata, set `metadata=False`.
In that case, only the timestamp is preserved. The `indent` parameter controls the indentation
level of the output file.

### yadopt.load

```python
def load(path: str | Path) -> YadOptArgs
```

The `yadopt.load` function reads a file produced by `yadopt.save` and reconstructs the corresponding
`YadOptArgs` instance. The function supports all formats produced by `yadopt.save`, including TOML,
JSON, and their compressed variants. The loaded object contains the parsed argument values and
associated type information. Any additional metadata stored in the file does not affect argument
reconstruction.

### yadopt.to\_dict

```python
def to_dict(args: YadOptArgs) -> dict[str, Any]
```

The `yadopt.to_dict` function converts a YadOptArgs instance into a standard Python dictionary.
The returned dictionary contains all parsed arguments and their values.
Note that once a YadOptArgs instance is converted to a dictionary, it cannot be restored,
since group information is not preserved in the dictionary representation.

### yadopt.to\_namedtuple

```python
def to_namedtuple(args: YadOptArgs) -> tuple[Any, ...]
```

The `yadopt.to_namedtuple` function converts a `YadOptArgs` instance into an immutable named tuple.
The returned named tuple contains all parsed arguments and their values. The concrete named tuple
type is generated dynamically, so the return type is annotated as `tuple[Any, ...]`.
Note that once a `YadOptArgs` instance is converted to a named tuple, it cannot be restored,
since group information is not preserved in the named tuple representation.

### yadopt.get\_group

```python
def get_group(args: YadOptArgs,
              group: str) -> YadOptArgs
```

The `yadopt.get_group` function extracts a specified section, or group, from a parsed `YadOptArgs`
instance and returns it as a new `YadOptArgs` object. The target group is identified by its section
name, such as `"Arguments"` or `"Options"`. The returned object retains the same structure and type
information as the original `YadOptArgs`, but includes only the arguments belonging to the specified
group.

