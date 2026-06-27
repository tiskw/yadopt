"""
yadopt.default - resolve default values of options in the argument vector.
"""
from __future__ import annotations

# Import standard libraries.
import dataclasses

# Import custom modules.
from .argvec  import ParsedArgVec
from .declaration  import PosArgDecl, OptArgDecl


@dataclasses.dataclass(frozen=True)
class DefaultResolvedArgVec:
    """
    Information of user input.
    """
    pos_args: dict[str, str | list[str]]
    opt_args: dict[str, str | None]

    def __str__(self) -> str:
        text  = self.__class__.__name__ + ":\n"
        text += " |- pos_args = " + str(self.pos_args) + "\n"
        text += " |- opt_args = " + str(self.opt_args)
        return text.strip()

    def validate(self, pos_args: list[PosArgDecl], opt_args: list[OptArgDecl]) -> None:
        """
        Run extra validation checks. This function is called only when running tests.
        This is a post-condition assertion in the context of DbC methodology.
        """
        # All variables are not typed yet, that is, all values are strings or lists of strings.
        for pos_value in self.pos_args.values():
            assert isinstance(pos_value, (str, list))
            if isinstance(pos_value, list) and len(pos_value) > 0:
                assert all(isinstance(item, str) for item in pos_value)
        for opt_value in self.opt_args.values():
            assert isinstance(opt_value, str) or opt_value is None

        # All positional arguments appear in the pos_args.
        for pos_arg_decl in pos_args:
            name = pos_arg_decl.spec.name
            assert name in self.pos_args, f"Positional argument '{name}' is missing in pos_args."

        # All optional arguments appear in the optargs.
        for opt_arg_decl in opt_args:
            n1 = opt_arg_decl.spec.name
            n2 = opt_arg_decl.spec.name_alt
            assert n1 in self.opt_args or n2 in self.opt_args, f"Option argument '{n1}' is missing in opt_args."


class DefaultValueResolver:
    """
    Resolve default values of options in the argument vector based on the option declarations.
    """
    def __init__(self, argvec: ParsedArgVec, optargs: list[OptArgDecl], verbose: bool) -> None:
        """
        Constructor.

        Args:
            argvec  (ParsedArgVec)     : [IN] Parsed argument vector.
            optargs (list[OptArgDecl]) : [IN] List of option declarations.
        """
        self.argvec : ParsedArgVec     = argvec
        self.optargs: list[OptArgDecl] = optargs
        self.verbose: bool             = verbose

    def resolve(self) -> DefaultResolvedArgVec:
        """
        Fill default values of options if not specified in the argument vector.

        Returns:
            (DefaultResolvedArgVec): Argument vector with default values filled in.
        """
        opt_args: dict[str, str | None] = {}

        for key, value in self.argvec.optargs.items():
            opt_args[key] = value

        for opt_arg_decl in self.optargs:
            if opt_args.get(opt_arg_decl.spec.name, None) is None:
                opt_args[opt_arg_decl.spec.name] = opt_arg_decl.desc.default

        return DefaultResolvedArgVec(pos_args=self.argvec.posargs, opt_args=opt_args)


# vim: expandtab tabstop=4 shiftwidth=4 fdm=marker
