#!/usr/bin/python3

import json
import time
from os import environ

from docopt import docopt
from mythx_models.response import Severity
from pythx import Client
from pythx.middleware.toolname import ClientToolNameMiddleware

from brownie import project
from brownie._config import ARGV
from brownie.cli.__main__ import __version__
from brownie.exceptions import ProjectNotFound

__doc__ = f"""Usage: brownie analyze [options]

Options:
  --eth-address           The address of your MythX account
  --password              The password of your MythX account
  --help -h               Display this message

Use analyze to submit your project to the MythX API for smart contract
security analysis.

To authenticate with the MythX API, you have to provide a username/password
combination. It is recommended to pass them through the environment
variables as "MYTHX_ETH_ADDRESS" and "MYTHX_PASSWORD".

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


def construct_source_dict_from_artifact(artifact):
    return {
        artifact.get("sourcePath"): {
            "source": artifact.get("source"),
            # "ast": artifact.get("ast"),
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
    }


def main():
    args = docopt(__doc__)
    project_path = project.check_for_project(".")
    if project_path is None:
        raise ProjectNotFound

    project.load()
    build = project.get_loaded_projects()[0]._build

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

    # if both eth address and username are None,
    client = Client(
        eth_address=environ.get("MYTHX_ETH_ADDRESS")
        or ARGV["eth-address"]
        or "0x0000000000000000000000000000000000000000",
        password=environ.get("MYTHX_PASSWORD") or ARGV["password"] or "trial",
        middlewares=[ClientToolNameMiddleware(name="brownie-{}".format(__version__))],
        staging=True,
    )

    # submit to MythX
    job_uuids = []
    for contract_name, analysis_request in job_data.items():
        # print(json.dumps(analysis_request["sources"]))
        # print(json.dumps(analysis_request, indent=2, sort_keys=True))
        resp = client.analyze(**analysis_request)
        print("Submitted analysis {} for contract {}".format(resp.uuid, contract_name))
        job_uuids.append(resp.uuid)

    # tell user execution in progress and poll (optionally async w/ UUID)
    # TODO: --async
    for uuid in job_uuids:
        while not client.analysis_ready(uuid):
            # TODO: Add poll interval option
            time.sleep(3)

    # assemble report json
    printed = False
    for uuid in job_uuids:
        highlight_report = {
            "highlights": {"MythX": {cn: {cp: []} for cp, cn in source_to_name.items()}}
        }
        resp = client.report(uuid)
        for report in resp.issue_reports:
            for issue in resp:
                # handle non-code issues
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
                                    issue.description_short,
                                ]
                            )

        with open("reports/security.json", "w+") as report_f:
            json.dump(highlight_report, report_f, indent=2, sort_keys=True)

    # TODO: tell user to display GUI (or automatically launch using --gui)
