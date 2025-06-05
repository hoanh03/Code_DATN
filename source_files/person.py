# person.py

from typing import Optional


class Person:
    """Một lớp đơn giản đại diện cho một con người."""
    
    def __init__(self, name: str, age: int):
        """
        Khởi tạo một đối tượng Person.

        Tham số:
            name: Tên của người.
            age: Tuổi của người.

        Ngoại lệ:
            ValueError: Nếu tên rỗng hoặc tuổi là số âm.
        """

        if not name:
            raise ValueError("Name cannot be empty")
        if age < 0:
            raise ValueError("Age cannot be negative")
            
        self.name = name
        self.age = age
        
    def greet(self) -> str:
        """Trả về một thông điệp chào hỏi."""
        return f"Hello, my name is {self.name} and I am {self.age} years old."
        
    def have_birthday(self) -> None:
        """Tăng tuổi của người lên 1."""
        self.age += 1