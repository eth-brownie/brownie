# @version ^0.2.0

stuff: public(uint256[4])


@external
def branches(a: uint256, b: bool) -> bool:
    if a > 4:
        return True
    elif b:
        return False
    if a - 2 == 3 and not b:
        return True
    return False


@external
def revertStrings(a: uint256) -> bool:
    assert a != 0, "zero"
    assert a != 1  # dev: one
    assert a != 2, "two"  # dev: error
    assert a != 3  # error
    assert a != 4  # dev: such modifiable, wow
    if a != 31337:
        return True
    raise "awesome show"  # dev: great job


@external
@view
def fixedType(a: decimal, b: decimal[2]) -> decimal[3]:
    return [a, b[0], b[1]]


@external
def outOfBounds(i: uint256, _value: uint256) -> bool:
    self.stuff[i] = _value
    return True


@external
def overflow(a: uint256, b: uint256) -> uint256:
    return a * b


@external
def underflow(a: uint256, b: uint256) -> uint256:
    return a - b


@external
def zeroDivision(a: uint256, b: uint256) -> uint256:
    return a / b


@external
def zeroModulo(a: uint256, b: uint256) -> uint256:
    return a % b
