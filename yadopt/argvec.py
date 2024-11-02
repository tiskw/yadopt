"""
Argment vector parsers.
"""

# Declare published functins and variables.
__all__ = ["parse_argvec", "UserInput"]

# Import standard libraries.
import copy
import dataclasses

# Import custom modules.
from .argopt import OptEntry
from .usage  import UsageEntry


@dataclasses.dataclass
class UserInput:
    """
    Information of user input.
    """
    pres: dict  # Preceding tokens.
    args: dict  # Argument tokens.
    opts: dict  # Option tokens.


def parse_argvec(argv: list[str], usages: list[UsageEntry], opts: list[OptEntry]) -> UserInput:
    """
    Try to match with the given arguemtn vector and usage patterns.
    If matched, this function returns a dictionary that represents name-value
    correspondance. Otherwise, returns None.

    Args:
        argv  (list[str])       : Argument vector.
        usage (list[UsageEntry]): List of usage info.
        opts  (list[OptEntry])  : List of option info.

    Returns:
        (dict): Correspondance of argument/option names and values.
    """
    # Copy and rename the input argument vector.
    argv_orig = copy.deepcopy(argv)

    # Get a map from altanative name to standard name.
    alt_name_map = {item.name_alt:item.name for item in opts if item.name_alt is not None}

    # Standardize option names of argument vector.
    for idx, token in enumerate(argv_orig):
        if (token.startswith("-")) and (token[1:] in alt_name_map):
            argv_orig[idx] = "--" + alt_name_map[token[1:]]

    for usage in usages:

        # Expand [OPTIONS] token in the usage.
        if "OPTIONS" in usage.opts:

            # Remove the OPTIONS key from the usage.
            usage.opts.pop("OPTIONS")

            # Append all options.
            for opt in opts:
                usage.opts[opt.name] = "dummy" if (opt.n_args > 0) else None

        # Standardize option names of usage pattern.
        usage.opts = {alt_name_map.get(key, key):val for key, val in usage.opts.items()}

        # Copy the input argment vector for safety.
        argv_copy = copy.deepcopy(argv_orig)

        # Try to match the argument vector and usage pattern.
        user_input = match_argvec_and_usage(argv_copy, usage)

        # If matched, returns the UserInput instance.
        if user_input is not None:

            # Append all unused precesing tokens.
            for u in usages:
                for token_pre in u.pres[1:]:
                    if token_pre not in user_input.pres:
                        user_input.pres[token_pre] = False

            return user_input

    return None


def match_argvec_and_usage(argv: list[str], usage: UsageEntry) -> UserInput:
    """
    Try to match the given argument vector and usage pattern.
    If matched, returns UserInput instance, and otherwise, returns None.

    Args:
        argv  (list[str]) : Argument vector.
        usage (UsageEntry): Usage pattern.

    Returns:
        (UserInput): UserInput instance if matched, and None otherwise.
    """
    # Initialize the output dictionary.
    user_input = UserInput({}, {}, {})

    # Check preceding strings.
    for idx, token in enumerate(usage.pres):

        # It's convenient for users to ignore the first preceding argument,
        # which is often the name of the called Python script.
        if idx == 0:
            continue

        if (len(argv) <= idx) or (argv[idx] != token):
            return None

        user_input.pres[token.lstrip("-")] = True

    # Drop the preceding tokens from the argument vector.
    argv = argv[len(usage.pres):]

    # Make a copy of available argument names.
    available_args = copy.deepcopy(usage.args)

    while argv:

        # Get next token.
        token = argv.pop(0)

        # Case 1: Option token.
        if token.startswith("-"):
            is_matched = proc_opt_token(token, argv, user_input, usage)

        # Case 2: Argument token.
        else:
            is_matched = proc_arg_token(token, user_input, available_args)

        # Return None if not matched.
        if not is_matched:
            return None

    # If unused arguments remaining, that means the usage does not match.
    if any(not arg.endswith("...") for arg in available_args):
        return None

    return user_input


def proc_arg_token(token: str, user_input: UserInput, available_args: list[str]) -> bool:
    """
    Process argument token.

    Args:
        token          (str)      : Input token.
        user_input     (UserInput): User input instance.
        available_args (list[str]): Rest of available arguments.
    """
    # NOT MATRCHED!: too many arguments.
    if not available_args:
        return False

    # Case 2.1: multiple arguments.
    if available_args[0].endswith("..."):

        # Get argument name.
        target_arg = available_args[0].rstrip(".")

        # Create a list.
        if target_arg not in user_input.args:
            user_input.args[target_arg] = []

        # Append the token to the list.
        user_input.args[target_arg].append(token)

    # Case 2.2: single arguments.
    else:
        user_input.args[available_args.pop(0)] = token

    return True


def proc_opt_token(token: str, argv: list[str], user_input: UserInput, usage: UsageEntry) -> bool:
    """
    Process option token.

    Args:
        token      (str)       : Input token.
        argv       (list[str]) : Argument vector.
        user_input (UserInput) : User input instance.
        usage      (UsageEntry): Usage pattern.
    """
    # Remove hyphens.
    token = token.lstrip("-")

    # NOT MATRCHED!: unknown option.
    if token not in usage.opts:
        return False

    # Case 1.1: Option without value.
    if usage.opts[token] is None:

        user_input.opts[token] = True

    # Case 1.2: Option with value.
    else:

        # NOT MATRCHED!: option value not found (no token).
        if not argv:
            return False

        # Get option value.
        token_value = argv.pop(0)

        # NOT MATRCHED!: option value not found (seems like option token).
        if token_value.startswith("-"):
            return False

        user_input.opts[token] = token_value

    return True


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
