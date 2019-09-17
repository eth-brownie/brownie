#!/usr/bin/python3

import json
import time
from os import environ

from docopt import docopt
from mythx_models.response import Severity
from pythx import Client
from pythx.middleware.toolname import ClientToolNameMiddleware

from brownie import project
from brownie._config import ARGV, update_argv_from_docopt
from brownie.cli.__main__ import __version__
from brownie.gui import Gui
from brownie.exceptions import ProjectNotFound

# TODO: Refactor core routines into helper functions
# TODO: testtesttesttesttesttesttesttesttesttesttesttest

__doc__ = f"""Usage: brownie analyze [options] [--async | --interval=<sec>]

Options:
  --gui                   Launch the Brownie GUI after analysis
  --full                  Perform a full scan (MythX Pro required)
  --interval=<sec>        Result polling interval in seconds [default: 3]
  --async                 Do not poll for results, print job IDs and exit
  --access-token          The JWT access token from the MythX dashboard
  --eth-address           The address of your MythX account
  --password              The password of your MythX account
  --help -h               Display this message

Use analyze to submit your project to the MythX API for smart contract
security analysis.

To authenticate with the MythX API, it is recommended that you provide
the MythX JWT access token. It can be obtained on the MythX dashboard
site in the profile section. They should be passed through the environment
variable "MYTHX_ACCESS_TOKEN". If that is not possible, it can also be
passed explicitly with the respective command line option.

Alternatively, you have to provide a username/password combination. It
is recommended to pass them through the environment variables as
"MYTHX_ETH_ADDRESS" and "MYTHX_PASSWORD".

You can also choose to not authenticate and submit your analyses as a free
trial user. No registration required! To see your past analyses, get access
to deeper vulnerability detection, and a neat dashboard, register at
https://mythx.io/. Any questions? Hit up dominik.muhs@consensys.net or contact
us on the website!
"""


SEVERITY_COLOURS = {
    Severity.LOW: "green",
    Severity.MEDIUM: "yellow",
    Severity.HIGH: "red",
}
DASHBOARD_BASE_URL = "https://dashboard.mythx.io/#/console/analyses/"


def construct_source_dict_from_artifact(artifact):
    return {
        artifact.get("sourcePath"): {
            "source": artifact.get("source"),
            # "ast": artifact.get("ast"),  # NOTE: Reenable once container issue fixed
        }
    }


def construct_request_from_artifact(artifact):
    bytecode = artifact.get("bytecode")
    deployed_bytecode = artifact.get("deployedBytecode")
    source_map = artifact.get("sourceMap")
    deployed_source_map = artifact.get("deployedSourceMap")
    return {
        "contract_name": artifact.get("contractName"),
        "bytecode": bytecode if bytecode else None,
        "deployed_bytecode": deployed_bytecode if deployed_bytecode else None,
        "source_map": source_map if source_map else None,
        "deployed_source_map": deployed_source_map if deployed_source_map else None,
        "sources": construct_source_dict_from_artifact(artifact),
        "source_list": artifact.get("allSourcePaths"),
        "main_source": artifact.get("sourcePath"),
        "solc_version": artifact["compiler"]["version"].replace("Version:", "").strip(),
        "analysis_mode": "full" if ARGV["full"] else "quick",
    }


def get_mythx_client():
    # if both eth address and username are None,
    if ARGV["access-token"]:
        authenticated = True
        auth_args = {"access_token": ARGV["access-token"]}
    elif environ.get("MYTHX_ACCESS_TOKEN"):
        authenticated = True
        auth_args = {"access_token": environ.get("MYTHX_ACCESS_TOKEN")}
    elif environ.get("MYTHX_ETH_ADDRESS") and environ.get("MYTHX_PASSWORD"):
        authenticated = True
        auth_args = {
            "eth_address": environ.get("MYTHX_ETH_ADDRESS"),
            "password": environ.get("MYTHX_PASSWORD"),
        }
    elif ARGV["eth-address"] and ARGV["password"]:
        authenticated = True
        auth_args = {"eth_address": ARGV["eth-address"], "password": ARGV["password"]}
    else:
        authenticated = False
        auth_args = {
            "eth_address": "0x0000000000000000000000000000000000000000",
            "password": "trial",
        }

    return Client(
        **auth_args,
        middlewares=[ClientToolNameMiddleware(name="brownie-{}".format(__version__))],
    ), authenticated


