import json


def test_dev_deployment_map_content(testproject, BrownieTester, config, accounts):
    config.settings["dev_deployment_artifacts"] = True

    # deploy and verify deployment of first contract
    BrownieTester.deploy(True, {"from": accounts[0]})
    map = testproject._build_path.joinpath("deployments/map.json")
    assert map.exists()

    with map.open("r") as fp:
        content = json.load(fp)
    assert len(content["dev"]["BrownieTester"]) == 1

    artifacts = list(testproject._build_path.joinpath("deployments/dev/").glob("*.json"))
    assert len(artifacts) == 1

    # deploy and verify deployment of second contract
    BrownieTester.deploy(True, {"from": accounts[0]})
    address = BrownieTester[-1].address

    with map.open("r") as fp:
        content = json.load(fp)

    assert len(content["dev"]["BrownieTester"]) == 2
    assert content["dev"]["BrownieTester"][0] == address

    artifacts = list(testproject._build_path.joinpath("deployments/dev/").glob("*.json"))
    assert len(artifacts) == 2


def test_dev_deployment_map_clear_on_disconnect(
    devnetwork, testproject, BrownieTester, config, accounts
):
    config.settings["dev_deployment_artifacts"] = True

    BrownieTester.deploy(True, {"from": accounts[0]})
    map = testproject._build_path.joinpath("deployments/map.json")

    devnetwork.disconnect()

    with map.open("r") as fp:
        content = json.load(fp)

    assert not content


def test_dev_deployment_map_clear_on_remove(testproject, BrownieTester, config, accounts):
    config.settings["dev_deployment_artifacts"] = True

    BrownieTester.deploy(True, {"from": accounts[0]})
    BrownieTester.remove(BrownieTester[-1])

    artifacts = list(testproject._build_path.joinpath("deployments/dev/").glob("*.json"))
    assert len(artifacts) == 0

    map = testproject._build_path.joinpath("deployments/map.json")
    with map.open("r") as fp:
        content = json.load(fp)
    assert not content
