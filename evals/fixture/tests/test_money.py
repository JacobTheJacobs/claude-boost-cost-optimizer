from shop.money import fmt


def test_fmt():
    assert fmt(1234.5) == "$1,234.50"
