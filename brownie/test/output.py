#!/usr/bin/python3

import pathlib
import warnings
from typing import Any, Dict, Final, List, Optional, Set, Tuple

from brownie._c_constants import Path, ujson_dump, ujson_dumps, ujson_loads
from brownie._config import CONFIG
from brownie.exceptions import BrownieConfigWarning
from brownie.network.state import TxHistory
from brownie.project import get_loaded_projects
from brownie.project.build import Build
from brownie.typing import ContractName, CoverageMap
from brownie.utils import color
from brownie.utils._color import bright_green, bright_magenta, bright_red, bright_yellow

from brownie.test.coverage import CoverageEval

COVERAGE_COLORS: Final[list[tuple[float, str]]] = [
    (0.8, bright_red),
    (0.9, bright_yellow),
    (1.0, bright_green),
]


def _save_coverage_report(
    build: Build, coverage_eval: CoverageEval, report_path: pathlib.Path
) -> pathlib.Path:
    # Saves a test coverage report for viewing in the GUI
    report = {
        "highlights": _get_highlights(build, coverage_eval),
        "coverage": _get_totals(build, coverage_eval),
        "sha1": {},  # TODO
    }
    report = ujson_loads(ujson_dumps(report, default=sorted))
    report_path = Path(report_path).absolute()
    if report_path.is_dir():
        report_path = report_path.joinpath("coverage.json")
    with report_path.open("w") as fp:
        ujson_dump(report, fp, sort_keys=True, indent=2)
    print(f"\nCoverage report saved at {report_path}")
    print("View the report using the Brownie GUI")
    return report_path


def _load_report_exclude_data(settings: Dict[str, Any]) -> Tuple[List[str], List[Any]]:
    exclude_paths: List[str] = []
    if settings["exclude_paths"]:
        exclude = settings["exclude_paths"]
        if not isinstance(exclude, list):
            exclude = [exclude]
        for glob_str in exclude:
            glob_path = Path(glob_str)
            base_path = glob_path.root if glob_path.is_absolute() else Path(".")
            try:
                exclude_paths.extend(map(Path.as_posix, base_path.glob(glob_str)))  # type: ignore [union-attr]
            except Exception:
                warnings.warn(
                    "Invalid glob pattern in config exclude settings: '{glob_str}'",
                    BrownieConfigWarning,
                )

    exclude_contracts = []
    if settings["exclude_contracts"]:
        exclude_contracts = settings["exclude_contracts"]
        if not isinstance(exclude_contracts, list):
            exclude_contracts = [exclude_contracts]

    return exclude_paths, exclude_contracts


def _build_gas_profile_output() -> List[str]:
    # Formats gas profile report that may be printed to the console
    exclude_paths, exclude_contracts = _load_report_exclude_data(CONFIG.settings["reports"])
    try:
        project = get_loaded_projects()[0]
    except IndexError:
        project = None

    gas = TxHistory().gas_profile
    sorted_gas = sorted(gas.items())
    grouped_by_contract: Dict[str, Dict[str, Dict[str, int | str]]] = {}
    padding: Dict[str, int] = {}

    lines = [""]

    only_include_project = CONFIG.settings["reports"]["only_include_project"]
    for full_name, gas_values in sorted_gas:
        contract, function = full_name.split(".", 1)

        try:
            if project._sources.get_source_path(contract) in exclude_paths:  # type: ignore [union-attr, arg-type]
                continue
        except (AttributeError, KeyError):
            # filters contracts that are not part of the project
            if only_include_project:
                continue
        if contract in exclude_contracts:
            continue

        # calculate padding to get table-like formatting
        padding["fn"] = max(padding.get("fn", 0), len(str(function)))
        for k, v in gas_values.items():
            padding[k] = max(padding.get(k, 0), len(str(v)))

        # group functions with payload by contract name
        if contract in grouped_by_contract:
            grouped_by_contract[contract][function] = gas_values  # type: ignore [assignment]
        else:
            grouped_by_contract[contract] = {function: gas_values}  # type: ignore [dict-item]

    for contract, functions in grouped_by_contract.items():
        lines.append(f"{bright_magenta}{contract}{color} <Contract>")
        sorted_functions = dict(
            sorted(functions.items(), key=lambda value: value[1]["avg"], reverse=True)
        )
        for ix, (fn_name, values) in enumerate(sorted_functions.items()):
            prefix = "\u2514\u2500" if ix == len(functions) - 1 else "\u251c\u2500"
            fn_name = fn_name.ljust(padding["fn"])
            values["avg"] = int(values["avg"])
            padded = {k: str(v).rjust(padding[k]) for k, v in values.items()}
            lines.append(
                f"   {prefix} {fn_name} -  avg: {padded['avg']}  avg (confirmed):"
                f" {padded['avg_success']}  low: {padded['low']}  high: {padded['high']}"
            )

    return lines + [""]


