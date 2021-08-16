#!/usr/bin/python3

import json
import warnings
from pathlib import Path

from brownie._config import CONFIG
from brownie.exceptions import BrownieConfigWarning
from brownie.network.state import TxHistory
from brownie.project import get_loaded_projects
from brownie.utils import color

COVERAGE_COLORS = [(0.8, "bright red"), (0.9, "bright yellow"), (1, "bright green")]


def _save_coverage_report(build, coverage_eval, report_path):
    # Saves a test coverage report for viewing in the GUI
    report = {
        "highlights": _get_highlights(build, coverage_eval),
        "coverage": _get_totals(build, coverage_eval),
        "sha1": {},  # TODO
    }
    report = json.loads(json.dumps(report, default=sorted))
    report_path = Path(report_path).absolute()
    if report_path.is_dir():
        report_path = report_path.joinpath("coverage.json")
    with report_path.open("w") as fp:
        json.dump(report, fp, sort_keys=True, indent=2)
    print(f"\nCoverage report saved at {report_path}")
    print("View the report using the Brownie GUI")
    return report_path


def _load_report_exclude_data(settings):
    exclude_paths = []
    if settings["exclude_paths"]:
        exclude = settings["exclude_paths"]
        if not isinstance(exclude, list):
            exclude = [exclude]
        for glob_str in exclude:
            if Path(glob_str).is_absolute():
                base_path = Path(glob_str).root
            else:
                base_path = Path(".")
            try:
                exclude_paths.extend([i.as_posix() for i in base_path.glob(glob_str)])
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


def _build_gas_profile_output():
    # Formats gas profile report that may be printed to the console
    exclude_paths, exclude_contracts = _load_report_exclude_data(CONFIG.settings["reports"])
    try:
        project = get_loaded_projects()[0]
    except IndexError:
        project = None

    gas = TxHistory().gas_profile
    sorted_gas = sorted(gas.items())
    grouped_by_contract = {}
    padding = {}

    lines = [""]

    only_include_project = CONFIG.settings["reports"]["only_include_project"]
    for full_name, values in sorted_gas:
        contract, function = full_name.split(".", 1)

        try:
            if project._sources.get_source_path(contract) in exclude_paths:
                continue
        except (AttributeError, KeyError):
            # filters contracts that are not part of the project
            if only_include_project:
                continue
        if contract in exclude_contracts:
            continue

        # calculate padding to get table-like formatting
        padding["fn"] = max(padding.get("fn", 0), len(str(function)))
        for k, v in values.items():
            padding[k] = max(padding.get(k, 0), len(str(v)))

        # group functions with payload by contract name
        if contract in grouped_by_contract.keys():
            grouped_by_contract[contract][function] = values
        else:
            grouped_by_contract[contract] = {function: values}

    for contract, functions in grouped_by_contract.items():
        lines.append(f"{color('bright magenta')}{contract}{color} <Contract>")
        sorted_functions = dict(
            sorted(functions.items(), key=lambda value: value[1]["avg"], reverse=True)
        )
        for ix, (fn_name, values) in enumerate(sorted_functions.items()):
            prefix = "\u2514\u2500" if ix == len(functions) - 1 else "\u251c\u2500"
            fn_name = fn_name.ljust(padding["fn"])
            values["avg"] = int(values["avg"])
            values = {k: str(v).rjust(padding[k]) for k, v in values.items()}
            lines.append(
                f"   {prefix} {fn_name} -  avg: {values['avg']}  avg (confirmed):"
                f" {values['avg_success']}  low: {values['low']}  high: {values['high']}"
            )

    return lines + [""]


def _build_coverage_output(coverage_eval):
    # Formats a coverage evaluation report that may be printed to the console

    exclude_paths, exclude_contracts = _load_report_exclude_data(CONFIG.settings["reports"])
    all_totals = [
        (i, _get_totals(i._build, coverage_eval, exclude_contracts)) for i in get_loaded_projects()
    ]
    all_totals = [i for i in all_totals if i[1]]
    lines = []

    for project, totals in all_totals:

        if len(all_totals) > 1:
            lines.append(f"\n======== {color('bright magenta')}{project._name}{color} ========")

        for contract_name in sorted(totals):
            if project._sources.get_source_path(contract_name) in exclude_paths:
                continue

            pct = _pct(
                totals[contract_name]["totals"]["statements"],
                totals[contract_name]["totals"]["branches"],
            )
            lines.append(
                f"\n  contract: {color('bright magenta')}{contract_name}{color}"
                f" - {_cov_color(pct)}{pct:.1%}{color}"
            )

            cov = totals[contract_name]
            results = []
            for fn_name, statement_cov in cov["statements"].items():
                branch_cov = cov["branches"][fn_name] if fn_name in cov["branches"] else (0, 0, 0)
                pct = _pct(statement_cov, branch_cov)
                results.append((fn_name, pct))

            for fn_name, pct in sorted(results, key=lambda k: (-k[1], k[0])):
                lines.append(f"    {fn_name} - {_cov_color(pct)}{pct:.1%}{color}")

    return lines


def _cov_color(pct):
    return color(next(i[1] for i in COVERAGE_COLORS if pct <= i[0]))


