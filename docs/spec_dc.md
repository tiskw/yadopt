---
layout: minimal
title: "Spec of dataclass"
parent: "Overview"
nav_order: 3
---

YadOpt Documentation
====================================================================================================

Dataclass Specification
----------------------------------------------------------------------------------------------------

In addition to help-message-driven parsing, YadOpt supports dataclass-driven command-line argument
parsing. In this style, YadOpt generates a help message internally from a dataclass definition and
then parses command-line arguments according to the generated help message.

This section describes the formal specification of dataclasses used
for command-line parsing in YadOpt.

### Overview of dataclass for command-line parsing

A dataclass can be passed directly to `yadopt.parse`.
The following example shows a typical dataclass-driven command-line parsing in YadOpt:

```python
import dataclasses
import yadopt

@dataclasses.dataclass
class Config:
    """Configuration for the script."""

    output_dir: yadopt.Path     # Path to output directory.
    optimizer: str = "sgdm"     # Optimizer name.
    num_epochs: int = 100       # The number of training epochs.
    cpu_only: bool = False      # Whether to use CPU only.

config: Config = yadopt.parse(Config)
print(config)
```

In this example, `output_dir` is treated as a positional argument because it has no default value.
The remaining fields, `optimizer`, `num_epochs`, and `cpu_only`, are treated as optional arguments
because they have default values. Field type annotations are used to determine the data types of
the parsed values. The supported data types are the same as those used in help-message-driven
parsing. Comments following field definitions are used as field descriptions in the generated
help message.

### Restrictions and notes

When using dataclass-driven parsing, keep the following points in mind:
- Field comments used as descriptions must be written on a single line.
  Multi-line descriptions are not supported.
- Because field descriptions are extracted from comments in the source code, this feature depends
  on the availability of the original source file. In environments where the source code cannot
  be inspected reliably, such as interactive sessions, notebooks, or zipapps, dataclass-driven
  parsing may not be available.
- The returned object is an instance of a dynamically generated dataclass that inherits
  from both the input dataclass and YadOptArgs.

