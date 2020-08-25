#!/usr/bin/python3

from pathlib import Path

import yaml

structure = {
    "project_structure": {
        "build": "artifacts",
        "contracts": "sources",
        "interfaces": "abi",
        "reports": "logs",
        "scripts": "automation",
        "tests": "checks",
    }
}


def test_different_folders(project, tmp_path):

    with tmp_path.joinpath("brownie-config.yaml").open("w") as fp:
        yaml.dump(structure, fp)

    project.main._create_folders(Path(tmp_path))
    for path in ("contracts", "interfaces", "scripts", "reports", "tests", "build"):
        assert not Path(tmp_path).joinpath(path).exists()

    for path in ("artifacts", "sources", "abi", "logs", "automation", "checks"):
        assert Path(tmp_path).joinpath(path).exists()


def test_compiles(project, tmp_path):
    with tmp_path.joinpath("brownie-config.yaml").open("w") as fp:
        yaml.dump(structure, fp)

    tmp_path.joinpath("sources").mkdir()
    with tmp_path.joinpath("sources/Foo.vy").open("w") as fp:
        fp.write(
            """# @version 0.2.4
@external
def foo() -> int128:
    return 2
"""
        )

    tmp_path.joinpath("abi").mkdir()
    with tmp_path.joinpath("abi/Bar.json").open("w") as fp:
        fp.write("[]")

    proj = project.load(tmp_path)

    assert "Foo" in proj._containers
    assert proj._path.joinpath("artifacts/contracts/Foo.json").exists()
    assert hasattr(proj.interface, "Bar")
