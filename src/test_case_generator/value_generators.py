# value_generators.py
# Contains functions for generating test values of different types

import random
import string
from typing import Any, Dict, List, Tuple, Type

class ValueGenerator:
    """Generates random values for different types."""

    @staticmethod
    def generate_int_values(count: int, min_value: int = -1000, max_value: int = 1000) -> List[int]:
        """Generate random integer values."""
        return [random.randint(min_value, max_value) for _ in range(count)]

    @staticmethod
    def generate_float_values(count: int, min_value: float = -1000.0, max_value: float = 1000.0) -> List[float]:
        """Generate random float values."""
        return [random.uniform(min_value, max_value) for _ in range(count)]

    @staticmethod
    def generate_positive_float_values(count: int, min_value: float = 0.01, max_value: float = 1000.0) -> List[float]:
        """Generate random positive float values."""
        return [random.uniform(min_value, max_value) for _ in range(count)]

    @staticmethod
    def generate_string_values(count: int, min_length: int = 0, max_length: int = 20, 
                              allowed_chars: str = string.ascii_letters + string.digits) -> List[str]:
        """Generate random string values."""
        return [''.join(random.choices(allowed_chars, k=random.randint(min_length, max_length)))
                for _ in range(count)]

    @staticmethod
    def generate_alphanumeric_string_values(count: int, min_length: int = 5, max_length: int = 20) -> List[str]:
        """Generate random alphanumeric string values with specific length constraints."""
        return [''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(min_length, max_length)))
                for _ in range(count)]

    @staticmethod
    def generate_name_values(count: int, min_length: int = 4, max_length: int = 50, 
                            exclude_values: List[str] = None) -> List[str]:
        """Generate random name values with specific length constraints and exclusions."""
        if exclude_values is None:
            exclude_values = ['abc']

        names = []
        for _ in range(count):
            while True:
                name = ''.join(random.choices(string.ascii_letters + ' ', k=random.randint(min_length, max_length)))
                if name not in exclude_values:
                    names.append(name)
                    break
        return names

    @staticmethod
    def generate_bool_values(count: int) -> List[bool]:
        """Generate random boolean values."""
        return [random.choice([True, False]) for _ in range(count)]

    @staticmethod
    def generate_list_values(count: int) -> List[List[Any]]:
        """Generate random list values."""
        lists = []
        for _ in range(count):
            length = random.randint(0, 5)
            lists.append([random.randint(-100, 100) for _ in range(length)])
        return lists

    @staticmethod
    def generate_dict_values(count: int) -> List[Dict[str, Any]]:
        """Generate random dictionary values."""
        dicts = []
        for _ in range(count):
            length = random.randint(0, 5)
            d = {}
            for _ in range(length):
                key = ''.join(random.choices(string.ascii_lowercase, k=random.randint(1, 5)))
                value = random.randint(-100, 100)
                d[key] = value
            dicts.append(d)
        return dicts

    @staticmethod
    def generate_tuple_values(count: int) -> List[Tuple[Any, ...]]:
        """Generate random tuple values."""
        tuples = []
        for _ in range(count):
            length = random.randint(0, 5)
            tuples.append(tuple(random.randint(-100, 100) for _ in range(length)))
        return tuples

    @classmethod
    def get_generator_for_type(cls, param_type: Type) -> callable:
        """Get the appropriate generator function for the given type."""
        type_generators = {
            int: cls.generate_int_values,
            float: cls.generate_float_values,
            str: cls.generate_string_values,
            bool: cls.generate_bool_values,
            list: cls.generate_list_values,
            dict: cls.generate_dict_values,
            tuple: cls.generate_tuple_values,
        }
        return type_generators.get(param_type)

    @classmethod
    def get_edge_cases_for_type(cls, param_type: Type) -> List[Any]:
        """Get edge cases for the given type."""
        edge_cases = {
            int: [0, 1, -1, 100, -100],
            float: [0.0, 1.0, -1.0, 100.0, -100.0],
            str: ["", "a", " ", "abc", "A" * 100],
            bool: [True, False],
            list: [[], [1], [1, 2, 3]],
            dict: [{}, {"key": "value"}, {"a": 1, "b": 2}],
            tuple: [(), (1,), (1, 2, 3)],
        }
        return edge_cases.get(param_type, [None])
