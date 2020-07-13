import json


def get_map(project) -> dict:
    with project._build_path.joinpath("deployments/map.json").open("r") as fp:
        content = json.load(fp)
    return content


def get_dev_artifacts(project) -> list:
    return list(project._build_path.joinpath("deployments/dev/").glob("*.json"))


def test_dev_deployment_map_content(testproject, BrownieTester, config, accounts):
    config.settings["dev_deployment_artifacts"] = True

    # deploy and verify deployment of first contract
    BrownieTester.deploy(True, {"from": accounts[0]})
    content = get_map(testproject)
    assert isinstance(content, dict)

    assert len(content["dev"]["BrownieTester"]) == 1
    assert len(get_dev_artifacts(testproject)) == 1

    # deploy and verify deployment of second contract
    BrownieTester.deploy(True, {"from": accounts[0]})
    address = BrownieTester[-1].address

    content = get_map(testproject)
    assert len(content["dev"]["BrownieTester"]) == 2
    assert content["dev"]["BrownieTester"][0] == address

    assert len(get_dev_artifacts(testproject)) == 2


def test_dev_deployment_map_clear_on_disconnect(
    devnetwork, testproject, BrownieTester, config, accounts
):
    config.settings["dev_deployment_artifacts"] = True

    BrownieTester.deploy(True, {"from": accounts[0]})
    devnetwork.disconnect()
    content = get_map(testproject)
    assert not content


def test_dev_deployment_map_clear_on_remove(testproject, BrownieTester, config, accounts):
    config.settings["dev_deployment_artifacts"] = True

    BrownieTester.deploy(True, {"from": accounts[0]})
    BrownieTester.remove(BrownieTester[-1])

    assert len(get_dev_artifacts(testproject)) == 0
    content = get_map(testproject)
    assert not content


def test_dev_deployment_map_revert(testproject, BrownieTester, config, accounts, chain):
    config.settings["dev_deployment_artifacts"] = True

    BrownieTester.deploy(True, {"from": accounts[0]})
    chain.snapshot()
    BrownieTester.deploy(True, {"from": accounts[0]})
    assert len(get_dev_artifacts(testproject)) == 2
    chain.revert()
    assert len(get_dev_artifacts(testproject)) == 1
    content = get_map(testproject)
    assert len(content["dev"]["BrownieTester"]) == 1
