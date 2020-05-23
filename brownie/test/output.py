#!/usr/bin/python3

import json
from pathlib import Path

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


def _print_gas_profile():
    # Formats and prints a gas profile report to the console
    print("\n\nGas Profile:")
    gas = TxHistory().gas_profile
    sorted_gas = sorted(gas.items())
    grouped_by_contract = {}
    padding = {}
    for full_name, values in sorted_gas:
        contract, function = full_name.split(".", 1)

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
        print(f"{color('bright magenta')}{contract}{color} <Contract>")
        sorted_functions = dict(
            sorted(functions.items(), key=lambda value: value[1]["avg"], reverse=True)
        )
        for ix, (fn_name, values) in enumerate(sorted_functions.items()):
            prefix = "\u2514\u2500" if ix == len(functions) - 1 else "\u251c\u2500"
            fn_name = fn_name.ljust(padding["fn"])
            values["avg"] = int(values["avg"])
            values = {k: str(v).rjust(padding[k]) for k, v in values.items()}
            print(
                f"   {prefix} {fn_name} -  avg: {values['avg']}"
                f"  low: {values['low']}  high: {values['high']}"
            )


def _print_coverage_totals(build, coverage_eval):
    # Formats and prints a coverage evaluation report to the console
    all_totals = [(i._name, _get_totals(i._build, coverage_eval)) for i in get_loaded_projects()]
    print("\n\nCoverage analysis:")

    for project_name, totals in all_totals:
        if not totals:
            continue

        print(f"\n ===== {color('bright magenta')}{project_name}{color} =====")

        for name in sorted(totals):
            pct = _pct(totals[name]["totals"]["statements"], totals[name]["totals"]["branches"])
            print(
                f"\n  contract: {color('bright magenta')}{name}{color}"
                f" - {_cov_color(pct)}{pct:.1%}{color}"
            )
            cov = totals[name]
            for fn_name, count in cov["statements"].items():
                branch = cov["branches"][fn_name] if fn_name in cov["branches"] else (0, 0, 0)
                pct = _pct(count, branch)
                print(f"    {fn_name} - {_cov_color(pct)}{pct:.1%}{color}")


def _cov_color(pct):
    return color(next(i[1] for i in COVERAGE_COLORS if pct <= i[0]))


def _pct(statement, branch):
    pct = statement[0] / (statement[1] or 1)
    if branch[-1]:
        pct = (pct + (branch[0] + branch[1]) / (branch[2] * 2)) / 2
    return pct


def _get_totals(build, coverage_eval):
    # Returns a modified coverage eval dict showing counts and totals for each function.

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
    for name in coverage_eval:
        try:
            coverage_map = build.get(name)["coverageMap"]
        except KeyError:
            del results[name]
            continue

        r = results[name]
        r["statements"], r["totals"]["statements"] = _statement_totals(
            coverage_eval[name], coverage_map["statements"]
        )
        r["branches"], r["totals"]["branches"] = _branch_totals(
            coverage_eval[name], coverage_map["branches"]
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
            pass
    return results


def _split(coverage_eval, coverage_map, key):
    results = {}
    for fn, map_ in coverage_map["statements"][key].items():
        results[fn] = [[i for i in map_ if int(i) in coverage_eval[0]], [], []]
    for fn, map_ in coverage_map["branches"][key].items():
        results[fn][1] = [i for i in map_ if int(i) in coverage_eval[1]]
        results[fn][2] = [i for i in map_ if int(i) in coverage_eval[2]]
    return results


def _statement_totals(coverage_eval, coverage_map):
    result = {}
    count, total = 0, 0
    for path, fn in [(k, x) for k, v in coverage_eval.items() for x in v]:
        count += len(coverage_eval[path][fn][0])
        total += len(coverage_map[path][fn])
        result[fn] = (len(coverage_eval[path][fn][0]), len(coverage_map[path][fn]))
    return result, (count, total)


def _branch_totals(coverage_eval, coverage_map):
    result = {}
    final = [0, 0, 0]
    for path, fn in [(k, x) for k, v in coverage_map.items() for x in v]:
        if path not in coverage_eval:
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