def _build_coverage_output(coverage_eval: CoverageEval) -> List[str]:
    # Formats a coverage evaluation report that may be printed to the console

    exclude_paths, exclude_contracts = _load_report_exclude_data(CONFIG.settings["reports"])

    projects = get_loaded_projects()
    all_totals = (
        _get_totals(project._build, coverage_eval, exclude_contracts) for project in projects
    )
    filtered = [(project, total) for project, total in zip(projects, all_totals) if total]
    lines = []

    for project, totals in filtered:

        if len(filtered) > 1:
            lines.append(f"\n======== {bright_magenta}{project._name}{color} ========")

        for contract_name in sorted(totals):
            if project._sources.get_source_path(contract_name) in exclude_paths:
                continue

            pct = _pct(
                totals[contract_name]["totals"]["statements"],
                totals[contract_name]["totals"]["branches"],
            )
            lines.append(
                f"\n  contract: {bright_magenta}{contract_name}{color}"
                f" - {_cov_color(pct)}{pct:.1%}{color}"
            )

            cov = totals[contract_name]
            branches = cov["branches"]
            results = []
            for fn_name, statement_cov in cov["statements"].items():
                branch_cov = branches.get(fn_name, (0, 0, 0))
                pct = _pct(statement_cov, branch_cov)
                results.append((fn_name, pct))

            lines.extend(
                f"    {fn_name} - {_cov_color(pct)}{pct:.1%}{color}"
                for fn_name, pct in sorted(results, key=lambda k: (-k[1], k[0]))
            )
    return lines


def _cov_color(pct: float) -> str:
    return next(i[1] for i in COVERAGE_COLORS if pct <= i[0])


def _pct(statement, branch):
    pct = statement[0] / (statement[1] or 1)
    if branch[-1]:
        pct = (pct + (branch[0] + branch[1]) / (branch[2] * 2)) / 2
    return pct


def _get_totals(
    build: Build,
    coverage_eval: CoverageEval,
    exclude_contracts: Optional[List[str]] = None,
) -> Dict[ContractName, Dict[str, Dict[str, Dict[str, Any]]]]:
    # Returns a modified coverage eval dict showing counts and totals for each function.

    if exclude_contracts is None:
        exclude_contracts = []
    split_by_fn = _split_by_fn(build, coverage_eval)
    results: Dict[ContractName, Dict[str, Dict[str, Any]]] = {
        i: {  # ty
            "statements": {},
            "totals": {"statements": 0, "branches": [0, 0]},
            "branches": {"true": {}, "false": {}},
        }
        for i in split_by_fn
    }
    for contract_name in split_by_fn:
        if contract_name in exclude_contracts:
            del results[contract_name]
            continue
        try:
            coverage_map = build.get(contract_name)["coverageMap"]  # type: ignore [typeddict-item]
        except KeyError:
            del results[contract_name]
            continue

        r = results[contract_name]
        r["statements"], r["totals"]["statements"] = _statement_totals(
            split_by_fn[contract_name], coverage_map["statements"], exclude_contracts
        )
        r["branches"], r["totals"]["branches"] = _branch_totals(
            split_by_fn[contract_name], coverage_map["branches"], exclude_contracts
        )

    return results


def _split_by_fn(
    build: Build,
    coverage_eval: Dict[ContractName, Dict[str, Dict[int, Set[int]]]],
) -> Dict[ContractName, Dict[str, Dict[str, Tuple[List[int], List[int], List[int]]]]]:
    # Splits a coverage eval dict so that coverage indexes are stored by function.
    results: Dict[ContractName, Dict[str, Dict[str, Any]]] = {
        i: {"statements": {}, "branches": {"true": {}, "false": {}}} for i in coverage_eval
    }
    for name in coverage_eval:
        try:
            map_ = build.get(name)["coverageMap"]  # type: ignore [typeddict-item]
            results[name] = {k: _split(v, map_, k) for k, v in coverage_eval[name].items()}
        except KeyError:
            del results[name]
    return results


def _split(
    coverage_eval: Dict[int, Set[int]],
    coverage_map: CoverageMap,
    key: str,
) -> Dict[str, Tuple[List[int], List[int], List[int]]]:
    branches = coverage_map["branches"][key]
    statements = coverage_map["statements"][key]
    # not too sure what to call these but we don't want to getitem repeatedly
    first_eval = coverage_eval[0]
    second_eval = coverage_eval[1]
    third_eval = coverage_eval[2]
    return {
        fn: (
            [i for i in statements[fn] if int(i) in first_eval],
            [i for i in branches[fn] if int(i) in second_eval],
            [i for i in branches[fn] if int(i) in third_eval],
        )
        for fn in branches.keys() & statements.keys()
    }


