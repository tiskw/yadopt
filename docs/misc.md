---
layout: minimal
title: "Miscellaneous"
parent: "Overview"
nav_order: 5
---

YadOpt Documentation
====================================================================================================

Miscellaneous
----------------------------------------------------------------------------------------------------

### Merge two YadOptArgs objects

The `YadOptArgs` class, which is returned by `yadopt.parse`, supports the merge operator `|`,
similar to Python dictionaries. This operator combines two `YadOptArgs` objects into a new one.
If the same key exists in both objects, the value from the right-hand operand is used.

This merge operator is particularly useful when reading an existing configuration file, such as
one specified with a `--config` argument, and then overriding those settings with values explicitly
provided on the command line.

For example:

```python
"""
Train a neural network model.

Arguments:
    config_path     Path to base config file.

Training options:
    --epochs INT    The number of training epochs.   [default: 100]
    --model STR     Neural network model name.       [default: mlp]
    --lr FLT        Learning rate.                   [default: 1.0E-3]
"""

import yadopt

if __name__ == "__main__":

    # Parse the command line arguments.
    args = yadopt.parse(__doc__)

    # Load the base config file.
    args_base = yadopt.load(args.config_path)

    # Update the parsed command line arguments.
    args_updated = args_base | args
    print(args_updated)
```

### Backward compatibility of the load functions

The older versions of YadOpt (<= 2026.1.5) used a different TOML/JSON format in the save and load
functions. The content of the TOML/JSON file was fundamentally different; older versions saved help
messages and argument vector before parsing, and re-parsed them when loading. This can be seen as
a YadOpt-style approach in which the help message is treated as the single source of truth. However,
it makes it impossible to save `YadOptArgs` after operations such as merging `|` or group extraction
`yadopt.get_group`, and it also fails to guarantee reproducibility if there is a bug in YadOpt's
parsing functionality (and there is no such thing as completely bug-free software, if anything, only
TeX might come close). Therefore, the current version of YadOpt has shifted to an approach that
directly stores the parsed argument values, and the help message and argument vector are not
included.



Older versions of YadOpt (<= 2026.1.5) used a different TOML/JSON format for the save and load
functions. The contents of these files were fundamentally different: older versions saved the help
message and the argument vector before parsing, then re-parsed them when loading. This can be viewed
as a YadOpt-style approach, in which the help message is treated as the single source of truth.
However, this approach makes it impossible to save a `YadOptArgs` object after operations such as
merging with `|` or extracting a group with `yadopt.get_group`. It also makes reproducibility depend
on the parser implementation, which means that a parsing bug could affect loaded results.

Therefore, the current version of YadOpt uses an approach that directly stores the parsed argument
values and group information, and the help message and original argument vector are no longer
stored.

