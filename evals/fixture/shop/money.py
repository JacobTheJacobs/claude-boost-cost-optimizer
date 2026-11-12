"""Money helpers."""


def parse_price(text: str) -> float:
    """'$1,234.50' -> 1234.5"""
    text = text.strip().lstrip("$")
    return float(text.replace(".", "").replace(",", "."))


def fmt(x: float) -> str:
    return f"${x:,.2f}"
