#!/usr/bin/python3
# mypy: disable-error-code="index,typeddict-unknown-key"

from typing import Any, Dict, Final, List, Optional, Union, cast

import solcast
from eth_typing import ABIElement, HexStr

from brownie._c_constants import Path, Version, deepcopy, sha1, ujson_loads
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
from brownie.typing import (
    CompilerConfig,
    ContractBuildJson,
    ContractName,
    EvmVersion,
    InputJson,
    InputJsonSolc,
    InputJsonVyper,
    InterfaceBuildJson,
    InterfaceSource,
    Language,
    OptimizerSettings,
    SettingsSolc,
    SourcesDict,
)
from brownie.utils import notify

from . import solidity, vyper

STANDARD_JSON: Final[InputJson] = {  # type: ignore [assignment]
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

EvmVersionSpec = Union[EvmVersion, Dict[Language, EvmVersion | None]]


# C constants
_from_standard_output: Final = solcast.from_standard_output


def compile_and_format(
    contract_sources: Dict[str, str],
    solc_version: Optional[str] = None,
    vyper_version: Optional[str] = None,
    optimize: Optional[bool] = True,
    runs: Optional[int] = 200,
    evm_version: Optional[EvmVersionSpec] = None,
    silent: bool = True,
    allow_paths: Optional[str] = None,
    interface_sources: Optional[Dict[str, str]] = None,
    remappings: Optional[Union[List[str], str]] = None,
    optimizer: Optional[OptimizerSettings] = None,
    viaIR: Optional[bool] = None,
) -> Dict[ContractName, ContractBuildJson]:
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

    build_json: Dict[ContractName, ContractBuildJson] = {}
    compiler_targets = {}

    vyper_sources = {
        key: contract_sources[key] for key in contract_sources if Path(key).suffix == ".vy"
    }
    if vyper_sources:
        # TODO add `vyper_version` input arg to manually specify, support in config file
        if vyper_version is None:
            compiler_targets.update(
                find_vyper_versions(vyper_sources, install_needed=True, silent=silent)
            )
        else:
            compiler_targets[vyper_version] = list(vyper_sources)

    solc_sources = {
        key: contract_sources[key] for key in contract_sources if Path(key).suffix == ".sol"
    }
    if solc_sources:
        if solc_version is None:
            compiler_targets.update(
                find_solc_versions(solc_sources, install_needed=True, silent=silent)
            )
        else:
            compiler_targets[solc_version] = list(solc_sources)

        if optimizer is None:
            if optimize:
                optimizer = {"enabled": True, "runs": runs or 0}
            else:
                optimizer = {"enabled": False, "runs": 0}

    language: Language
    compiler_data: CompilerConfig
    for version, path_list in compiler_targets.items():
        compiler_data = {}  # type: ignore [typeddict-item]
        if path_list[0].endswith(".vy"):
            set_vyper_version(version)
            language = "Vyper"
            compiler_data["version"] = str(vyper.get_version())
            interfaces = {
                key: interface_sources[key]
                for key in interface_sources
                if Path(key).suffix != ".sol"
            }
        else:
            set_solc_version(version)
            language = "Solidity"
            compiler_data["version"] = str(solidity.get_version())
            interfaces = {
                k: v
                for k in interface_sources
                if Path(k).suffix == ".sol"
                and Version(version) in sources.get_pragma_spec(v := interface_sources[k], k)
            }

        to_compile = {key: contract_sources[key] for key in contract_sources if key in path_list}

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
    evm_version: Optional[EvmVersion] = None,
    language: Language = "Solidity",
    interface_sources: Optional[Dict[str, str]] = None,
    remappings: Optional[Union[List[str], str]] = None,
    optimizer: Optional[OptimizerSettings] = None,
    viaIR: Optional[bool] = None,
) -> InputJson:
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

    input_json = deepcopy(STANDARD_JSON)
    input_json["language"] = language  # type: ignore [arg-type]
    settings = input_json["settings"]
    settings["evmVersion"] = evm_version
    if language == "Solidity":
        settings["optimizer"] = optimizer
        settings["remappings"] = _get_solc_remappings(remappings)
        if viaIR is not None:
            settings["viaIR"] = viaIR

    input_sources = _sources_dict(contract_sources, language)
    input_json["sources"] = input_sources

    if interface_sources:
        if language == "Solidity":
            input_sources.update(_sources_dict(interface_sources, language))
        else:
            input_json["interfaces"] = cast(
                Dict[str, InterfaceSource],
                _sources_dict(interface_sources, language),
            )

    return input_json


