import shutil

import click

from brownie import project
from brownie._config import _load_project_structure_config
from brownie.exceptions import ProjectNotFound
from brownie.utils import color

CODESIZE_COLORS = [(1, "bright red"), (0.8, "bright yellow")]


@click.command(short_help="Compile the contract source files")
@click.argument("contracts", type=str, nargs=-1)
@click.option(
    "-a", "--all", "compile_all", default=False, is_flag=True, help="Recompile all contracts"
)
@click.option(
    "-s",
    "--size",
    "display_size",
    default=False,
    is_flag=True,
    help="Show deployed bytecode sizes contracts",
)
def cli(contracts, compile_all, display_size):
    """
    Compiles the contract source files for this project and saves the results
    in the build/contracts/ folder.

    An optional list of specific CONTRACTS can be provided.

    Note that Brownie automatically recompiles any changed contracts each time
    a project is loaded. You do not have to manually trigger a recompile."""
    project_path = project.check_for_project(".")
    if project_path is None:
        raise ProjectNotFound

    build_path = project_path.joinpath(_load_project_structure_config(project_path)["build"])

    contract_artifact_path = build_path.joinpath("contracts")
    interface_artifact_path = build_path.joinpath("interfaces")

    if compile_all:
        shutil.rmtree(contract_artifact_path, ignore_errors=True)
        shutil.rmtree(interface_artifact_path, ignore_errors=True)
    elif contracts:
        for name in contracts:
            path = contract_artifact_path.joinpath(f"{name}.json")
            if path.exists():
                path.unlink()

    proj = project.load()

    if display_size:
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
