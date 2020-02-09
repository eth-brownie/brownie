#!/usr/bin/python3

import json
from copy import deepcopy
from pathlib import Path
from typing import Dict, Optional, Union

from eth_utils import remove_0x_prefix
from semantic_version import Version

from brownie.exceptions import UnsupportedLanguage
from brownie.project import sources
from brownie.project.compiler.solidity import (  # NOQA: F401
    find_best_solc_version,
    find_solc_versions,
    install_solc,
    set_solc_version,
)
from brownie.utils import notify

from . import solidity, vyper

STANDARD_JSON: Dict = {
    "language": None,
    "sources": {},
    "settings": {
        "outputSelection": {
            "*": {"*": ["abi", "evm.bytecode", "evm.deployedBytecode"], "": ["ast"]}
        },
        "evmVersion": None,
        "remappings": [],
    },
}
EVM_SOLC_VERSIONS = [
    ("istanbul", Version("0.5.13")),
    ("petersburg", Version("0.5.5")),
    ("byzantium", Version("0.4.0")),
]


def compile_and_format(
    contract_sources: Dict[str, str],
    solc_version: Optional[str] = None,
    optimize: bool = True,
    runs: int = 200,
    evm_version: int = None,
    minify: bool = False,
    silent: bool = True,
    allow_paths: Optional[str] = None,
    interface_sources: Optional[Dict[str, str]] = None,
) -> Dict:
    """Compiles contracts and returns build data.

    Args:
        contracts: a dictionary in the form of {'path': "source code"}
        solc_version: solc version to compile with (use None to set via pragmas)
        optimize: enable solc optimizer
        runs: optimizer runs
        evm_version: evm version to compile for
        minify: minify source files
        silent: verbose reporting
        allow_paths: compiler allowed filesystem import path

    Returns:
        build data dict
    """
    if not contract_sources:
        return {}
    if interface_sources is None:
        interface_sources = {}

    if [i for i in contract_sources if Path(i).suffix not in (".sol", ".vy")]:
        raise UnsupportedLanguage("Source suffixes must be one of ('.sol', '.vy')")
    if [i for i in interface_sources if Path(i).suffix not in (".sol", ".vy", ".json")]:
        raise UnsupportedLanguage("Interface suffixes must be one of ('.sol', '.vy', '.json')")

    build_json: Dict = {}
    compiler_targets = {}

    vyper_paths = [i for i in contract_sources if Path(i).suffix == ".vy"]
    if vyper_paths:
        compiler_targets["vyper"] = vyper_paths

    solc_sources = {k: v for k, v in contract_sources.items() if Path(k).suffix == ".sol"}
    if solc_sources:
        if solc_version is None:
            compiler_targets.update(
                find_solc_versions(solc_sources, install_needed=True, silent=silent)
            )
        else:
            compiler_targets[solc_version] = list(solc_sources)

    for version, path_list in compiler_targets.items():
        compiler_data: Dict = {"minify_source": minify}
        if version == "vyper":
            language = "Vyper"
            compiler_data["version"] = str(vyper.get_version())
            interfaces = {k: v for k, v in interface_sources.items() if Path(k).suffix != ".sol"}
        else:
            set_solc_version(version)
            language = "Solidity"
            compiler_data["version"] = str(solidity.get_version())
            interfaces = {
                k: v
                for k, v in interface_sources.items()
                if Path(k).suffix == ".sol" and Version(version) in sources.get_pragma_spec(v, k)
            }

        to_compile = {k: v for k, v in contract_sources.items() if k in path_list}

        input_json = generate_input_json(
            to_compile, optimize, runs, evm_version, minify, language, interfaces
        )
        output_json = compile_from_input_json(input_json, silent, allow_paths)

        output_json["contracts"] = {
            k: v for k, v in output_json["contracts"].items() if k in path_list
        }

        build_json.update(generate_build_json(input_json, output_json, compiler_data, silent))
    return build_json


def generate_input_json(
    contract_sources: Dict[str, str],
    optimize: bool = True,
    runs: int = 200,
    evm_version: Union[int, str, None] = None,
    minify: bool = False,
    language: str = "Solidity",
    interface_sources: Optional[Dict[str, str]] = None,
) -> Dict:

    """Formats contracts to the standard solc input json.

    Args:
        contract_sources: a dictionary in the form of {path: 'source code'}
        optimize: enable solc optimizer
        runs: optimizer runs
        evm_version: evm version to compile for
        minify: should source code be minified?
        language: source language (Solidity or Vyper)

    Returns: dict
    """

    if language not in ("Solidity", "Vyper"):
        raise UnsupportedLanguage(f"{language}")

    if evm_version is None:
        if language == "Solidity":
            evm_version = next(i[0] for i in EVM_SOLC_VERSIONS if solidity.get_version() >= i[1])
        else:
            evm_version = "istanbul"

    input_json: Dict = deepcopy(STANDARD_JSON)
    input_json["language"] = language
    input_json["settings"]["evmVersion"] = evm_version
    if language == "Solidity":
        input_json["settings"]["optimizer"] = {"enabled": optimize, "runs": runs if optimize else 0}
    input_json["sources"] = _sources_dict(contract_sources, minify, language)

    if interface_sources:
        if language == "Solidity":
            input_json["sources"].update(_sources_dict(interface_sources, False, language))
        else:
            input_json["interfaces"] = _sources_dict(interface_sources, False, language)

    return input_json


