# test_case_generator.py

import inspect
import json
import os
import random
import signal
import string
import sys
import platform
from dataclasses import dataclass
from inspect import Signature
from typing import Any, Callable, Dict, List, Tuple, Type, Union, get_type_hints

# Flag to check if we're on Windows
IS_WINDOWS = platform.system() == 'Windows'

# Define a timeout exception
class TimeoutException(Exception):
    pass

# Define a timeout handler
def timeout_handler(signum, frame):
    raise TimeoutException("Function execution timed out")


@dataclass
class TestCase:
    """Represents a single test case for a function."""
    inputs: List[Any]
    expected_output: Any
    description: str = ""
    raises: Type[Exception] = None


class TestCaseGenerator:
    """
    Generates test cases for Python functions using reflection.

    This class analyzes function signatures, parameter types, and return types
    to generate appropriate test cases automatically.
    """

    DEFAULT_NUM_CASES = 5

    def __init__(self):
        self.type_generators = {
            int: self._generate_int_values,
            float: self._generate_float_values,
            str: self._generate_string_values,
            bool: self._generate_bool_values,
            list: self._generate_list_values,
            dict: self._generate_dict_values,
            tuple: self._generate_tuple_values,
        }

        # Add edge case generators for common types
        self.edge_case_generators = {
            int: lambda: [0, 1, -1, 100, -100],  # Avoid sys.maxsize to prevent potential overflow
            float: lambda: [0.0, 1.0, -1.0, 100.0, -100.0],  # Avoid infinity and NaN values
            str: lambda: ["", "a", " ", "abc", "A" * 100],
            bool: lambda: [True, False],
            list: lambda: [[], [1], [1, 2, 3]],
            dict: lambda: [{}, {"key": "value"}, {"a": 1, "b": 2}],
            tuple: lambda: [(), (1,), (1, 2, 3)],
        }

    def generate_test_cases(self, func: Callable, num_cases: int = DEFAULT_NUM_CASES) -> List[TestCase]:
        """
        Generate test cases for the given function.

        Args:
            func: The function to generate test cases for
            num_cases: Number of test cases to generate (excluding edge cases)

        Returns:
            A list of TestCase objects
        """
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)
        type_hints.get('return', Any)

        test_cases : List[TestCase] = []

        # Add edge cases first
        edge_cases = self._generate_edge_cases(func, sig, type_hints)
        test_cases.extend(edge_cases)

        # Add random test cases
        for _ in range(num_cases):
            inputs = []
            for param_name, param in sig.parameters.items():
                param_type = type_hints.get(param_name, Any)
                value = self._generate_value_for_type(param_type)
                inputs.append(value)

            try:
                if not IS_WINDOWS:
                    # Set a timeout for function execution (3 seconds) - only on non-Windows platforms
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(3)

                try:
                    # Execute the function with the generated inputs to get expected output
                    expected_output = func(*inputs)
                    test_case = TestCase(
                        inputs=inputs,
                        expected_output=expected_output,
                        description=f"Test with inputs: {inputs}"
                    )
                    test_cases.append(test_case)
                except TimeoutException:
                    # If the function execution times out, skip this test case
                    print(f"Warning: Function execution timed out for {func.__name__} with inputs {inputs}")
                    continue
                except Exception as e:
                    # If the function raises an exception, create a test case for that
                    test_case = TestCase(
                        inputs=inputs,
                        expected_output=None,
                        description=f"Test with inputs: {inputs} (raises {type(e).__name__})",
                        raises=type(e)
                    )
                    test_cases.append(test_case)
                finally:
                    # Cancel the alarm, but only if we set it (non-Windows platforms)
                    if not IS_WINDOWS:
                        signal.alarm(0)
            except Exception as e:
                # Handle any other exceptions
                print(f"Error generating test case: {str(e)}")
                continue

        return test_cases

    def _generate_edge_cases(self, func: Callable, sig: Signature,
                            type_hints: Dict[str, Type]) -> List[TestCase]:
        """Generate edge cases for the given function."""
        edge_cases = []

        # Get parameter edge values
        param_edge_values = {}
        for param_name, param in sig.parameters.items():
            param_type = type_hints.get(param_name, Any)
            if param_type in self.edge_case_generators:
                param_edge_values[param_name] = self.edge_case_generators[param_type]()
            else:
                # For unsupported types, use a single None value
                param_edge_values[param_name] = [None]

        # Generate combinations of edge values (limit to avoid explosion)
        param_names = list(sig.parameters.keys())
        if not param_names:
            return []

        # For each parameter, try its edge values while keeping others at "normal" values
        for idx, param_name in enumerate(param_names):
            for edge_value in param_edge_values[param_name]:
                inputs = []
                for inner_idx, inner_param in enumerate(param_names):
                    if inner_idx == idx:
                        inputs.append(edge_value)
                    else:
                        # Use a "typical" value for other parameters
                        param_type = type_hints.get(inner_param, Any)
                        if param_type in self.type_generators:
                            inputs.append(self.type_generators[param_type](1)[0])
                        else:
                            inputs.append(None)

                try:
                    if not IS_WINDOWS:
                        # Set a timeout for function execution (3 seconds) - only on non-Windows platforms
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
                        # If the function execution times out, skip this test case
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
                        # Cancel the alarm, but only if we set it (non-Windows platforms)
                        if not IS_WINDOWS:
                            signal.alarm(0)
                except Exception as e:
                    # Handle any other exceptions
                    print(f"Error generating edge case: {str(e)}")
                    continue

        return edge_cases

    def _generate_value_for_type(self, param_type: Type) -> Any:
        """Generate a random value for the given type."""
        if param_type in self.type_generators:
            return self.type_generators[param_type](1)[0]
        else:
            # For unsupported types, return None
            return None

    def _generate_int_values(self, count: int) -> List[int]:
        """Generate random integer values."""
        return [random.randint(-1000, 1000) for _ in range(count)]

    def _generate_float_values(self, count: int) -> List[float]:
        """Generate random float values."""
        return [random.uniform(-1000.0, 1000.0) for _ in range(count)]

    def _generate_string_values(self, count: int) -> List[str]:
        """Generate random string values."""
        return [''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(0, 20)))
                for _ in range(count)]

    def _generate_bool_values(self, count: int) -> List[bool]:
        """Generate random boolean values."""
        return [random.choice([True, False]) for _ in range(count)]

    def _generate_list_values(self, count: int) -> List[List[Any]]:
        """Generate random list values."""
        lists = []
        for _ in range(count):
            length = random.randint(0, 5)
            lists.append([random.randint(-100, 100) for _ in range(length)])
        return lists

    def _generate_dict_values(self, count: int) -> List[Dict[str, Any]]:
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

    def _generate_tuple_values(self, count: int) -> List[Tuple[Any, ...]]:
        """Generate random tuple values."""
        tuples = []
        for _ in range(count):
            length = random.randint(0, 5)
            tuples.append(tuple(random.randint(-100, 100) for _ in range(length)))
        return tuples