def _get_solc_remappings(remappings: Optional[Union[List[str], str]]) -> List[str]:
    remap_dict: Dict[str, str]
    if remappings is None:
        remap_dict = {}
    elif isinstance(remappings, str):
        remap_dict = dict([remappings.split("=")])
    else:
        remap_dict = dict(i.split("=") for i in remappings)
    remapped_dict: Dict[str, str] = {}
    packages = _get_data_folder().joinpath("packages")
    for path in packages.iterdir():
        pathname = path.name
        key = next((k for k, v in remap_dict.items() if v.startswith(pathname)), None)
        if key:
            remapped_dict[key] = path.parent.joinpath(remap_dict.pop(key)).as_posix()
        else:
            remapped_dict[pathname] = path.as_posix()
    for k, v in remap_dict.items():
        if packages.joinpath(v).exists():
            remapped_dict[k] = packages.joinpath(v).as_posix()

    return [f"{k}={v}" for k, v in dict(remap_dict, **remapped_dict).items()]


def _get_allow_paths(allow_paths: Optional[str], remappings: List[str]) -> str:
    # generate the final allow_paths field based on path remappings
    path_list = [] if allow_paths is None else [allow_paths]

    remapping_paths = [i[i.index("=") + 1 :] for i in remappings]
    data_path = _get_data_folder().joinpath("packages").as_posix()
    remapping_paths = [i for i in remapping_paths if not i.startswith(data_path)]

    path_list = path_list + [data_path] + remapping_paths
    return ",".join(path_list)


def compile_from_input_json(
    input_json: InputJson, silent: bool = True, allow_paths: Optional[str] = None
) -> Dict:
    """
    Compiles contracts from a standard input json.

    Args:
        input_json: solc input json
        silent: verbose reporting
        allow_paths: compiler allowed filesystem import path

    Returns: standard compiler output json
    """

    language = cast(Language, input_json["language"])
    if language == "Vyper":
        return vyper.compile_from_input_json(cast(InputJsonVyper, input_json), silent, allow_paths)

    if language == "Solidity":
        settings = cast(SettingsSolc, input_json["settings"])
        allow_paths = _get_allow_paths(allow_paths, settings["remappings"])
        return solidity.compile_from_input_json(
            cast(InputJsonSolc, input_json), silent, allow_paths
        )

    raise UnsupportedLanguage(language)


def generate_build_json(
    input_json: InputJson,
    output_json: Dict,
    compiler_data: Optional[CompilerConfig] = None,
    silent: bool = True,
) -> Dict[ContractName, ContractBuildJson]:
    """Formats standard compiler output to the brownie build json.

    Args:
        input_json: solc input json used to compile
        output_json: output json returned by compiler
        compiler_data: additonal data to include under 'compiler' in build json
        silent: verbose reporting

    Returns: build json dict"""

    language = input_json["language"]
    if language not in ("Solidity", "Vyper"):
        raise UnsupportedLanguage(language)

    if not silent:
        print("Generating build data...")

    compiler_data = compiler_data or {}  # type: ignore [assignment]

    settings = input_json["settings"]
    compiler_data["evm_version"] = settings["evmVersion"]
    build_json: Dict[ContractName, ContractBuildJson] = {}

    if language == "Solidity":
        compiler_data["optimizer"] = settings["optimizer"]  # type: ignore [typeddict-item]
        source_nodes, statement_nodes, branch_nodes = solidity._get_nodes(output_json)

    sources = input_json["sources"]
    contracts: Dict[str, Dict[ContractName, dict]] = output_json["contracts"]

    for path_str, path_contracts in contracts.items():
        if path_str in sources:
            source: str = sources[path_str]["content"]  # type: ignore [typeddict-item]
            get_alias = False
        else:
            with Path(path_str).open(encoding="utf-8") as fp:
                source = fp.read()
            get_alias = True

        for contract_name, contract in path_contracts.items():
            if get_alias:
                contract_alias = _get_alias(contract_name, path_str)
            else:
                contract_alias = contract_name

            if not silent:
                print(f" - {contract_alias}")

            natspec = merge_natspec(contract.get("devdoc", {}), contract.get("userdoc", {}))

            abi: List[ABIElement] = contract["abi"]
            output_evm: dict = contract["evm"]
            deployed_bytecode: dict = output_evm["deployedBytecode"]
            bytecode: HexStr = deployed_bytecode["object"]

            if contract_alias in build_json and not bytecode:
                continue

            ast = output_json["sources"][path_str]["ast"]

            if language == "Solidity":
                contract_node = next(
                    i[contract_name] for i in source_nodes if i.absolutePath == path_str
                )
                build_json[contract_alias] = solidity._get_unique_build_json(
                    output_evm,
                    contract_node,
                    statement_nodes,
                    branch_nodes,
                    any(i["type"] == "fallback" for i in abi),
                )

            else:
                if contract_name == "<stdin>":
                    contract_name = contract_alias = ContractName("Vyper")
                build_json[contract_alias] = vyper._get_unique_build_json(
                    output_evm,
                    path_str,
                    contract_alias,
                    ast,
                    (0, len(source)),
                )

            build_json[contract_alias].update(
                {
                    "abi": abi,
                    "ast": ast,
                    "compiler": compiler_data,  # type: ignore [typeddict-item]
                    "contractName": contract_name,
                    "deployedBytecode": bytecode,
                    "deployedSourceMap": deployed_bytecode["sourceMap"],
                    "language": language,  # type: ignore [typeddict-item]
                    "natspec": natspec,
                    "opcodes": deployed_bytecode["opcodes"],
                    "sha1": HexStr(sha1(source.encode()).hexdigest()),
                    "source": source,
                    "sourceMap": output_evm["bytecode"].get("sourceMap", ""),
                    "sourcePath": path_str,
                }
            )
            size = len(bytecode.removeprefix("0x")) / 2
            if size > 24577:
                notify(
                    "WARNING",
                    f"deployed size of {contract_name} is {size} bytes, "
                    "exceeds EIP-170 limit of 24577",
                )

    if not silent:
        print("")

    return build_json


