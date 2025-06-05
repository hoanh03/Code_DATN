# models.py
# Chứa các mô hình dữ liệu cho gói test_case_generator

from dataclasses import dataclass
from typing import Any, List, Type, Optional, Callable

@dataclass
class TestCase:
    """Đại diện cho một trường hợp kiểm thử (test case) đơn lẻ của một hàm."""
    inputs: List[Any]
    expected_output: Any
    description: str = ""
    raises: Type[Exception] = None

@dataclass
class ClassMethodTestCase:
    """Đại diện cho một trường hợp kiểm thử (test case) đơn lẻ của một phương thức lớp."""
    class_type: Type
    constructor_inputs: List[Any]
    method_name: str
    method_inputs: List[Any]
    expected_output: Any
    description: str = ""
    raises: Type[Exception] = None
    pre_state_validation: Optional[Callable] = None
    post_state_validation: Optional[Callable] = None
    is_property_getter: bool = False
