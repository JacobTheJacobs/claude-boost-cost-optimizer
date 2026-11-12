"""Sales stats."""


def total(items):
    return sum(i["price"] * i["qty"] for i in items)


def mean_price(items):
    return sum(i["price"] for i in items) / len(items) if items else 0.0
