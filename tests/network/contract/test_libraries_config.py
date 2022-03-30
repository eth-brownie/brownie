"""
Test `brownie-config.yaml` `libraries` fields
"""
import pytest

from brownie.exceptions import BrownieConfigError
from brownie.project import load, new

CONFIG_TEMPLATE = """
libraries:
  {name1}: {address1}
  {name2}: {address2}
"""


def test_errors_with_wrong_addresses(tmp_path_factory):
    dir = tmp_path_factory.mktemp("temp-project")
    new(dir.as_posix())

    data = {"name1": "lib1", "address1": None, "name2": "lib2", "address2": "dummy-addres"}

    wrong_addresses = (
        f"""' 0x{40*'A'}'""",
        f"""'0x{40*'B'} '""",
        f"""'{20*'ff'}'""",
        f"""'{21*'0x'}'""",
        """'dummy-string'""",
        f"""'0x{20*'GH'}'""",
        f"""'0x{20*'4J'}'""",
    )

    for addr in wrong_addresses:
        data["address1"] = addr
        with open(dir.joinpath("brownie-config.yaml"), "w") as file:
            file.write(CONFIG_TEMPLATE.format(**data))
        with pytest.raises(BrownieConfigError) as error:
            load(dir, f"proj_{addr}").close()
        assert f"Passed lib1 with {addr}" in str(error.value)


def test_libraries_config_loading(tmp_path_factory):
    dir = tmp_path_factory.mktemp("temp-project")
    new(dir.as_posix())

    data = {"name1": "lib1", "address1": None, "name2": "lib2", "address2": "dummy-addres"}

    correct_addresses = (
        f"""'0x{20*'ab'}'""",
        f"""'0x{20*'9c'}'""",
        f"""'0x{20*'D5'}'""",
        f"""'0x{20*'EE'}'""",
    )

    for i in range(len(correct_addresses) - 1):
        data["address1"] = correct_addresses[i]
        data["address2"] = correct_addresses[i + 1]
        with open(dir.joinpath("brownie-config.yaml"), "w") as file:
            file.write(CONFIG_TEMPLATE.format(**data))
        load(dir, f"proj_{i}").close()


def test_address_dubling(tmp_path_factory):
    dir = tmp_path_factory.mktemp("temp-project")
    new(dir.as_posix())

    data = {"name1": "lib1", "address1": None, "name2": "lib2", "address2": "dummy-addres"}

    correct_addresses = (
        f"""'0x{20*'ab'}'""",
        f"""'0x{20*'9c'}'""",
        f"""'0x{20*'D5'}'""",
        f"""'0x{20*'EE'}'""",
    )

    for addr in correct_addresses:
        data["address1"] = addr
        data["address2"] = addr
        with open(dir.joinpath("brownie-config.yaml"), "w") as file:
            file.write(CONFIG_TEMPLATE.format(**data))
        with pytest.raises(BrownieConfigError) as error:
            load(dir, f"proj_{addr}").close()
        assert f"Address {addr} is the same for 'lib1'" in str(error.value)