def _pct(statement, branch):
    pct = statement[0] / (statement[1] or 1)
    if branch[-1]:
        pct = (pct + (branch[0] + branch[1]) / (branch[2] * 2)) / 2
    return pct


def _get_totals(build, coverage_eval, exclude_contracts=None):
    # Returns a modified coverage eval dict showing counts and totals for each function.

    if exclude_contracts is None:
        exclude_contracts = []
    coverage_eval = _split_by_fn(build, coverage_eval)
    results = dict(
        (
            i,
            {
                "statements": {},
                "totals": {"statements": 0, "branches": [0, 0]},
                "branches": {"true": {}, "false": {}},
            },
        )
        for i in coverage_eval
    )
    for contract_name in coverage_eval:
        if contract_name in exclude_contracts:
            del results[contract_name]
            continue
        try:
            coverage_map = build.get(contract_name)["coverageMap"]
        except KeyError:
            del results[contract_name]
            continue

        r = results[contract_name]
        r["statements"], r["totals"]["statements"] = _statement_totals(
            coverage_eval[contract_name], coverage_map["statements"], exclude_contracts
        )
        r["branches"], r["totals"]["branches"] = _branch_totals(
            coverage_eval[contract_name], coverage_map["branches"], exclude_contracts
        )

    return results


def _split_by_fn(build, coverage_eval):
    # Splits a coverage eval dict so that coverage indexes are stored by function.
    results = dict(
        (i, {"statements": {}, "branches": {"true": {}, "false": {}}}) for i in coverage_eval
    )
    for name in coverage_eval:
        try:
            map_ = build.get(name)["coverageMap"]
            results[name] = dict((k, _split(v, map_, k)) for k, v in coverage_eval[name].items())
        except KeyError:
            del results[name]
    return results


def _split(coverage_eval, coverage_map, key):
    results = {}
    branches = coverage_map["branches"][key]
    statements = coverage_map["statements"][key]
    for fn in branches.keys() & statements.keys():
        results[fn] = [
            [i for i in statements[fn] if int(i) in coverage_eval[0]],
            [i for i in branches[fn] if int(i) in coverage_eval[1]],
            [i for i in branches[fn] if int(i) in coverage_eval[2]],
        ]
    return results


def _statement_totals(coverage_eval, coverage_map, exclude_contracts):
    result = {}
    count, total = 0, 0
    for path, fn in [(k, x) for k, v in coverage_eval.items() for x in v]:
        if fn.split(".")[0] in exclude_contracts or fn not in coverage_eval[path]:
            continue
        count += len(coverage_eval[path][fn][0])
        total += len(coverage_map[path][fn])
        result[fn] = (len(coverage_eval[path][fn][0]), len(coverage_map[path][fn]))
    return result, (count, total)


def _branch_totals(coverage_eval, coverage_map, exclude_contracts):
    result = {}
    final = [0, 0, 0]
    for path, fn in [(k, x) for k, v in coverage_map.items() for x in v]:
        if fn.split(".")[0] in exclude_contracts:
            continue
        if path not in coverage_eval or fn not in coverage_eval[path]:
            true, false = 0, 0
        else:
            true = len(coverage_eval[path][fn][2])
            false = len(coverage_eval[path][fn][1])
        total = len(coverage_map[path][fn])
        result[fn] = (true, false, total)
        for i in range(3):
            final[i] += result[fn][i]
    return result, final


def _get_highlights(build, coverage_eval):
    # Returns a highlight map formatted for display in the GUI.
    results = {"statements": {}, "branches": {}}
    for name, eval_ in coverage_eval.items():
        try:
            coverage_map = build.get(name)["coverageMap"]
        except KeyError:
            continue

        results["statements"][name] = _statement_highlights(eval_, coverage_map["statements"])
        results["branches"][name] = _branch_highlights(eval_, coverage_map["branches"])

    return results


def _statement_highlights(coverage_eval, coverage_map):
    results = dict((i, []) for i in coverage_map)
    for path, fn in [(k, x) for k, v in coverage_map.items() for x in v]:
        results[path].extend(
            [
                list(offset) + [_statement_color(i, coverage_eval, path), ""]
                for i, offset in coverage_map[path][fn].items()
            ]
        )
    return results


def _statement_color(i, coverage_eval, path):
    if path not in coverage_eval or int(i) not in coverage_eval[path][0]:
        return "red"
    return "green"


def _branch_highlights(coverage_eval, coverage_map):
    results = dict((i, []) for i in coverage_map)
    for path, fn in [(k, x) for k, v in coverage_map.items() for x in v]:
        results[path].extend(
            [
                list(offset[:2]) + [_branch_color(int(i), coverage_eval, path, offset[2]), ""]
                for i, offset in coverage_map[path][fn].items()
            ]
        )
    return results


def _branch_color(i, coverage_eval, path, jump):
    if path not in coverage_eval:
        return "red"
    if i in coverage_eval[path][2]:
        if i in coverage_eval[path][1]:
            return "green"
        return "yellow" if jump else "orange"
    if i in coverage_eval[path][1]:
        return "orange" if jump else "yellow"
    return "red"
