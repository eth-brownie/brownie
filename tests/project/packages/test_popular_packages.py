import pytest

from brownie.project.main import install_package

PACKAGES = ["OpenZeppelin/openzeppelin-contracts@2.5.0", "aragon/aragonOS@4.4.0"]


@pytest.mark.parametrize("package_id", PACKAGES)
def test_popular_packages(package_test, package_id):
    install_package(package_id)
