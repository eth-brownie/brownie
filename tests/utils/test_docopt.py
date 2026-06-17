from brownie._cli import init as init_mod
from brownie.utils.docopt import docopt


def test_init_force_flag_is_bool():
    args = docopt(init_mod.__doc__, ["init", "test/path", "--force"])
    assert type(args["--force"]) is bool
    assert args["--force"] is True
