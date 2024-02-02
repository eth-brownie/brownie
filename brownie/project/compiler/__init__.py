#!/usr/bin/python3

import json
from copy import deepcopy
from hashlib import sha1
from pathlib import Path
from typing import Dict, Optional, Union

import solcast
from eth_utils import remove_0x_prefix
from semantic_version import Version

from brownie._config import _get_data_folder
from brownie.exceptions import UnsupportedLanguage
from brownie.project import sources
from brownie.project.compiler.solidity import (  # NOQA: F401
    find_best_solc_version,
    find_solc_versions,
    install_solc,
    set_solc_version,
)
from brownie.project.compiler.utils import _get_alias, merge_natspec
from brownie.project.compiler.vyper import find_vyper_versions, set_vyper_version
from brownie.utils import notify

from . import solidity, vyper

STANDARD_JSON: Dict = {
    "language": None,
    "sources": {},
    "settings": {
        "outputSelection": {
            "*": {
                "*": ["abi", "devdoc", "evm.bytecode", "evm.deployedBytecode", "userdoc"],
                "": ["ast"],
            }
        },
        "evmVersion": None,
        "remappings": [],
    },
}


def compile_and_format(
    contract_sources: Dict[str, str],
    solc_version: Optional[str] = None,
    vyper_version: Optional[str] = None,
    optimize: bool = True,
    runs: int = 200,
    evm_version: Optional[Union[str, Dict[str, str]]] = None,
    silent: bool = True,
    allow_paths: Optional[str] = None,
    interface_sources: Optional[Dict[str, str]] = None,
    remappings: Optional[list] = None,
    optimizer: Optional[Dict] = None,
    viaIR: Optional[bool] = None,
) -> Dict:
    """Compiles contracts and returns build data.

    Args:
        contract_sources: a dictionary in the form of {'path': "source code"}
        solc_version: solc version to compile with (use None to set via pragmas)
        optimize: (deprecated) enable solc optimizer
        runs: (deprecated) optimizer runs
        evm_version: evm version to compile for
        silent: verbose reporting
        allow_paths: compiler allowed filesystem import path
        interface_sources: dictionary of interfaces as {'path': "source code"}
        remappings: list of solidity path remappings
        optimizer: dictionary of solidity optimizer settings
        viaIR: enable compilation pipeline to go through the Yul intermediate representation

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

    vyper_sources = {k: v for k, v in contract_sources.items() if Path(k).suffix == ".vy"}
    if vyper_sources:
        # TODO add `vyper_version` input arg to manually specify, support in config file
        if vyper_version is None:
            compiler_targets.update(
                find_vyper_versions(vyper_sources, install_needed=True, silent=silent)
            )
        else:
            compiler_targets[vyper_version] = list(vyper_sources)
    solc_sources = {k: v for k, v in contract_sources.items() if Path(k).suffix == ".sol"}
    if solc_sources:
        if solc_version is None:
            compiler_targets.update(
                find_solc_versions(solc_sources, install_needed=True, silent=silent)
            )
        else:
            compiler_targets[solc_version] = list(solc_sources)

        if optimizer is None:
            optimizer = {"enabled": optimize, "runs": runs if optimize else 0}

    for version, path_list in compiler_targets.items():
        compiler_data: Dict = {}
        if path_list[0].endswith(".vy"):
            set_vyper_version(version)
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
            to_compile,
            evm_version=evm_version[language] if isinstance(evm_version, dict) else evm_version,
            language=language,
            interface_sources=interfaces,
            remappings=remappings,
            optimizer=optimizer,
            viaIR=viaIR,
        )

        output_json = compile_from_input_json(input_json, silent, allow_paths)
        build_json.update(generate_build_json(input_json, output_json, compiler_data, silent))

    return build_json


def generate_input_json(
    contract_sources: Dict[str, str],
    optimize: bool = True,
    runs: int = 200,
    evm_version: Optional[str] = None,
    language: str = "Solidity",
    interface_sources: Optional[Dict[str, str]] = None,
    remappings: Optional[list] = None,
    optimizer: Optional[Dict] = None,
    viaIR: Optional[bool] = None,
) -> Dict:
    """Formats contracts to the standard solc input json.

    Args:
        contract_sources: a dictionary in the form of {path: 'source code'}
        optimize: (deprecated) enable solc optimizer
        runs: (deprecated) optimizer runs
        evm_version: evm version to compile for
        language: source language (Solidity or Vyper)
        interface_sources: dictionary of interfaces as {'path': "source code"}
        remappings: list of solidity path remappings
        optimizer: dictionary of solidity optimizer settings
        viaIR: enable compilation pipeline to go through the Yul intermediate representation

    Returns: dict
    """

    if language not in ("Solidity", "Vyper"):
        raise UnsupportedLanguage(f"{language}")

    if optimizer is None:
        optimizer = {"enabled": optimize, "runs": runs if optimize else 0}

    if evm_version is None:
        _module = solidity if language == "Solidity" else vyper
        evm_version = next(
            i[0] for i in _module.EVM_VERSION_MAPPING if _module.get_version() >= i[1]
        )

    input_json: Dict = deepcopy(STANDARD_JSON)
    input_json["language"] = language
    input_json["settings"]["evmVersion"] = evm_version
    if language == "Solidity":
        input_json["settings"]["optimizer"] = optimizer
        input_json["settings"]["remappings"] = _get_solc_remappings(remappings)
        if viaIR is not None:
            input_json["settings"]["viaIR"] = viaIR
    input_json["sources"] = _sources_dict(contract_sources, language)

    if interface_sources:
        if language == "Solidity":
            input_json["sources"].update(_sources_dict(interface_sources, language))
        else:
            input_json["interfaces"] = _sources_dict(interface_sources, language)

    return input_json


def _get_solc_remappings(remappings: Optional[list]) -> list:
    if remappings is None:
        remap_dict: Dict = {}
    elif isinstance(remappings, str):
        remap_dict = dict([remappings.split("=")])
    else:
        remap_dict = dict(i.split("=") for i in remappings)
    remapped_dict = {}
    packages = _get_data_folder().joinpath("packages")
    for path in packages.iterdir():
        key = next((k for k, v in remap_dict.items() if v.startswith(path.name)), None)
        if key:
            remapped_dict[key] = path.parent.joinpath(remap_dict.pop(key)).as_posix()
        else:
            remapped_dict[path.name] = path.as_posix()
    for k, v in remap_dict.items():
        if packages.joinpath(v).exists():
            remapped_dict[k] = packages.joinpath(v).as_posix()

    return [f"{k}={v}" for k, v in dict(remap_dict, **remapped_dict).items()]


def _get_allow_paths(allow_paths: Optional[str], remappings: list) -> str:
    # generate the final allow_paths field based on path remappings
    path_list = [] if allow_paths is None else [allow_paths]

    remapping_paths = [i[i.index("=") + 1 :] for i in remappings]
    data_path = _get_data_folder().joinpath("packages").as_posix()
    remapping_paths = [i for i in remapping_paths if not i.startswith(data_path)]

    path_list = path_list + [data_path] + remapping_paths
    return ",".join(path_list)


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
        allow_paths = _get_allow_paths(allow_paths, input_json["settings"]["remappings"])
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
    build_json: Dict = {}

    if input_json["language"] == "Solidity":
        compiler_data["optimizer"] = input_json["settings"]["optimizer"]
        source_nodes, statement_nodes, branch_nodes = solidity._get_nodes(output_json)

    for path_str, contract_name in [
        (k, x) for k, v in output_json["contracts"].items() for x in v.keys()
    ]:
        contract_alias = contract_name

        if path_str in input_json["sources"]:
            source = input_json["sources"][path_str]["content"]
        else:
            with Path(path_str).open(encoding="utf-8") as fp:
                source = fp.read()
            contract_alias = _get_alias(contract_name, path_str)

        if not silent:
            print(f" - {contract_alias}")

        abi = output_json["contracts"][path_str][contract_name]["abi"]
        natspec = merge_natspec(
            output_json["contracts"][path_str][contract_name].get("devdoc", {}),
            output_json["contracts"][path_str][contract_name].get("userdoc", {}),
        )
        output_evm = output_json["contracts"][path_str][contract_name]["evm"]
        if contract_alias in build_json and not output_evm["deployedBytecode"]["object"]:
            continue

        if input_json["language"] == "Solidity":
            contract_node = next(
                i[contract_name] for i in source_nodes if i.absolutePath == path_str
            )
            build_json[contract_alias] = solidity._get_unique_build_json(
                output_evm,
                contract_node,
                statement_nodes,
                branch_nodes,
                next((True for i in abi if i["type"] == "fallback"), False),
            )

        else:
            if contract_name == "<stdin>":
                contract_name = contract_alias = "Vyper"
            build_json[contract_alias] = vyper._get_unique_build_json(
                output_evm,
                path_str,
                contract_alias,
                output_json["sources"][path_str]["ast"],
                (0, len(source)),
            )

        build_json[contract_alias].update(
            {
                "abi": abi,
                "ast": output_json["sources"][path_str]["ast"],
                "compiler": compiler_data,
                "contractName": contract_name,
                "deployedBytecode": output_evm["deployedBytecode"]["object"],
                "deployedSourceMap": output_evm["deployedBytecode"]["sourceMap"],
                "language": input_json["language"],
                "natspec": natspec,
                "opcodes": output_evm["deployedBytecode"]["opcodes"],
                "sha1": sha1(source.encode()).hexdigest(),
                "source": source,
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


def _sources_dict(original: Dict, language: str) -> Dict:
    result: Dict = {}
    for key, value in original.items():
        if Path(key).suffix == ".json":
            if isinstance(value, str):
                value = json.loads(value)
            result[key] = {"abi": value}
        else:
            result[key] = {"content": value}
    return result


def get_abi(
    contract_sources: Dict[str, str],
    solc_version: Optional[str] = None,
    allow_paths: Optional[str] = None,
    remappings: Optional[list] = None,
    silent: bool = True,
) -> Dict:
    """
    Generate ABIs from contract interfaces.

    Arguments
    ---------
    contract_sources : dict
        a dictionary in the form of {'path': "source code"}
    solc_version: solc version to compile with (use None to set via pragmas)
    allow_paths : str, optional
        Compiler allowed filesystem import path
    remappings : list, optional
        List of solidity path remappings
    silent : bool, optional
        Disable verbose reporting

    Returns
    -------
    dict
        Compiled ABIs in the format `{'contractName': [ABI]}`
    """

    final_output = {
        Path(k).stem: {
            "abi": json.loads(v),
            "contractName": Path(k).stem,
            "type": "interface",
            "source": None,
            "offset": None,
            "sha1": sha1(v.encode()).hexdigest(),
        }
        for k, v in contract_sources.items()
        if Path(k).suffix == ".json"
    }

    for path, source in [(k, v) for k, v in contract_sources.items() if Path(k).suffix == ".vy"]:
        input_json = generate_input_json({path: source}, language="Vyper")
        input_json["settings"]["outputSelection"]["*"] = {"*": ["abi"]}
        try:
            output_json = compile_from_input_json(input_json, silent, allow_paths)
        except Exception:
            # vyper interfaces do not convert to ABIs
            # https://github.com/vyperlang/vyper/issues/1944
            continue
        name = Path(path).stem
        final_output[name] = {
            "abi": output_json["contracts"][path][name]["abi"],
            "contractName": name,
            "type": "interface",
            "source": source,
            "offset": [0, len(source)],
            "sha1": sha1(contract_sources[path].encode()).hexdigest(),
        }

    solc_sources = {k: v for k, v in contract_sources.items() if Path(k).suffix == ".sol"}

    if not solc_sources:
        return final_output

    if solc_version:
        compiler_targets = {solc_version: list(solc_sources)}
    else:
        compiler_targets = find_solc_versions(solc_sources, install_needed=True, silent=silent)

    for version, path_list in compiler_targets.items():
        to_compile = {k: v for k, v in contract_sources.items() if k in path_list}

        set_solc_version(version)
        input_json = generate_input_json(to_compile, language="Solidity", remappings=remappings)
        input_json["settings"]["outputSelection"]["*"] = {"*": ["abi"], "": ["ast"]}

        output_json = compile_from_input_json(input_json, silent, allow_paths)
        source_nodes = solcast.from_standard_output(output_json)
        abi_json = {k: v for k, v in output_json["contracts"].items() if k in path_list}

        for path, name, data in [(k, x, y) for k, v in abi_json.items() for x, y in v.items()]:
            contract_node = next(i[name] for i in source_nodes if i.absolutePath == path)
            dependencies = []
            for node in [
                i for i in contract_node.dependencies if i.nodeType == "ContractDefinition"
            ]:
                dependency_name = node.name
                path_str = node.parent().absolutePath
                dependencies.append(_get_alias(dependency_name, path_str))

            final_output[name] = {
                "abi": data["abi"],
                "ast": output_json["sources"][path]["ast"],
                "contractName": name,
                "dependencies": dependencies,
                "type": "interface",
                "source": contract_sources[path],
                "offset": contract_node.offset,
                "sha1": sha1(contract_sources[path].encode()).hexdigest(),
            }

    return final_output
