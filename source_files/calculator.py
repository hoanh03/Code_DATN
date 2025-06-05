# calculator.py

def add(a: int, b: int) -> int:
    """Cộng hai số nguyên và trả về kết quả."""
    return a + b

def subtract(a: int, b: int) -> int:
    """Trừ b khỏi a và trả về kết quả."""
    return a - b

def multiply(a: int, b: int) -> int:
    """Nhân hai số nguyên và trả về kết quả."""
    return a * b

def divide(a: int, b: int) -> float:
    """Chia a cho b và trả về kết quả dạng số thực.

    Ngoại lệ:
        ZeroDivisionError: Nếu b bằng 0
    """
    return a / b

def power(a: int, b: int) -> int:
    """Lũy thừa a với b và trả về kết quả."""
    return a ** b

def modulus(a: int, b: int) -> int:
    """Trả về phần dư của phép chia a cho b.

        Ngoại lệ:
            ZeroDivisionError: Nếu b bằng 0
        """
    return a % b

def square_root(a: int) -> float:
    """Trả về căn bậc hai của a.

    Ngoại lệ:
        ValueError: Nếu a là số âm
    """
    if a < 0:
        raise ValueError("Cannot calculate square root of a negative number")
    return a ** 0.5

def absolute(a: int) -> int:
    """Trả về giá trị tuyệt đối của a."""
    return abs(a)