def _statement_totals(
    coverage_eval: Dict[str, Dict[str, Tuple[List[int], List[int], List[int]]]],
    coverage_map: Dict[str, Dict[str, Dict[int, Any]]],
    exclude_contracts,
) -> Tuple[Dict[str, Tuple[int, int]], Tuple[int, int]]:
    result: Dict[str, Tuple[int, int]] = {}
    count, total = 0, 0
    for path, fns in coverage_eval.items():
        coverage_eval_for_path = coverage_eval[path]
        coverage_map_for_path = coverage_map[path]
        for fn in fns:
            if fn.split(".")[0] in exclude_contracts or fn not in coverage_eval_for_path:
                continue
            fn_count = len(coverage_eval_for_path[fn][0])
            fn_total = len(coverage_map_for_path[fn])
            count += fn_count
            total += fn_total
            result[fn] = fn_count, fn_total
    return result, (count, total)


def _branch_totals(
    coverage_eval: Dict[str, Dict[str, Tuple[List[int], List[int], List[int]]]],
    coverage_map: Dict[str, Dict[str, Dict[int, Any]]],
    exclude_contracts: List[str],
) -> Tuple[Dict[str, Tuple[int, int, int]], Tuple[int, int, int]]:
    result: Dict[str, Tuple[int, int, int]] = {}
    final_true = 0
    final_false = 0
    final_total = 0
    for path, fns in coverage_map.items():
        for fn in fns:
            if fn.split(".")[0] in exclude_contracts:
                continue

            if path not in coverage_eval or fn not in coverage_eval[path]:
                true, false = 0, 0
            else:
                coverage_eval_for_fn = coverage_eval[path][fn]
                true = len(coverage_eval_for_fn[2])
                false = len(coverage_eval_for_fn[1])
                final_true += true
                final_false += false

            total = len(coverage_map[path][fn])
            final_total += total

            result[fn] = (true, false, total)

    return result, (final_true, final_false, final_total)


def _get_highlights(build, coverage_eval) -> Dict[str, Dict[str, Dict[str, list]]]:
    # Returns a highlight map formatted for display in the GUI.
    results: Dict[str, Dict[str, Dict[str, list]]] = {"statements": {}, "branches": {}}
    for name, eval_ in coverage_eval.items():
        try:
            coverage_map = build.get(name)["coverageMap"]
        except KeyError:
            continue

        results["statements"][name] = _statement_highlights(eval_, coverage_map["statements"])
        results["branches"][name] = _branch_highlights(eval_, coverage_map["branches"])

    return results


def _statement_highlights(
    coverage_eval: Dict[str, Dict[int, set]],
    coverage_map: Dict[str, Dict[str, Dict[int, Any]]],
) -> Dict[str, List]:
    results: Dict[str, List] = {i: [] for i in coverage_map}
    for path, fns in coverage_map.items():
        for fn in fns:
            results[path].extend(
                [*offset, _statement_color(i, coverage_eval, path), ""]
                for i, offset in coverage_map[path][fn].items()
            )
    return results


def _statement_color(
    i: int,
    coverage_eval: Dict[str, Dict[int, set]],
    path: str,
) -> str:
    if path in coverage_eval and int(i) in coverage_eval[path][0]:
        return "green"
    return "red"


def _branch_highlights(
    coverage_eval: Dict[str, Dict[int, Set]],
    coverage_map: Dict[str, Dict[str, Dict[int, Any]]],
) -> Dict[str, List]:
    results: Dict[str, List] = {i: [] for i in coverage_map}
    for path, fns in coverage_map.items():
        for fn in fns:
            results[path].extend(
                [*offset[:2], _branch_color(int(i), coverage_eval, path, offset[2]), ""]
                for i, offset in coverage_map[path][fn].items()
            )
    return results


def _branch_color(
    i: int,
    coverage_eval: Dict[str, Dict[int, Set]],
    path: str,
    jump: None,
) -> str:
    if path not in coverage_eval:
        return "red"
    coverage_eval_for_path = coverage_eval[path]
    if i in coverage_eval_for_path[2]:
        if i in coverage_eval_for_path[1]:
            return "green"
        return "yellow" if jump else "orange"
    if i in coverage_eval_for_path[1]:
        return "orange" if jump else "yellow"
    return "red"
