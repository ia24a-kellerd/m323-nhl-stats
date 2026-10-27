from services.functional import compose, identity


def test_compose_applies_functions_left_to_right():
    add_one = lambda x: x + 1
    double = lambda x: x * 2

    assert compose(add_one, double)(3) == 8
    assert compose(double, add_one)(3) == 7


def test_compose_without_functions_is_identity():
    assert compose()(42) == 42
    assert identity("x") == "x"
