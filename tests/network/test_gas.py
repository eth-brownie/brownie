import pytest

from brownie.network.gas.strategies import ExponentialScalingStrategy, LinearScalingStrategy


def test_linear_initial():
    strat = LinearScalingStrategy(1, 10)
    generator = strat.get_gas_price()
    assert next(generator) == 1


def test_linear_max():
    strat = LinearScalingStrategy(100, 1000)
    generator = strat.get_gas_price()
    last = next(generator)
    for i in range(20):
        if last == 1000:
            assert next(generator) == 1000
        else:
            value = next(generator)
            assert last < value <= 1000
            last = value


@pytest.mark.parametrize("increment", [1.1, 1.25, 1.337, 2])
def test_linear_increment(increment):
    strat = LinearScalingStrategy(100, 100000000000, increment=increment)
    generator = strat.get_gas_price()

    last = next(generator)

    for i in range(20):
        value = next(generator)
        assert int(last * increment) == value
        last = value


def test_exponential_initial():
    strat = ExponentialScalingStrategy(1, 10)
    generator = strat.get_gas_price()
    assert next(generator) == 1


def test_exponential_max():
    strat = ExponentialScalingStrategy(100, 1000)
    generator = strat.get_gas_price()
    last = next(generator)
    for i in range(20):
        if last == 1000:
            assert next(generator) == 1000
        else:
            value = next(generator)
            assert last < value <= 1000
            last = value


def test_exponential_increment():
    strat = ExponentialScalingStrategy(100, 100000000000)
    generator = strat.get_gas_price()

    values = [next(generator) for i in range(20)]

    diff = values[1] - values[0]
    for i in range(2, 20):
        assert values[i] - values[i - 1] > diff
        diff = values[i] - values[i - 1]