def _sources_dict(original: Dict[str, Any], language: Language) -> SourcesDict:
    result: SourcesDict = {}
    for key, value in original.items():
        if Path(key).suffix == ".json":
            if isinstance(value, str):
                value = ujson_loads(value)
            result[key] = {"abi": value}
        else:
            result[key] = {"content": value}
    return result


def get_abi(
    contract_sources: Dict[str, str],
    solc_version: Optional[str] = None,
    allow_paths: Optional[str] = None,
    remappings: Optional[List[str]] = None,
    silent: bool = True,
) -> Dict[ContractName, InterfaceBuildJson]:
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

    final_output: Dict[ContractName, InterfaceBuildJson] = {
        ContractName(stem := p.stem): {
            "abi": ujson_loads(v),
            "contractName": ContractName(stem),
            "type": "interface",
            "source": None,
            "offset": None,
            "sha1": HexStr(sha1(v.encode()).hexdigest()),
        }
        for k, v in contract_sources.items()
        if (p := Path(k)).suffix == ".json"
    }

    for path, source in contract_sources.items():
        if Path(path).suffix == ".vy":
            input_json = generate_input_json({path: source}, language="Vyper")
            input_json["settings"]["outputSelection"]["*"] = {"*": ["abi"]}
            try:
                output_json = compile_from_input_json(input_json, silent, allow_paths)
            except Exception:
                # vyper interfaces do not convert to ABIs
                # https://github.com/vyperlang/vyper/issues/1944
                continue
            name = ContractName(Path(path).stem)
            final_output[name] = {
                "abi": output_json["contracts"][path][name]["abi"],
                "contractName": name,
                "type": "interface",
                "source": source,
                "offset": (0, len(source)),
                "sha1": HexStr(sha1(contract_sources[path].encode()).hexdigest()),
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
        source_nodes = _from_standard_output(output_json)
        compiled_sources: dict[str, dict] = output_json["sources"]
        abi_json: Dict[str, dict] = {
            k: v for k, v in output_json["contracts"].items() if k in path_list
        }

        for path, contracts in abi_json.items():
            path_source = contract_sources[path]
            for name, data in contracts.items():
                contract_node = next(i[name] for i in source_nodes if i.absolutePath == path)
                dependencies = []
                for node in contract_node.dependencies:
                    if node.nodeType == "ContractDefinition":
                        dependency_name = node.name
                        path_str = node.parent().absolutePath
                        dependencies.append(_get_alias(dependency_name, path_str))

                final_output[name] = {
                    "abi": data["abi"],
                    "ast": compiled_sources[path]["ast"],
                    "contractName": name,
                    "dependencies": dependencies,
                    "type": "interface",
                    "source": path_source,
                    "offset": contract_node.offset,
                    "sha1": HexStr(sha1(path_source.encode()).hexdigest()),
                }

    return final_output
