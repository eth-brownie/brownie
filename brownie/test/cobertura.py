import time
from collections import defaultdict

from lxml import etree


def _make_cobertura_report(build, coverage_eval):
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

            content = build._sources.get(filename).splitlines(True)
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
    return root


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
