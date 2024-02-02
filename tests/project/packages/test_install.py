import shutil

import pytest
import yaml

from brownie._config import _get_data_folder
from brownie.exceptions import InvalidPackage
from brownie.project.main import install_package


@pytest.fixture(autouse=True)
def setup(package_test):
    yield
    path = _get_data_folder().joinpath("packages")
    shutil.rmtree(path)
    path.mkdir()


@pytest.fixture
def dependentproject(newproject):
    config = {"dependencies": ["brownie-mix/token-mix@1.0.0"]}
    with newproject._path.joinpath("brownie-config.yaml").open("w") as fp:
        yaml.dump(config, fp)

    yield newproject


def test_install_from_github():
    install_package("brownie-mix/token-mix@1.0.0")


def test_github_already_installed():
    path = _get_data_folder().joinpath("packages/brownie-mix")
    path.mkdir()
    path.joinpath("token-mix@1.0.0").mkdir()

    with pytest.raises(FileExistsError):
        install_package("brownie-mix/token-mix@1.0.0")


def test_unknown_version():
    with pytest.raises(ValueError):
        install_package("brownie-mix/token-mix@1.0.1")


def test_bad_project_id_version():
    with pytest.raises(ValueError):
        install_package("brownie-mix/token-mix")


def test_bad_project_id_repo_org():
    with pytest.raises(ValueError):
        install_package("token-mix@1.0.0")


def test_valid_repo_not_a_project():
    with pytest.raises(InvalidPackage):
        install_package("iamdefinitelyahuman/eth-event@0.2.2")

    assert not _get_data_folder().joinpath("packages/iamdefinitelyahuman/eth-event@0.2.2").exists()


def test_install_from_config_dependencies(dependentproject):
    package_folder = _get_data_folder().joinpath("packages/brownie-mix/token-mix@1.0.0")
    assert not package_folder.exists()

    dependentproject.load()
    assert package_folder.exists()


def test_dependency_already_installed(dependentproject):
    install_package("brownie-mix/token-mix@1.0.0")
    dependentproject.load()


def test_wont_compile():
    # can't compile due to a NamespaceCollision, should still install
    install_package("makerdao/dss@1.0.6")
