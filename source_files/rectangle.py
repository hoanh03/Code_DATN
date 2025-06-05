# rectangle.py


class Rectangle:
    """Một lớp đơn giản đại diện cho hình chữ nhật."""
    
    def __init__(self, width: float, height: float):
        """
        Khởi tạo một đối tượng Hình chữ nhật.

        Tham số:
            width: Chiều rộng của hình chữ nhật
            height: Chiều cao của hình chữ nhật

        Ngoại lệ:
            ValueError: Nếu chiều rộng hoặc chiều cao không phải là số dương
        """

        if width <= 0 or height <= 0:
            raise ValueError("Width and height must be positive")
            
        self.width = width
        self.height = height
        
    def area(self) -> float:
        """Tính diện tích của hình chữ nhật."""
        return self.width * self.height
        
    def perimeter(self) -> float:
        """Tính chu vi của hình chữ nhật."""
        return 2 * (self.width + self.height)