def generate_pytest_file(module_path: str, output_path: str = None, num_cases: int = 5) -> str:
    """
    Generate a pytest file for a given module.

    Args:
        module_path: Path to the Python module file
        output_path: Path where the pytest file should be saved (if None, just returns content)
        num_cases: Number of test cases to generate per function

    Returns:
        The content of the generated pytest file
    """
    import importlib.util

    # Import the module
    module_name = os.path.basename(module_path).replace('.py', '')
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {module_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    # Get all functions from the module
    functions = {}
    for name, obj in inspect.getmembers(module, inspect.isfunction):
        if obj.__module__ == module.__name__:
            functions[name] = obj

    # Generate test cases for each function
    generator = TestCaseGenerator()
    all_test_cases = {}
    for func_name, func in functions.items():
        test_cases = generator.generate_test_cases(func, num_cases)
        all_test_cases[func_name] = test_cases

    # Generate the pytest file content
    content = [
        f"# Automatically generated tests for {module_name}",
        "import pytest",
        f"from source_files.{module_name} import {', '.join(functions.keys())}",
        "",
        "# This file was generated by the test_case_generator"
    ]

    for func_name, test_cases in all_test_cases.items():
        content.append("")
        content.append(f"# Tests for {func_name}")

        # Generate a parametrized test for regular test cases
        regular_cases = [tc for tc in test_cases if tc.raises is None]
        if regular_cases:
            content.append(f"@pytest.mark.parametrize('inputs,expected', [")
            for tc in regular_cases:
                serialized_inputs = repr(tc.inputs)
                serialized_expected = repr(tc.expected_output)
                content.append(f"    # {tc.description}")
                content.append(f"    ({serialized_inputs}, {serialized_expected}),")
            content.append("])")
            content.append(f"def test_{func_name}(inputs, expected):")
            content.append(f"    assert {func_name}(*inputs) == expected")
            content.append("")

        # Generate separate tests for test cases that raise exceptions
        exception_cases = [tc for tc in test_cases if tc.raises is not None]
        for i, tc in enumerate(exception_cases):
            content.append(f"def test_{func_name}_raises_{i}():")
            content.append(f"    # {tc.description}")
            content.append(f"    with pytest.raises({tc.raises.__name__}):")
            content.append(f"        {func_name}(*{repr(tc.inputs)})")
            content.append("")

    final_content = "\n".join(content)

    # Save to file if output_path is provided
    if output_path:
        with open(output_path, 'w') as f:
            f.write(final_content)

    return final_content




if __name__ == "__main__":
    # Example usage
    import argparse

    parser = argparse.ArgumentParser(description='Generate test cases for Python modules')
    parser.add_argument('module_path', help='Path to the Python module file')
    parser.add_argument('--output', '-o', help='Path where the output file should be saved')
    parser.add_argument('--num-cases', '-n', type=int, default=5,
                        help='Number of test cases to generate per function')

    args = parser.parse_args()

    output_path = args.output or f"test_{os.path.basename(args.module_path)}"
    generate_pytest_file(args.module_path, output_path, args.num_cases)
    print(f"Generated pytest file at {output_path}")
