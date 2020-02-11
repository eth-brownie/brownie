#!/usr/bin/python3

import importlib
import json
import re
import time
from os import environ
from pathlib import Path

from pythx import Client, ValidationError
from pythx.middleware.toolname import ClientToolNameMiddleware

from brownie import project
from brownie._cli.__main__ import __version__
from brownie._config import ARGV, _update_argv_from_docopt
from brownie.exceptions import ProjectNotFound
from brownie.utils import color, notify
from brownie.utils.docopt import docopt

__doc__ = """Usage: brownie analyze [options] [--async | --interval=<sec>]

Options:
  --gui                     Launch the Brownie GUI after analysis
  --full                    Perform a full scan (MythX Pro required)
  --interval=<sec>          Result polling interval in seconds [default: 3]
  --async                   Do not poll for results, print job IDs and exit
  --api-key=<string>        The JWT access token from the MythX dashboard
  --help -h                 Display this message

Submits your project to the MythX API for smart contract security analysis.

In order to perform an analysis you must register for a MythX account and
generate a JWT access token. This access token may be passed through an
environment variable "MYTHX_API_KEY", or given via a command line option.

Visit https://mythx.io/ to learn more about MythX and sign up for an account.
"""


SEVERITY_COLOURS = {"LOW": "yellow", "MEDIUM": "orange", "HIGH": "red"}
DASHBOARD_BASE_URL = "https://dashboard.mythx.io/#/console/analyses/"
TRIAL_PRINTED = False
BYTECODE_ADDRESS_PATCH = re.compile(r"__\w{38}")
DEPLOYED_ADDRESS_PATCH = re.compile(r"__\$\w{34}\$__")


def construct_source_dict_from_artifact(artifact):
    return {
        artifact.get("sourcePath"): {
            "source": artifact.get("source"),
            # "ast": artifact.get("ast"),  # NOTE: Reenable once container issue fixed
        }
    }


def construct_request_from_artifact(artifact):
    global BYTECODE_ADDRESS_PATCH

    bytecode = artifact.get("bytecode")
    deployed_bytecode = artifact.get("deployedBytecode")
    source_map = artifact.get("sourceMap")
    deployed_source_map = artifact.get("deployedSourceMap")

    bytecode = re.sub(BYTECODE_ADDRESS_PATCH, "0" * 40, bytecode)
    deployed_bytecode = re.sub(DEPLOYED_ADDRESS_PATCH, "0" * 40, deployed_bytecode)

    source_list = artifact.get("allSourcePaths")
    return {
        "contract_name": artifact.get("contractName"),
        "bytecode": bytecode if bytecode else None,
        "deployed_bytecode": deployed_bytecode if deployed_bytecode else None,
        "source_map": source_map if source_map else None,
        "deployed_source_map": deployed_source_map if deployed_source_map else None,
        "sources": construct_source_dict_from_artifact(artifact),
        "source_list": source_list if source_list else None,
        "main_source": artifact.get("sourcePath"),
        "solc_version": artifact["compiler"]["version"],
        "analysis_mode": "full" if ARGV["full"] else "quick",
    }


def get_mythx_client():
    if ARGV["api-key"]:
        auth_args = {"api_key": ARGV["api-key"]}
    elif environ.get("MYTHX_API_KEY"):
        auth_args = {"api_key": environ.get("MYTHX_API_KEY")}
    else:
        raise ValidationError(
            "You must provide a MythX API key via environment variable or the commandline"
        )

    return Client(
        **auth_args, middlewares=[ClientToolNameMiddleware(name=f"brownie-{__version__}")]
    )


def get_contract_locations(build):
    return {d["sourcePath"]: d["contractName"] for _, d in build.items()}


def get_contract_types(build):
    contracts = set([n for n, d in build.items() if d["type"] == "contract"])
    libraries = set([n for n, d in build.items() if d["type"] == "library"])

    return contracts, libraries


def assemble_contract_jobs(build, contracts):
    job_data = {}
    for contract in contracts:
        artifact = build.get(contract)
        job_data[contract] = construct_request_from_artifact(artifact)
    return job_data


def update_contract_jobs_with_dependencies(build, contracts, libraries, job_data):
    for lib in libraries:
        artifact = build.get(lib)
        source_dict = construct_source_dict_from_artifact(artifact)
        deps = set(build.get_dependents(lib))
        dep_contracts = contracts.intersection(deps)
        for contract in dep_contracts:
            job_data[contract]["sources"].update(source_dict)

    return job_data


