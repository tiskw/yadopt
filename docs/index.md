---
layout: default
title: "Overview"
nav_order: 1
---

YadOpt Documentation
====================================================================================================

Overview
----------------------------------------------------------------------------------------------------

This documentation provides a comprehensive guide to YadOpt, a help-message-driven command-line
argument parsing library for Python. YadOpt treats a human-readable help message as
the **single source of truth** for defining CLI behavior. From this specification, it automatically
derives parsing logic, typed interfaces, and reproducible configurations.

For basic information of YadOpt, including installation instructions and quick examples, please
refer to the [README](https://github.com/tiskw/yadopt) of the repository. This documentation
focuses on the detailed information, such as the API reference and the help message specification,
avoiding duplication of introductory materials.

Table of Contents
----------------------------------------------------------------------------------------------------

### Help Message Specification
- [Overview of help message structure](./spec_hm.md#Overview-of-help-message-structure)
- [Sections](./spec_hm.md#Sections)
- [Lines in a section](./spec_hm.md#Lines-in-a-section)
- [Positional argument declaration](./spec_hm.md#Positional-argument-declaration)
- [Optional argument declaration](./spec_hm.md#Optional-argument-declaration)
- [Naming conventions](./spec_hm.md#Naming-conventions)
- [Type inference of positional or optional argument values](./spec_hm.md#Type-inference-of-positional-or-optional-argument-values)
- [Common mistakes and pitfalls](./spec_hm.md#Common-mistakes-and-pitfalls)

### Dataclass Specification
- [Overview of dataclass for command-line parsing](./spec_dc.md#Overview-of-dataclass-for-command-line-parsing)
- [Restrictions and notes](./spec_dc.md#Restrictions-and-notes)

### API Reference
- [yadopt.parse](./apiref.md#yadopt.parse)
- [yadopt.wrap](./apiref.md#yadopt.wrap)
- [yadopt.save](./apiref.md#yadopt.save)
- [yadopt.load](./apiref.md#yadopt.load)
- [yadopt.to\_dict](./apiref.md#yadopt.to_dict)
- [yadopt.to\_namedtuple](./apiref.md#yadopt.to_namedtuple)
- [yadopt.get\_group](./apiref.md#yadopt.get_group)

### Miscellaneous
- [Merge two YadOptArgs objects](./misc.md#Merge-two-YadOptArgs-objects)
- [Backward compatibility of the load functions](./misc.md#Backward-compatibility-of-the-load-functions)


Project Information
----------------------------------------------------------------------------------------------------

### Author

YadOpt is developed and maintained by:
- [Tetsuya Ishikawa](https://github.com/tiskw)

### Contributing and Issues

Bug reports, feature requests, and contributions are welcome.
Please visit the GitHub repository:
- [https://github.com/tiskw/yadopt](https://github.com/tiskw/yadopt)

### License

This project is distributed under the MIT License.

### Acknowledgements

YadOpt is inspired by projects such as [docopt](https://github.com/docopt) and
[docopt-ng](https://github.com/jazzband/docopt-ng). It aims to extend the idea
of help-message-driven CLI definitions for modern Python development.