def compile_from_input_json(
    input_json: Dict, silent: bool = True, allow_paths: Optional[str] = None
) -> Dict:

    """
    Compiles contracts from a standard input json.

    Args:
        input_json: solc input json
        silent: verbose reporting
        allow_paths: compiler allowed filesystem import path

    Returns: standard compiler output json
    """

    if input_json["language"] == "Vyper":
        return vyper.compile_from_input_json(input_json, silent, allow_paths)
    if input_json["language"] == "Solidity":
        return solidity.compile_from_input_json(input_json, silent, allow_paths)
    raise UnsupportedLanguage(f"{input_json['language']}")


def generate_build_json(
    input_json: Dict, output_json: Dict, compiler_data: Optional[Dict] = None, silent: bool = True
) -> Dict:
    """Formats standard compiler output to the brownie build json.

    Args:
        input_json: solc input json used to compile
        output_json: output json returned by compiler
        compiler_data: additonal data to include under 'compiler' in build json
        silent: verbose reporting

    Returns: build json dict"""

    if input_json["language"] not in ("Solidity", "Vyper"):
        raise UnsupportedLanguage(f"{input_json['language']}")

    if not silent:
        print("Generating build data...")

    if compiler_data is None:
        compiler_data = {}
    compiler_data["evm_version"] = input_json["settings"]["evmVersion"]
    minified = compiler_data.get("minify_source", False)
    build_json = {}
    path_list = list(input_json["sources"])

    if input_json["language"] == "Solidity":
        compiler_data.update(
            {
                "optimize": input_json["settings"]["optimizer"]["enabled"],
                "runs": input_json["settings"]["optimizer"]["runs"],
            }
        )
        source_nodes, statement_nodes, branch_nodes = solidity._get_nodes(output_json)

    for path_str, contract_name in [
        (k, v) for k in path_list for v in output_json["contracts"].get(k, {})
    ]:

        if not silent:
            print(f" - {contract_name}...")

        abi = output_json["contracts"][path_str][contract_name]["abi"]
        output_evm = output_json["contracts"][path_str][contract_name]["evm"]
        hash_ = sources.get_hash(
            input_json["sources"][path_str]["content"],
            contract_name,
            minified,
            input_json["language"],
        )

        if input_json["language"] == "Solidity":
            contract_node = next(
                i[contract_name] for i in source_nodes if i.absolutePath == path_str
            )
            build_json[contract_name] = solidity._get_unique_build_json(
                output_evm,
                contract_node,
                statement_nodes,
                branch_nodes,
                next((True for i in abi if i["type"] == "fallback"), False),
            )

        else:
            if contract_name == "<stdin>":
                contract_name = "Vyper"
            build_json[contract_name] = vyper._get_unique_build_json(
                output_evm,
                path_str,
                contract_name,
                output_json["sources"][path_str]["ast"],
                (0, len(input_json["sources"][path_str]["content"])),
            )

        build_json[contract_name].update(
            {
                "abi": abi,
                "ast": output_json["sources"][path_str]["ast"],
                "compiler": compiler_data,
                "contractName": contract_name,
                "deployedBytecode": output_evm["deployedBytecode"]["object"],
                "deployedSourceMap": output_evm["deployedBytecode"]["sourceMap"],
                "language": input_json["language"],
                "opcodes": output_evm["deployedBytecode"]["opcodes"],
                "sha1": hash_,
                "source": input_json["sources"][path_str]["content"],
                "sourceMap": output_evm["bytecode"].get("sourceMap", ""),
                "sourcePath": path_str,
            }
        )
        size = len(remove_0x_prefix(output_evm["deployedBytecode"]["object"])) / 2  # type: ignore
        if size > 24577:
            notify(
                "WARNING",
                f"deployed size of {contract_name} is {size} bytes, exceeds EIP-170 limit of 24577",
            )

    if not silent:
        print("")

    return build_json


def _sources_dict(original: Dict, minify: bool, language: str) -> Dict:
    result: Dict = {}
    for key, value in original.items():
        if Path(key).suffix == ".json":
            if isinstance(value, str):
                value = json.loads(value)
            result[key] = {"abi": value}
        else:
            result[key] = {"content": sources.minify(value, language)[0] if minify else value}
    return result
