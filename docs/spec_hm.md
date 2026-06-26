---
layout: minimal
title: "Spec of help message"
parent: "Overview"
nav_order: 2
---

YadOpt Documentation
====================================================================================================

Specification of help message
----------------------------------------------------------------------------------------------------

This section presents the formal specification of the help message.

### Overview of help message structure

A YadOpt help message is defined as a single string composed of one or more *sections*.
Of these sections, only those related to positional and optional arguments are parsed by YadOpt.
The sections that YadOpt parses consist of one or more *lines*,
with each line representing a declaration of a single positional or optional argument.

Positional arguments are declared by placing a delimiter after the argument name, followed by a description of
the positional argument, where the delimiter is defined as two or more consecutive whitespace characters.
There are no particular restrictions on the description; it can be written freely.

Optional arguments are declared by listing the option name, delimiter, and description in that order.
For options that take a value, include the option value in the option name (e.g., `--opt VALUE` or `--opt=VALUE`).
Short option names are also allowed (e.g., `-o, --opt VALUE`). You can write any description you like,
but if you want the option to have a default value, add the string `[default: ...]` at the end of the description.

YadOpt will raise an error if it cannot interpret the declaration lines for positional or optional arguments.

### Sections

A section is defined as a block of text that begins with a line that has no indentation and ends with a colon,
followed by a line that shares a common indentation level. Brackets can be used instead of colons.
Here, indentation is defined as the number of spaces at the beginning of each line, excluding blank lines,
and a tab character is treated as four spaces.
The section indentation level refers to the amount of indentation of the first line of the section's content.

```
Section Name A:
    This line is part of the section A.
    This line is also part of the section A.

This line is not part of a section.

[Section Name B]
    Brackets are also considered sections, not just colons.
```

YadOpt only recognizes sections that meet the following conditions (case is not sensitive):
  * the section name is either "arguments" or "options",
  * the section name starts with "arguments " or "options " (note that there is a whitespace at the end),
  * the section name ends with " arguments" or " options" (note that there is a whitespace at the beginning).
Other sections and strings outside of sections are ignored.

(Strictly speaking, the existence of a section that is named `Usage` slightly affects the display of help messages,
but this is not relevant to the help message specifications, so we won't delve into it further here)

### Lines in a section

The sections that YadOpt parses consist of one or more lines. Basically, one line corresponds to one declaration
of a positional or an optional argument, but declarations spanning multiple lines are also possible.
Lines with indentation deeper than the section's indentation level (as mentioned earlier, it is defined
as the indentation of the first line in the section) are considered to be the same line as the preceding line.
For example, the following declares a single option, `--opt`, and will not produce an error.

```
Options:
    --opt   The description
            spans multiple
            lines.
```

Also, the following is technically acceptable, but it is extremely difficult to read and strongly discouraged.

```
Options:
    --opt   The description   (indent=4)
       spans multiple         (indent=7 > 4)
         lines.               (indent=9 > 4)
```

### Positional argument declaration

Positional arguments are declared by placing a delimiter, two or more whitespace characters,
after the argument name, followed by a description of the positional argument. For example:

```
Arguments:
    conf_path     Path to the config file.
```

### Optional argument declaration

Optional arguments are declared by listing the option name, delimiter, and description in that order.
Optional arguments allow for the use of both short and long option names, as well as use them together,
and can also assign values to options. To assign a value to an option, write the value name after the option name,
followed by a single whitespace or a single equals sign without a whitespace.

Short options must consist of a single character. For example, an option declaration like `-abc` is not allowed.
Instead, if the argument `-abc` is given during command execution (i.e., the argument vector contains `-abc`),
this is treated as `-a`, `-b`, and `-c` are specified simultaneously.

Therefore, there are many variations in the declaration of optional arguments.
Some of them are listed below:

```
Flag options:
    -a                  Short name flag option.
    --alice             Long name flag option.

Options with a value:
    --bob VALUE         Long option with a value (whitespace).
    --charlie=VALUE     Long option with a value (equal sign).
    -d, --dave VALUE    Short and long option with a value.
    -e VAL, --eve VAL   Another way to declare an option with a value.
    --frank, -f         Unconventional but acceptable.
```

You can write any description you like, but if you want the option to have a default value, add the string
`[default: ...]` at the end of the description. Note that the `[default: ...]` notation is case-sensitive.
The string following `default:` will be recognized as the default value.

### Naming convention

The naming convention for positional and optional argument names follows Python's variable naming conventions.
This differs from the argument naming conventions of common Linux commands, but is because the parsed
arguments will later be referenced as Python variable names.
Exceptionally, hyphens and dots are allowed in any character other than the first character.
However, in this case, the hyphen and dot will be internally replaced with an underscore.
Therefore, be aware that variable name conflicts may occur due to the replacement.
For example, the argument names `user-name` and `user_name` cannot coexist.
Such conflicts will result in an error.

### Type inference of positional or optional argument values

For positional arguments or optional arguments that take values,
the type can be assigned using the following procedure.
Type assignment is performed in the order described below, and if none of the conditions apply,
it is treated as a string type.

#### 1. None type

If the value of a positional argument or an optional argument exactly matches "None" including case sensitivity,
the value will be NoneType, regardless of the type specification below.

#### 2. Description head

If the option description begins with parentheses and a type name,
the content inside the parentheses will be recognized as the type name.

```
Arguments:
    arg     (int) This is an integer argument.
```

#### 3. Value name suffix

If the name of a positional argument or option value ends with a type name, that type name will be used.

```
Arguments and options:
    arg_int        This is an integer argument.
    --opt FLOAT    This is a float-value option.
```

### Common mistakes and pitfalls

#### Number of spaces when specifying both short and long options

When specifying both short and long option names, or option values,
be careful not to accidentally include two or more spaces.
For example, the following two statements, differing only in the number of spaces,
declare completely different options.
Use a single space between an option name and its value,
and two or more whitespace characters to separate the description.

```
Options:
    --opt1 VALUE    Option with a value.
    --opt2          VALUE Oops, it is a flag option!
```

YadOpt attempts to detect such errors and raise errors or warnings whenever possible,
but it's not possible to catch all such cases completely, so careful attention is required.

#### Indentation errors that do not result in errors

If you make an indentation error like the one below, YadOpt will try to generate a warning whenever possible,
but in principle, no error will occur.
This is because `line3` below is, by definition, outside Section A, and YadOpt ignores strings outside of sections.

```
Section A:
    line1
    line2
  line3
```

#### Multiple positional argument errors

A positional argument declared with `...` must be the last positional argument.
If you declare a positional argument with `...` in the middle of other positional arguments,
YadOpt will raise an error.

#### Examples of section names

- Section names parsed by YadOpt:
    * `Mandatory arguments` (ends with ` arguments`)
    * `Options with a value` (starts with `options `)
- Section names ignored by YadOpt:
    * `MandatoryArguments`
    * `Flag-options`

