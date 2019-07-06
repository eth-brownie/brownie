#!/usr/bin/python3

import json
from pathlib import Path
import sys
import time

from . import coverage


def get_path(path_str, default_folder="scripts"):
    '''Returns path to a python module.

    Args:
        path_str: module path
        default_folder: default folder path to check if path_str is not found

    Returns: Path object'''
    if not path_str.endswith('.py'):
        path_str += ".py"
    path = _get_path(path_str, default_folder)
    if not path.is_file():
        raise FileNotFoundError(f"{path_str} is not a file")
    return path


def _get_path(path_str, default_folder):
    path = Path(path_str or default_folder)
    if not path.exists() and not path.is_absolute():
        if not path_str.startswith(default_folder+'/'):
            path = Path(default_folder).joinpath(path_str)
        if not path.exists() and sys.path[0]:
            path = Path(sys.path[0]).joinpath(path)
    if not path.exists():
        raise FileNotFoundError(f"Cannot find {path_str}")
    if path.is_file() and path.suffix != ".py":
        raise TypeError(f"'{path_str}' is not a python script")
    return path


def save_report(coverage_eval, report_path):
    '''Saves a test coverage report for viewing in the GUI.

    Args:
        coverage_eval: Coverage evaluation dict
        report_path: Path to save to. If a folder is given, saves as coverage-ddmmyy

    Returns: Path object where report file was saved'''
    report = {
        'highlights': coverage.get_highlights(coverage_eval),
        'coverage': coverage.get_totals(coverage_eval),
        'sha1': {}  # TODO
    }
    report = json.loads(json.dumps(report, default=sorted))
    report_path = Path(report_path).absolute()
    if report_path.is_dir():
        filename = "coverage-"+time.strftime('%d%m%y')+"{}.json"
        count = len(list(report_path.glob(filename.format('*'))))
        if count:
            last_path = _report_path(report_path, filename, count-1)
            with last_path.open() as fp:
                last_report = json.load(fp)
            if last_report == report:
                print(f"\nCoverage report saved at {last_path}")
                return last_path
        report_path = _report_path(report_path, filename, count)
    with report_path.open('w') as fp:
        json.dump(report, fp, sort_keys=True, indent=2)
    print(f"\nCoverage report saved at {report_path}")
    return report_path


def _report_path(base_path, filename, count):
    return base_path.joinpath(filename.format("-"+str(count) if count else ""))
