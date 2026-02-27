import pytest
from calculator import Calculator


@pytest.fixture
def calc():
    return Calculator()


def test_add(calc):
    assert calc.add(5, 3) == 8.0
    assert calc.add(-3, 3) == 0.0
    assert calc.add(-3, -3) == -6.0


def test_subtract(calc):
    assert calc.subtract(5, 3) == 2.0
    assert calc.subtract(-3, 3) == -6.0


def test_multiply(calc):
    assert calc.multiply(5, 3) == 15.0
    assert calc.multiply(5, 0) == 0.0
    assert calc.multiply(-5, 3) == -15.0


def test_divide(calc):
    assert calc.divide(5, 2) == 2.5
    assert calc.divide(-5, 2) == -2.5


def test_divide_by_zero(calc):
    with pytest.raises(ZeroDivisionError):
        calc.divide(5, 0)


def test_calculate_with_operator(calc):
    assert calc.calculate(5, "+", 3) == 8.0
    assert calc.calculate(5, "-", 3) == 2.0
    assert calc.calculate(5, "*", 3) == 15.0
    assert calc.calculate(5, "/", 2) == 2.5


def test_unknown_operator(calc):
    with pytest.raises(ValueError):
        calc.calculate(5, "%", 3)
