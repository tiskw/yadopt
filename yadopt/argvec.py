"""
Argment vector parsers.
"""

# Declare published functins and variables.
__all__ = ["parse_argvec"]

# Import custom modules.
from .dtypes import ArgEntry, OptEntry, UsageOption, UsageEntry, UserInput
from .usage  import match_argvec_and_usage


def parse_argvec(argv: list[str], args: list[ArgEntry], opts: list[OptEntry], usages: list[UsageEntry]) -> UserInput:
    """
    Try to match with the given arguemtn vector and usage patterns.
    If matched usage found, this function returns a dictionary that represents name-value
    correspondance. Otherwise, returns None.

    Args:
        argv           (list[str]) : Argument vector.
        dsinfo         (DocStrInfo): Parsed result of docstring.
        force_continue (bool)      : Never exit the software if True.

    Returns:
        (UserInput): Correspondance of argument/option names and values.
    """
    def standerdize_option_names_in_argument_vector(argv, alt_names):
        """
        Standardize option names of argument vector.
        For example, "-h" -> "--help".
        """
        # Standardize option names of argument vector.
        for idx, (prefix, key) in enumerate((token[0], token[1:]) for token in argv):
            yield f"--{alt_names[key]}" if (prefix == "-") and (key in alt_names) else argv[idx]

    # Get a map from altanative name to standard name.
    alt_names = {item.name_alt:item.name for item in opts if item.name_alt is not None}

    # Standardize option names of argument vector.
    argv_std = list(standerdize_option_names_in_argument_vector(argv, alt_names))

    for usage in usages:

        # Convert options in usage to dict.
        usage_opt_dict: dict[str, UsageOption] = {usage_opt.name: usage_opt for usage_opt in usage.opts}

        # Expand [OPTIONS] token in the usage.
        if "OPTIONS" in usage_opt_dict:

            # Remove the OPTIONS key from the usage.
            usage_opt_dict.pop("OPTIONS")

            # Append all options.
            usage_opt_dict = {opt.name: UsageOption(name=opt.name, has_value=opt.has_value, required=False) for opt in opts}

        # Standardize option names of usage pattern.
        usage_opt_dict = {alt_names.get(key, key): value for key, value in usage_opt_dict.items()}

        # Try to match the argument vector and usage pattern.
        user_input = match_argvec_and_usage(argv_std, usage, usage_opt_dict)

        # If matched, returns the UserInput instance.
        if user_input is not None:

            # Append all unused precesing tokens as False.
            for u in usages:
                for token_pre in u.pres[1:]:
                    if token_pre not in user_input.pres:
                        user_input.pres[token_pre] = False

            # Append all optional arguments that has default value but not appears in the user input.
            for opt in opts:
                if (opt.name not in user_input.opts) and (opt.default is not None) and (opt.name in usage_opt_dict) and (not usage_opt_dict[opt.name].required):
                    user_input.opts[opt.name] = opt.default

            return user_input

    # If appropriate usage not found, return empty user input.
    return UserInput(pres={}, args={}, opts={})


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
