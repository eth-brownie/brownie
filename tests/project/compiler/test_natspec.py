from brownie.project.compiler.utils import merge_natspec

DEVDOC = {
    "author": "Warned Bros",
    "details": "Simply chewing a carrot does not count, carrots must pass the throat",
    "methods": {
        "age(uint256,uint256)": {
            "details": "Compares the entire string and does not rely on a hash",
            "params": {
                "food": "The name of a food to evaluate (in English)",
                "qty": "The number of food items to evaluate",
            },
            "returns": {
                "_0": "True if Bugs will eat it, False otherwise",
                "_1": "A second value for testing purposes",
            },
        }
    },
    "title": "A simulator for Bug Bunny, the most famous Rabbit",
}

USERDOC = {
    "methods": {
        "constructor": "I'm only here to mess with things",
        "age(uint256,uint256)": {"notice": "Determine if Bugs will accept `qty` of `food` to eat"},
    },
    "notice": "You can use this contract for only the most basic simulation",
}


def test_userdoc():
    natspec = merge_natspec(DEVDOC, USERDOC)

    assert USERDOC["notice"] == natspec["notice"]
    assert "constructor" not in natspec["methods"]

    notice = USERDOC["methods"]["age(uint256,uint256)"]["notice"]
    assert notice == natspec["methods"]["age(uint256,uint256)"]["notice"]


def test_devdoc():
    natspec = merge_natspec(DEVDOC, USERDOC)

    for key in DEVDOC:
        if key == "methods":
            continue
        assert DEVDOC[key] == natspec[key]


def test_devdoc_methods():
    natspec = merge_natspec(DEVDOC, USERDOC)

    methods = DEVDOC["methods"]["age(uint256,uint256)"]
    for key in methods:
        assert methods[key] == natspec["methods"]["age(uint256,uint256)"][key]
