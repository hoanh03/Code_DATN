# test_generator.py
# Chứa lớp chính TestCaseGenerator

import inspect
import signal
import platform
import random
from inspect import Signature
from typing import Any, Callable, Dict, List, Type, Union, get_type_hints

from .models import TestCase, ClassMethodTestCase
from .exceptions import TimeoutException, timeout_handler
from .value_generators import ValueGenerator
from .class_analyzer import ClassAnalyzer
from .test_generator_methods import _generate_constructor_test_cases, _generate_method_test_cases, \
    _generate_property_getter_test_cases, _generate_property_setter_test_cases
from .pytest_generator import generate_pytest_file

# Xuất lại hàm generate_pytest_file tại cấp module để giữ tính tương thích ngược
__all__ = ['TestCaseGenerator', 'generate_pytest_file']

# Làm cho generate_pytest_file có thể truy cập trực tiếp tại cấp module
# Điều này để đảm bảo tính tương thích ngược với mã đã từng sử dụng nó tại đây
globals()['generate_pytest_file'] = generate_pytest_file

# Gắn cờ để kiểm tra xem hệ thống có phải là Windows không
IS_WINDOWS = platform.system() == 'Windows'

class TestCaseGenerator:
    """
    Tạo các trường hợp kiểm thử (test case) cho các hàm và lớp Python bằng cách sử dụng kỹ thuật reflection.

    Lớp này phân tích chữ ký của hàm, loại tham số và loại giá trị trả về
    để tự động sinh ra các bài kiểm thử phù hợp. Ngoài ra nó cũng có thể phân tích các lớp
    và tạo kiểm thử cho các phương thức của lớp.
    """

    DEFAULT_NUM_CASES = 5

    def __init__(self):
        self.value_generator = ValueGenerator()

    def generate_test_cases(self, func: Callable, num_cases: int = DEFAULT_NUM_CASES) -> List[TestCase]:
        """
        Tạo các trường hợp kiểm thử cho hàm đã cho.

        Tham số:
            func: Hàm cần sinh test case
            num_cases: Số lượng test case cần sinh (không bao gồm giá trị biên)

        Trả về:
            Một danh sách các đối tượng TestCase
        """
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)

        test_cases : List[TestCase] = []

        # Thêm các trường hợp biên (edge case) trước
        edge_cases = self._generate_edge_cases(func, sig, type_hints)
        test_cases.extend(edge_cases)

        # Thêm các trường hợp kiểm thử ngẫu nhiên
        for _ in range(num_cases):
            inputs = []
            for param_name, param in sig.parameters.items():
                param_type = type_hints.get(param_name, Any)
                value = self._generate_value_for_type(param_type, param_name)
                inputs.append(value)

            try:
                if not IS_WINDOWS:
                    # Đặt timeout cho việc thực thi hàm (3 giây) - chỉ áp dụng trên các nền tảng không phải Windows
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(3)

                try:
                    # Thực thi hàm với các đầu vào đã sinh ra để lấy kết quả mong muốn
                    expected_output = func(*inputs)
                    test_case = TestCase(
                        inputs=inputs,
                        expected_output=expected_output,
                        description=f"Test with inputs: {inputs}"
                    )
                    test_cases.append(test_case)
                except TimeoutException:
                    # Nếu thực thi hàm quá thời gian, bỏ qua trường hợp kiểm thử này
                    print(f"Warning: Function execution timed out for {func.__name__} with inputs {inputs}")
                    continue
                except Exception as e:
                    # Nếu hàm gây ra ngoại lệ, tạo trường hợp kiểm thử với ngoại lệ đó
                    test_case = TestCase(
                        inputs=inputs,
                        expected_output=None,
                        description=f"Test with inputs: {inputs} (raises {type(e).__name__})",
                        raises=type(e)
                    )
                    test_cases.append(test_case)
                finally:
                    # Hủy bỏ báo động (nếu đã đặt), chỉ áp dụng trên nền tảng không phải Windows
                    if not IS_WINDOWS:
                        signal.alarm(0)
            except Exception as e:
                # Xử lý bất kỳ ngoại lệ nào khác
                print(f"Error generating test case: {str(e)}")
                continue

        return test_cases

    def _generate_edge_cases(self, func: Callable, sig: Signature,
                            type_hints: Dict[str, Type]) -> List[TestCase]:
        """Generate edge cases for the given function."""
        edge_cases = []

        # Lấy các giá trị biên cho các tham số
        param_edge_values = {}
        for param_name, param in sig.parameters.items():
            param_type = type_hints.get(param_name, Any)
            # Tạo các giá trị biên dựa trên loại tham số
            param_edge_values[param_name] = ValueGenerator.get_edge_cases_for_type(param_type)

        # Tạo các tổ hợp giá trị biên (hạn chế để tránh tăng kích thước)
        param_names = list(sig.parameters.keys())
        if not param_names:
            return []

        # Đối với mỗi tham số, thử các giá trị biên trong khi giữ các giá trị khác ở trạng thái "bình thường"
        for idx, param_name in enumerate(param_names):
            for edge_value in param_edge_values[param_name]:
                inputs = []
                for inner_idx, inner_param in enumerate(param_names):
                    if inner_idx == idx:
                        inputs.append(edge_value)
                    else:
                        # Sử dụng giá trị "bình thường" cho các tham số khác
                        param_type = type_hints.get(inner_param, Any)
                        # Generate valid values for other parameters
                        value = self._generate_value_for_type(param_type, inner_param)
                        inputs.append(value)

                try:
                    if not IS_WINDOWS:
                        # Đặt timeout cho việc thực thi hàm (3 giây) - chỉ áp dụng trên nền tảng không phải Windows
                        signal.signal(signal.SIGALRM, timeout_handler)
                        signal.alarm(3)

                    try:
                        expected_output = func(*inputs)
                        edge_cases.append(TestCase(
                            inputs=inputs,
                            expected_output=expected_output,
                            description=f"Edge case for {param_name}={edge_value}"
                        ))
                    except TimeoutException:
                        # Nếu thực thi hàm quá thời gian, bỏ qua trường hợp kiểm thử này
                        print(f"Warning: Function execution timed out for {func.__name__} with edge case {param_name}={edge_value}")
                        continue
                    except Exception as e:
                        edge_cases.append(TestCase(
                            inputs=inputs,
                            expected_output=None,
                            description=f"Edge case for {param_name}={edge_value} (raises {type(e).__name__})",
                            raises=type(e)
                        ))
                    finally:
                        # Hủy bỏ báo động, chỉ áp dụng trên nền tảng không phải Windows
                        if not IS_WINDOWS:
                            signal.alarm(0)
                except Exception as e:
                    # Xử lý bất kỳ ngoại lệ nào khác
                    print(f"Error generating edge case: {str(e)}")
                    continue

        return edge_cases

    def _generate_value_for_type(self, param_type: Type, param_name: str = None, class_type: Type = None) -> Any:
        """
        Sinh một giá trị ngẫu nhiên cho loại được cung cấp, dựa trên loại tham số và loại lớp.

        Tham số:
            param_type: Loại của tham số
            param_name: Tên của tham số (tùy chọn)
            class_type: Lớp đang được kiểm thử (tùy chọn)

        Trả về:
            Một giá trị ngẫu nhiên tương ứng với loại tham số.
        """

        # Xử lý mặc định đối với các loại tiêu chuẩn
        if class_type and param_type and hasattr(param_type, '__name__') and param_type.__name__ == class_type.__name__:
            try:
                # Thử phân tích lớp và tạo một instance với các tham số hợp lệ
                from .class_analyzer import ClassAnalyzer
                class_info = ClassAnalyzer.analyze_class(param_type)
                if 'constructor' in class_info:
                    constructor_inputs = []
                    for inner_param_name, inner_param in class_info['constructor']['parameters'].items():
                        inner_param_type = class_info['constructor']['type_hints'].get(inner_param_name, Any)
                        # Gọi đệ quy để sinh giá trị cho các tham số constructor
                        # nhưng không truyền class_type để tránh đệ quy vô hạn
                        value = self._generate_value_for_type(inner_param_type, inner_param_name)
                        constructor_inputs.append(value)
                    return param_type(*constructor_inputs)
            except Exception as e:
                print(f"Error creating instance of {param_type.__name__}: {str(e)}")
                return None

        # Xử lý mặc định cho các loại chuẩn
        generator = ValueGenerator.get_generator_for_type(param_type)
        if generator:
            return generator(1)[0]
        else:
            # Đối với các loại không được hỗ trợ, trả về None
            return None

    def generate_class_test_cases(self, cls: Type, num_cases: int = DEFAULT_NUM_CASES) -> Dict[str, List[ClassMethodTestCase]]:
        """
        Tạo kiểm thử cho lớp Python đã cho.

        Tham số:
            cls: Lớp cần tạo kiểm thử
            num_cases: Số bài kiểm thử cần sinh ra cho mỗi phương thức

        Trả về:
            Từ điển ánh xạ tên phương thức đến danh sách các ClassMethodTestCase
        """

        class_info = ClassAnalyzer.analyze_class(cls)
        test_cases = {}

        # Tạo các trường hợp kiểm thử cho constructor
        if 'constructor' in class_info:
            constructor_cases = _generate_constructor_test_cases(self, cls, class_info['constructor'], num_cases)
            test_cases['__init__'] = constructor_cases

        # Tạo các trường hợp kiểm thử cho các phương thức
        for method_type, method_dict in [
            ('methods', class_info['methods']),
            ('class_methods', class_info['class_methods']),
            ('static_methods', class_info['static_methods'])
        ]:
            for method_name, method_info in method_dict.items():
                method_cases = _generate_method_test_cases(
                    self, cls, method_name, method_info, method_type, num_cases
                )
                test_cases[method_name] = method_cases

        # Tạo các trường hợp kiểm thử cho các thuộc tính
        for prop_name, prop_info in class_info['properties'].items():
            if prop_info['has_getter']:
                getter_cases = _generate_property_getter_test_cases(self, cls, prop_name, prop_info, num_cases)
                test_cases[f'get_{prop_name}'] = getter_cases

            if prop_info['has_setter']:
                setter_cases = _generate_property_setter_test_cases(self, cls, prop_name, prop_info, num_cases)
                test_cases[f'set_{prop_name}'] = setter_cases

        return test_cases

