#!/usr/bin/python3

from brownie.project import ethpm

ETHPM_CONFIG = {
    "package_name": "testpackage",
    "version": "1.0.0",
    "settings": {"deployment_networks": False, "include_dependencies": False},
}


def test_release_package(dep_project, accounts):
    registry = dep_project.PackageRegistry.deploy({"from": accounts[0]})

    package_config = ETHPM_CONFIG.copy()
    package_config["settings"]["include_dependencies"] = False
    manifest, uri = ethpm.create_manifest(dep_project._path, package_config, True)
    ethpm.release_package(registry.address, accounts[0], "testpackage", "1.0.0", uri)
    id_ = registry.getReleaseId("testpackage", "1.0.0")
    assert registry.getReleaseData(id_)[-1] == uri
