"""Small calculator module used as a documentation-generator example."""

def triangle_area(base: float, height: float) -> float:
    """Calculate the area of a triangle."""
    return base * height / 2

def rectangle_area(width: float, height: float) -> float:
    """Calculate the area of a rectangle."""
    return width * height

class Calculator:
    """Simple calculator example."""

    def add(self, left: float, right: float) -> float:
        return left + right

    def multiply(self, left: float, right: float) -> float:
        return left * right
