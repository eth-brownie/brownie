#!/usr/bin/python3

import json
import time
import warnings
from collections import defaultdict
from pathlib import Path

from lxml import etree

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

    root = etree.Element("coverage")
    root.set("complexity", "")
    root.set("version", "1.9")
    root.set("timestamp", str(int(time.time() * 1000)))
    packages = etree.SubElement(root, "packages")

    total_valid_lines = 0
    total_lines_covered = 0

    total_valid_branches = 0
    total_branches_covered = 0

    for contract_name in coverage_eval:
        contract = build.get(contract_name)
        coverage_map = contract["coverageMap"]

        package = etree.SubElement(packages, "package")
        package.set("name", contract_name)
        package.set("complexity", "")

        classes = etree.SubElement(package, "classes")

        path_ids = set(
            [k for k, v in coverage_map["statements"].items() if v]
            + [k for k, v in coverage_map["branches"].items() if v]
        )

        package_valid_lines = 0
        package_lines_covered = 0

        package_valid_branches = 0
        package_branches_covered = 0

        for path_id in sorted(list(path_ids)):
            filename = contract["allSourcePaths"][path_id]
            if filename.startswith("/"):
                continue

            content = open(filename).readlines()
            file_coverage = coverage_eval[contract_name].get(path_id, [set(), set(), set()])
            line_coverage = _lines_to_coverage(coverage_map, path_id, file_coverage, content)

            class_ = etree.SubElement(classes, "class")
            class_.set("name", filename)
            class_.set("filename", filename)
            class_.set("complexity", "")

            class_lines = etree.SubElement(class_, "lines")

            class_valid_lines = 0
            class_lines_covered = 0

            class_valid_branches = 0
            class_branches_covered = 0
            for line_no in sorted(line_coverage):
                line = etree.SubElement(class_lines, "line")
                line.set("number", str(line_no))
                class_valid_lines += 1
                package_valid_lines += 1
                total_valid_lines += 1
                if line_coverage[line_no] is not None:
                    line.set("hits", str(1))
                    class_lines_covered += 1
                    package_lines_covered += 1
                    total_lines_covered += 1
                    if line_coverage[line_no]:
                        line.set("branch", "true")
                        branches_covered = sum(line_coverage[line_no])
                        valid_branches = len(line_coverage[line_no]) * 2
                        class_valid_branches += valid_branches
                        class_branches_covered += branches_covered
                        package_valid_branches += valid_branches
                        package_branches_covered += branches_covered
                        total_valid_branches += valid_branches
                        total_branches_covered += branches_covered
                        pct = round((branches_covered / valid_branches) * 100)
                        line.set(
                            "condition-coverage", f"{pct}% ({branches_covered}/{valid_branches})"
                        )
                else:
                    line.set("hits", str(0))

            class_.set("line-rate", _rate(class_valid_lines, class_lines_covered))
            class_.set("branch-rate", _rate(class_valid_branches, class_branches_covered))

        package.set("line-rate", _rate(package_valid_lines, package_lines_covered))
        package.set("branch-rate", _rate(package_valid_branches, package_branches_covered))

    root.set("line-rate", _rate(total_valid_lines, total_lines_covered))
    root.set("branch-rate", _rate(total_valid_branches, total_branches_covered))
    root.set("lines-covered", str(total_lines_covered))
    root.set("lines-valid", str(total_valid_lines))
    root.set("branches-covered", str(total_branches_covered))
    root.set("branches-valid", str(total_valid_branches))

    xml_path = report_path.parent.joinpath("coverage.xml")

    with xml_path.open("wb") as fp:
        fp.write(etree.tostring(root, pretty_print=True))

    print(f"\nCoverage reports saved at {report_path} and {xml_path}")
    print("View the report using the Brownie GUI")
    return report_path


def _rate(line_count, hit_count):
    if line_count == 0:
        return "1.0"
    else:
        return "{:.5}".format(hit_count / line_count)


def _lines_to_coverage(coverage_map, path_id, file_coverage, content):
    available_offsets = set()

    for function in coverage_map["statements"][path_id].values():
        for statement, [from_, to] in function.items():
            available_offsets.update(range(from_, to))

    for function in coverage_map["branches"][path_id].values():
        for statement, [from_, to, _] in function.items():
            available_offsets.update(range(from_, to))

    statements = coverage_map["statements"][path_id]
    branches = coverage_map["branches"][path_id]

    flat_statements = {int(k): v for d in statements.values() for k, v in d.items()}
    flat_branches = {int(k): [v[0], v[1]] for d in branches.values() for k, v in d.items()}
    branch_coverage = defaultdict(int)

    covered_offsets = set()
    [covered_statements, covered_yes_branches, covered_no_branches] = file_coverage

    for stmt in covered_statements:
        covered_offsets.update(range(*flat_statements[stmt]))

    for stmt in covered_yes_branches:
        covered_offsets.update(range(*flat_branches[stmt]))
        branch_coverage[stmt] += 1

    for stmt in covered_no_branches:
        covered_offsets.update(range(*flat_branches[stmt]))
        branch_coverage[stmt] += 1

    offset_branches = defaultdict(list)
    for statements in branches.values():
        for stmt, [from_, to, _] in statements.items():
            offset_branches[from_].append(stmt)

    branch_lines = {}
    line_to_coverage = {}
    from_ = 0
    for n, line in enumerate(content):
        to = from_ + len(line)
        if set(range(from_, to)).intersection(available_offsets):
            is_covered = bool(set(range(from_, to)).intersection(covered_offsets))
            if is_covered:
                line_to_coverage[n + 1] = []
            else:
                line_to_coverage[n + 1] = None
        for offset, branches in list(offset_branches.items()):
            if from_ <= offset < to:
                for branch in branches:
                    branch_lines[int(branch)] = n + 1
                offset_branches.pop(offset)
        from_ = to

    for stmt, coverage in branch_coverage.items():
        line = branch_lines[int(stmt)]
        # nothing covers the line
        if line_to_coverage[line] is None:
            continue
        line_to_coverage[line].append(coverage)

    return line_to_coverage


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

    for full_name, values in sorted_gas:
        contract, function = full_name.split(".", 1)

        try:
            if project._sources.get_source_path(contract) in exclude_paths:
                continue
        except (AttributeError, KeyError):
            pass
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
                f"   {prefix} {fn_name} -  avg: {values['avg']}"
                f"  low: {values['low']}  high: {values['high']}"
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


def _statement_totals(coverage_eval, coverage_map, exclude_contracts):
    result = {}
    count, total = 0, 0
    for path, fn in [(k, x) for k, v in coverage_eval.items() for x in v]:
        if fn.split(".")[0] in exclude_contracts:
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
