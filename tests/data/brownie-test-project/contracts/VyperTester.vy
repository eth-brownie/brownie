
stuff: public(uint256[4])


@public
def outOfBounds(i: uint256, value: uint256) -> bool:
    self.stuff[i] = value
    return True


@public
def overflow(a: uint256, b: uint256) -> uint256:
    return a * b


@public
def underflow(a: uint256, b: uint256) -> uint256:
    return a - b


@public
def zeroDivision(a: uint256, b: uint256) -> uint256:
    return a / b


@public
def revertStrings(a: uint256) -> bool:
    assert a != 0, "zero"
    assert a != 1  # dev: one
    assert a != 2, "two"  # dev: error
    assert a != 3  # error
    assert_modifiable(a != 4)  # dev: such modifiable, wow
    if a != 31337:
        return True
    raise "awesome show"  # dev: great job


@public
def branches(a: uint256, b: bool) -> bool:
    if a > 4:
        return True
    elif b:
        return False
    if a - 2 == 3 and not b:
        return True
    return False
