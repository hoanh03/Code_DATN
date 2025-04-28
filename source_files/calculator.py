# calculator.py

def add(a: int, b: int) -> int:
    """Add two integers and return the result."""
    return a + b

def subtract(a: int, b: int) -> int:
    """Subtract b from a and return the result."""
    return a - b

def multiply(a: int, b: int) -> int:
    """Multiply two integers and return the result."""
    return a * b

def divide(a: int, b: int) -> float:
    """Divide a by b and return the result as a float.

    Raises:
        ZeroDivisionError: If b is zero
    """
    return a / b

def power(a: int, b: int) -> int:
    """Raise a to the power of b and return the result."""
    return a ** b

def modulus(a: int, b: int) -> int:
    """Return the remainder of a divided by b.

    Raises:
        ZeroDivisionError: If b is zero
    """
    return a % b

def square_root(a: int) -> float:
    """Return the square root of a.

    Raises:
        ValueError: If a is negative
    """
    if a < 0:
        raise ValueError("Cannot calculate square root of a negative number")
    return a ** 0.5

def absolute(a: int) -> int:
    """Return the absolute value of a."""
    return abs(a)
