#!/usr/bin/python3

import shutil

from brownie import project
from brownie._config import _load_project_structure_config
from brownie.exceptions import ProjectNotFound
from brownie.utils import color
from brownie.utils.docopt import docopt

CODESIZE_COLORS = [(1, "bright red"), (0.8, "bright yellow")]

__doc__ = """Usage: brownie compile [<contract> ...] [options]

Arguments
  [<contract> ...]       Optional list of contract names to compile.

Options:
  --all -a              Recompile all contracts
  --size -s             Show deployed bytecode sizes contracts
  --help -h             Display this message

Compiles the contract source files for this project and saves the results
in the build/contracts/ folder.

Note that Brownie automatically recompiles any changed contracts each time
a project is loaded. You do not have to manually trigger a recompile."""


def main():
    args = docopt(__doc__)
    project_path = project.check_for_project(".")
    if project_path is None:
        raise ProjectNotFound

    build_path = project_path.joinpath(_load_project_structure_config(project_path)["build"])

    contract_artifact_path = build_path.joinpath("contracts")
    interface_artifact_path = build_path.joinpath("interfaces")

    if args["--all"]:
        shutil.rmtree(contract_artifact_path, ignore_errors=True)
        shutil.rmtree(interface_artifact_path, ignore_errors=True)
    elif args["<contract>"]:
        for name in args["<contract>"]:
            path = contract_artifact_path.joinpath(f"{name}.json")
            if path.exists():
                path.unlink()

    proj = project.load()

    if args["--size"]:
        print("============ Deployment Bytecode Sizes ============")
        codesize = []
        for contract in proj:
            bytecode = contract._build["deployedBytecode"]
            if bytecode:
                codesize.append((contract._name, len(bytecode) // 2))
        indent = max(len(i[0]) for i in codesize)
        for name, size in sorted(codesize, key=lambda k: k[1], reverse=True):
            pct = size / 24577
            pct_color = color(next((i[1] for i in CODESIZE_COLORS if pct >= i[0]), ""))
            print(f"  {name:<{indent}}  -  {size:>6,}B  ({pct_color}{pct:.2%}{color})")
        print()

    print(f"Project has been compiled. Build artifacts saved at {contract_artifact_path}")