def send_to_mythx(job_data, client):
    job_uuids = []
    for c, (contract_name, analysis_request) in enumerate(job_data.items(), start=1):
        resp = client.analyze(**analysis_request)
        if ARGV["async"]:
            print(f"Analysis for {contract_name} can be found at {DASHBOARD_BASE_URL}{resp.uuid}")
        else:
            print(
                f"Submitted analysis {color('bright blue')}{resp.uuid}{color} for "
                f"contract {color('bright magenta')}{contract_name}{color} ({c}/{len(job_data)})"
            )
        job_uuids.append(resp.uuid)

    return job_uuids


def wait_for_jobs(job_uuids, client):
    for uuid in job_uuids:
        while not client.analysis_ready(uuid):
            time.sleep(int(ARGV["interval"]))


def print_trial_message(issue):
    global TRIAL_PRINTED
    if issue.swc_id == "" or issue.severity.name in ("UNKNOWN", "NONE"):
        if not TRIAL_PRINTED:
            print(f"{issue.description_long}\n")
            TRIAL_PRINTED = True
        return True
    return False


def update_report(client, uuid, highlight_report, stdout_report, source_to_name):
    resp = client.report(uuid)
    for report in resp.issue_reports:
        for issue in resp:
            if print_trial_message(issue):
                continue

            # convert issue locations to report locations
            # severities are highlighted according to SEVERITY_COLOURS
            for loc in issue.locations:
                comp = loc.source_map.components[0]
                source_list = loc.source_list or report.source_list

                if source_list and 0 <= comp.file_id < len(source_list):
                    filename = source_list[comp.file_id]
                    if filename not in source_to_name:
                        continue
                    contract_name = source_to_name[filename]
                    severity = issue.severity.name
                    stdout_report.setdefault(contract_name, {}).setdefault(severity, 0)
                    stdout_report[contract_name][severity] += 1
                    highlight_report["highlights"]["MythX"].setdefault(
                        contract_name, {filename: []}
                    )
                    highlight_report["highlights"]["MythX"][contract_name][filename].append(
                        [
                            comp.offset,
                            comp.offset + comp.length,
                            SEVERITY_COLOURS[severity],
                            f"{issue.swc_id}: {issue.description_short}\n{issue.description_long}",
                        ]
                    )


def main():
    args = docopt(__doc__)
    _update_argv_from_docopt(args)

    project_path = project.check_for_project(".")
    if project_path is None:
        raise ProjectNotFound

    build = project.load()._build

    print("Preparing project data for submission to MythX...")
    contracts, libraries = get_contract_types(build)

    job_data = assemble_contract_jobs(build, contracts)
    job_data = update_contract_jobs_with_dependencies(build, contracts, libraries, job_data)

    client = get_mythx_client()

    job_uuids = send_to_mythx(job_data, client)

    # exit if user wants an async analysis run
    if ARGV["async"]:
        print(
            "\nAll contracts were submitted successfully. Check the dashboard at "
            "https://dashboard.mythx.io/ for the progress and results of your analyses"
        )
        return

    print("\nWaiting for results...")
    wait_for_jobs(job_uuids, client)

    # assemble report json
    source_to_name = get_contract_locations(build)
    highlight_report = {"highlights": {"MythX": {}}}
    stdout_report = {}
    for c, uuid in enumerate(job_uuids, start=1):
        print(
            f"Generating report for job {color('bright blue')}{uuid}{color} ({c}/{len(job_uuids)})"
        )
        print(f"You can also check the results at {DASHBOARD_BASE_URL}{uuid}\n")

        update_report(client, uuid, highlight_report, stdout_report, source_to_name)

    # erase previous report
    report_path = Path("reports/security.json")
    if report_path.exists():
        report_path.unlink()

    total_issues = sum(x for i in stdout_report.values() for x in i.values())
    if not total_issues:
        notify("SUCCESS", "No issues found!")
        return

    # display console report
    total_high_severity = sum(i.get("HIGH", 0) for i in stdout_report.values())
    if total_high_severity:
        notify(
            "WARNING", f"Found {total_issues} issues including {total_high_severity} high severity!"
        )
    else:
        print(f"Found {total_issues} issues:")
    for name in sorted(stdout_report):
        print(f"\n  contract: {color('bright magenta')}{name}{color}")
        for key in [i for i in ("HIGH", "MEDIUM", "LOW") if i in stdout_report[name]]:
            c = color("bright red" if key == "HIGH" else "bright yellow")
            print(f"    {key.title()}: {c}{stdout_report[name][key]}{color}")

    # Write report to Brownie directory
    with report_path.open("w+") as fp:
        json.dump(highlight_report, fp, indent=2, sort_keys=True)

    # Launch GUI if user requested it
    if ARGV["gui"]:
        print("Launching the Brownie GUI")
        Gui = importlib.import_module("brownie._gui").Gui
        Gui().mainloop()