def main():

    args = docopt(__doc__)
    update_argv_from_docopt(args)

    project_path = project.check_for_project(".")
    if project_path is None:
        raise ProjectNotFound

    build = project.load()._build

    # aggregate main contracts and libraries
    contracts = set([n for n, d in build.items() if d["type"] == "contract"])
    libraries = set([n for n, d in build.items() if d["type"] == "library"])

    source_to_name = {d["sourcePath"]: d["contractName"] for _, d in build.items()}

    # assemble basic MythX analysis jobs for each contract
    job_data = {}
    for contract in contracts:
        artifact = build.get(contract)
        job_data[contract] = construct_request_from_artifact(artifact)

    # update base requests with dependency data
    for lib in libraries:
        artifact = build.get(lib)
        source_dict = construct_source_dict_from_artifact(artifact)
        deps = set(build.get_dependents(lib))
        dep_contracts = contracts.intersection(deps)
        for contract in dep_contracts:
            job_data[contract]["sources"].update(source_dict)

    client, authenticated = get_mythx_client()

    # submit to MythX
    job_uuids = []
    for contract_name, analysis_request in job_data.items():
        resp = client.analyze(**analysis_request)
        if ARGV["async"] and authenticated:
            print(
                "The analysis for {} can be found at {}{}".format(
                    contract_name, DASHBOARD_BASE_URL, resp.uuid
                )
            )
        else:
            print(
                "Submitted analysis {} for contract {}".format(resp.uuid, contract_name)
            )
        job_uuids.append(resp.uuid)

    # exit if user wants an async analysis run
    if ARGV["async"] and authenticated:
        print(
            "\nAll contracts were submitted successfully. Check the dashboard at "
            "https://dashboard.mythx.io/ for the progress and results of your analyses"
        )
        return

    # poll in user-specified interval until all results are in
    for uuid in job_uuids:
        while not client.analysis_ready(uuid):
            time.sleep(int(ARGV["interval"]))

    # assemble report json
    printed = False
    for uuid in job_uuids:
        print("Generating report for job {}".format(uuid))
        if authenticated:
            print(
                "You can also check the results at {}{}\n".format(
                    DASHBOARD_BASE_URL, uuid
                )
            )

        highlight_report = {
            "highlights": {"MythX": {cn: {cp: []} for cp, cn in source_to_name.items()}}
        }
        resp = client.report(uuid)
        for report in resp.issue_reports:
            for issue in resp:
                # handle non-code issues and print message only once
                if issue.swc_id == "" or issue.severity in (
                    Severity.UNKNOWN,
                    Severity.NONE,
                ):
                    if not printed:
                        print(issue.description_short)
                        print(issue.description_long)
                        print()
                        printed = True
                    continue

                # convert issue locations to report locations
                # severities are highlighted according to SEVERITY_COLOURS
                for loc in issue.locations:
                    comp = loc.source_map.components[0]
                    source_list = loc.source_list or report.source_list

                    if source_list and 0 <= comp.file_id < len(source_list):
                        filename = source_list[comp.file_id]
                        if filename in source_to_name:
                            contract_name = source_to_name[filename]
                            highlight_report["highlights"]["MythX"][contract_name][
                                filename
                            ].append(
                                [
                                    comp.offset,
                                    comp.offset + comp.length,
                                    SEVERITY_COLOURS[issue.severity],
                                    "{}: {}".format(
                                        issue.swc_id, issue.description_short
                                    ),
                                ]
                            )

        # Write report to Brownie directory
        with open("reports/security.json", "w+") as report_f:
            json.dump(highlight_report, report_f, indent=2, sort_keys=True)

    # Launch GUI if user requested it
    if ARGV["gui"]:
        print("Launching the Brownie GUI")
        Gui().mainloop()
