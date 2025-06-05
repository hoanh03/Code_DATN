# pytest_generator.py
# Contains functions for generating pytest files

import importlib.util
import inspect
import os
import sys
from typing import Dict, List

from .models import ClassMethodTestCase


# Import TestCaseGenerator inside the function to avoid circular imports

def _serialize_method_inputs(method_inputs, mock_functions=None):
    """
    Serialize a list of method inputs to a string that can be used in generated code.

    Args:
        method_inputs: List of input values to serialize
        mock_functions: Optional set to collect mock function names

    Returns:
        A string representation of the method inputs list
    """
    method_inputs_list = []
    for input_value in method_inputs:
        # Handle None
        if input_value is None:
            method_inputs_list.append('None')
        # Handle complex objects with memory addresses
        elif str(input_value).startswith('<') and ' object at 0x' in str(input_value):
            # Extract the class name from the string representation
            class_name = str(input_value).split(' ')[0][1:]  # Remove '<' and get the class name

            # For complex objects, use a generic placeholder
            mock_func_name = f'create_mock_{class_name.replace(".", "_")}_instance'

            # Add to the set of mock functions if provided
            if mock_functions is not None:
                mock_functions.add((mock_func_name, class_name))

            method_inputs_list.append(f'{mock_func_name}()')
        # Default to repr for other types
        else:
            method_inputs_list.append(repr(input_value))
    return "[" + ", ".join(method_inputs_list) + "]"


def _generate_parametrized_test(content, test_name, test_cases, param_names, param_values_func, test_body_func, fixture_param=None):
    """
    Generate a parametrized test for regular test cases.

    Args:
        content: List to append the generated content to
        test_name: Name of the test function
        test_cases: List of test cases
        param_names: String of parameter names for the parametrize decorator
        param_values_func: Function that takes a test case and returns the parameter values
        test_body_func: Function that takes no arguments and returns the test body lines
        fixture_param: Optional fixture parameter to add to the function signature

    Returns:
        None (modifies content in-place)
    """
    content.append(f"@pytest.mark.parametrize('{param_names}', [")
    for tc in test_cases:
        content.append(f"    # {tc.description}")
        content.append(f"    {param_values_func(tc)},")
    content.append("])")

    # Add fixture parameter to the function signature if provided
    if fixture_param:
        content.append(f"def {test_name}({param_names.replace(',', ', ')}, {fixture_param}):")
    else:
        content.append(f"def {test_name}({param_names.replace(',', ', ')}):")

    content.extend(test_body_func())
    content.append("")


def _generate_exception_test(content, test_name, tc, exception_code_func, fixture_param=None):
    """
    Generate a test for a case that raises an exception.

    Args:
        content: List to append the generated content to
        test_name: Name of the test function
        tc: Test case that raises an exception
        exception_code_func: Function that takes no arguments and returns the code that should raise the exception
        fixture_param: Optional fixture parameter to add to the function signature

    Returns:
        None (modifies content in-place)
    """
    # Add fixture parameter to the function signature if provided
    if fixture_param:
        content.append(f"def {test_name}({fixture_param}):")
    else:
        content.append(f"def {test_name}():")

    content.append(f"    # {tc.description}")
    content.append(f"    with pytest.raises({tc.raises.__name__}):")
    content.extend(exception_code_func())
    content.append("")

def _generate_class_pytest_content(cls_name: str, test_cases: Dict[str, List[ClassMethodTestCase]], mock_functions=None, valid_constructor_inputs=None) -> List[str]:
    """
    Generate pytest content for a class.

    Args:
        cls_name: Name of the class
        test_cases: Dictionary mapping method names to lists of ClassMethodTestCase objects
        mock_functions: Optional set to collect mock function names
        valid_constructor_inputs: Optional dictionary to store valid constructor inputs for each class

    Returns:
        List of strings representing pytest content
    """
    content = [
        f"# Tests for class {cls_name}",
        ""
    ]

    # Only create a fixture if there are test cases
    if test_cases:
        # Find a valid constructor test case to use for the fixture
        valid_constructor_case = None
        if '__init__' in test_cases:
            for tc in test_cases['__init__']:
                if tc.raises is None:
                    valid_constructor_case = tc
                    break

        if valid_constructor_case:
            # Create a fixture with valid constructor inputs
            content.extend([
                "@pytest.fixture",
                f"def {cls_name.lower()}_instance():",
                f"    # Create a valid instance of {cls_name} for testing",
                f"    return {cls_name}(*{repr(valid_constructor_case.constructor_inputs)})",
                ""
            ])

            # Store valid constructor inputs for this class
            if valid_constructor_inputs is not None:
                valid_constructor_inputs[cls_name] = valid_constructor_case.constructor_inputs
        else:
            # If no valid constructor case found, add a comment explaining why no fixture is created
            content.extend([
                f"# Note: No fixture created for {cls_name} as no valid constructor test case was found",
                ""
            ])

    # Generate tests for constructor
    if '__init__' in test_cases:
        constructor_cases = test_cases['__init__']

        # Regular constructor cases
        regular_cases = [tc for tc in constructor_cases if tc.raises is None]
        if regular_cases:
            content.append(f"# Tests for {cls_name} constructor")

            def param_values_func(tc):
                return repr(tc.constructor_inputs)

            def test_body_func():
                return [
                    f"    instance = {cls_name.lower()}_instance",
                    f"    assert isinstance(instance, {cls_name})"
                ]

            _generate_parametrized_test(
                content,
                f"test_{cls_name}_constructor",
                regular_cases,
                'constructor_inputs',
                param_values_func,
                test_body_func
            )

        # Constructor cases that raise exceptions
        exception_cases = [tc for tc in constructor_cases if tc.raises is not None]
        for i, tc in enumerate(exception_cases):
            def exception_code_func():
                return [f"        {cls_name}(*{repr(tc.constructor_inputs)})"]

            _generate_exception_test(
                content,
                f"test_{cls_name}_constructor_raises_{i}",
                tc,
                exception_code_func
            )

    # Generate tests for methods
    for method_name, method_cases in test_cases.items():
        if method_name == '__init__':
            continue  # Already handled

        # Check if this is a property getter by looking at the is_property_getter field
        is_property = any(tc.is_property_getter for tc in method_cases)

        if is_property and method_name.startswith('get_'):
            # Property getter tests
            prop_name = method_name[4:]  # Remove 'get_' prefix
            content.append(f"# Tests for {cls_name}.{prop_name} property getter")

            # Regular getter cases
            regular_cases = [tc for tc in method_cases if tc.raises is None]
            if regular_cases:
                def param_values_func(tc):
                    serialized_inputs = repr(tc.constructor_inputs)
                    serialized_expected = repr(tc.expected_output)
                    return f"({serialized_inputs}, {serialized_expected})"

                def test_body_func():
                    return [
                        f"    instance = {cls_name.lower()}_instance",
                        f"    assert instance.{prop_name} == expected"
                    ]

                _generate_parametrized_test(
                    content,
                    f"test_{cls_name}_{prop_name}_getter",
                    regular_cases,
                    'constructor_inputs,expected',
                    param_values_func,
                    test_body_func,
                    f"{cls_name.lower()}_instance"
                )

            # Getter cases that raise exceptions
            exception_cases = [tc for tc in method_cases if tc.raises is not None]
            for i, tc in enumerate(exception_cases):
                def exception_code_func():
                    return [
                        f"        instance = {cls_name.lower()}_instance",
                        f"        value = instance.{prop_name}"
                    ]

                _generate_exception_test(
                    content,
                    f"test_{cls_name}_{prop_name}_getter_raises_{i}",
                    tc,
                    exception_code_func,
                    f"{cls_name.lower()}_instance"
                )

        elif method_name.startswith('set_'):
            # Property setter tests
            prop_name = method_name[4:]  # Remove 'set_' prefix
            content.append(f"# Tests for {cls_name}.{prop_name} property setter")

            # Regular setter cases
            regular_cases = [tc for tc in method_cases if tc.raises is None]
            if regular_cases:
                def param_values_func(tc):
                    serialized_inputs = repr(tc.constructor_inputs)
                    serialized_value = repr(tc.method_inputs[0])
                    serialized_expected = repr(tc.expected_output)
                    return f"({serialized_inputs}, {serialized_value}, {serialized_expected})"

                def test_body_func():
                    return [
                        f"    instance = {cls_name.lower()}_instance",
                        f"    instance.{prop_name} = value",
                        f"    assert instance.{prop_name} == expected"
                    ]

                _generate_parametrized_test(
                    content,
                    f"test_{cls_name}_{prop_name}_setter",
                    regular_cases,
                    'constructor_inputs,value,expected',
                    param_values_func,
                    test_body_func,
                    f"{cls_name.lower()}_instance"
                )

            # Setter cases that raise exceptions
            exception_cases = [tc for tc in method_cases if tc.raises is not None]
            for i, tc in enumerate(exception_cases):
                def exception_code_func():
                    return [
                        f"        instance = {cls_name.lower()}_instance",
                        f"        instance.{prop_name} = {repr(tc.method_inputs[0])}"
                    ]

                _generate_exception_test(
                    content,
                    f"test_{cls_name}_{prop_name}_setter_raises_{i}",
                    tc,
                    exception_code_func,
                    f"{cls_name.lower()}_instance"
                )

        else:
            # Regular method tests
            content.append(f"# Tests for {cls_name}.{method_name} method")

            # Regular method cases
            regular_cases = [tc for tc in method_cases if tc.raises is None]
            if regular_cases:
                def param_values_func(tc):
                    serialized_constructor_inputs = repr(tc.constructor_inputs)
                    serialized_method_inputs = _serialize_method_inputs(tc.method_inputs, mock_functions)
                    serialized_expected = repr(tc.expected_output)
                    return f"({serialized_constructor_inputs}, {serialized_method_inputs}, {serialized_expected})"

                def test_body_func():
                    return [
                        f"    instance = {cls_name.lower()}_instance",
                        f"    result = instance.{method_name}(*method_inputs)",
                        f"    assert result == expected"
                    ]

                # Define param_names for the parametrize decorator
                param_names = 'constructor_inputs,method_inputs,expected'

                # Add fixture parameter to the function signature
                content.append(f"@pytest.mark.parametrize('{param_names}', [")
                for tc in regular_cases:
                    content.append(f"    # {tc.description}")
                    content.append(f"    {param_values_func(tc)},")
                content.append("])")
                content.append(f"def test_{cls_name}_{method_name}({param_names.replace(',', ', ')}, {cls_name.lower()}_instance):")
                content.extend(test_body_func())
                content.append("")

            # Method cases that raise exceptions
            exception_cases = [tc for tc in method_cases if tc.raises is not None]
            for i, tc in enumerate(exception_cases):
                serialized_method_inputs = _serialize_method_inputs(tc.method_inputs, mock_functions)

                def exception_code_func():
                    return [
                        f"        instance = {cls_name.lower()}_instance",
                        f"        instance.{method_name}(*{serialized_method_inputs})"
                    ]

                _generate_exception_test(
                    content,
                    f"test_{cls_name}_{method_name}_raises_{i}",
                    tc,
                    exception_code_func,
                    f"{cls_name.lower()}_instance"
                )

    return content


def generate_pytest_file(module_path: str, output_path: str = None, num_cases: int = 5) -> str:
    """
    Generate a pytest file for a given module.

    Args:
        module_path: Path to the Python module file
        output_path: Path where the pytest file should be saved (if None, just returns content)
        num_cases: Number of test cases to generate per function/method

    Returns:
        The content of the generated pytest file
    """
    # Import the module
    module_name = os.path.basename(module_path).replace('.py', '')
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {module_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    # Get all functions and classes from the module
    functions = {}
    classes = {}
    for name, obj in inspect.getmembers(module):
        if inspect.isfunction(obj) and obj.__module__ == module.__name__:
            functions[name] = obj
        elif inspect.isclass(obj) and obj.__module__ == module.__name__:
            classes[name] = obj

    # Import TestCaseGenerator here to avoid circular imports
    from .test_generator import TestCaseGenerator

    # Generate test cases
    generator = TestCaseGenerator()

    # Generate function test cases
    function_test_cases = {}
    for func_name, func in functions.items():
        test_cases = generator.generate_test_cases(func, num_cases)
        function_test_cases[func_name] = test_cases

    # Generate class test cases
    class_test_cases = {}
    for cls_name, cls in classes.items():
        test_cases = generator.generate_class_test_cases(cls, num_cases)
        class_test_cases[cls_name] = test_cases

    # Create a set to collect mock functions and a dictionary to store valid constructor inputs for each class
    mock_functions = set()
    valid_constructor_inputs = {}

    # Generate the pytest file content
    content = [
        f"# Automatically generated tests for {module_name}",
        "import pytest",
        "import dataclasses",
        "import datetime",
        "import typing",
    ]

    # Extract all imports from the source file
    import_statements = []

    with open(module_path, 'r', encoding='utf-8') as f:
        source_code = f.read()

        # Find all import statements in the source code
        import_lines = [line.strip() for line in source_code.split('\n')
                       if line.strip().startswith(('import ', 'from ')) and 'import' in line]

        # Process each import statement
        for line in import_lines:
            # Skip imports from the module itself or relative imports
            if line.startswith('from .') or line.startswith('from __future__'):
                continue

            # Handle 'import module' statements
            if line.startswith('import '):
                modules = line[7:].split(',')
                for module in modules:
                    module = module.strip().split(' as ')[0]  # Remove 'as alias' if present
                    if module and module != module_name:
                        import_statements.append(f"import {module}")

            # Handle 'from module import ...' statements
            elif line.startswith('from '):
                parts = line.split(' import ')
                if len(parts) == 2:
                    module = parts[0][5:].strip()
                    if module and module != module_name and module != '__future__':
                        # We import the whole module rather than specific items
                        import_statements.append(f"import {module}")

    # Add unique imports to content
    for import_stmt in sorted(set(import_statements)):
        content.append(import_stmt)

    # Import statements
    if functions:
        content.append(f"from source_files.{module_name} import {', '.join(functions.keys())}")
    if classes:
        content.append(f"from source_files.{module_name} import {', '.join(classes.keys())}")

    content.extend([
        "",
        "# This file was generated by the test_case_generator"
    ])

    # Generate mock function definitions
    if mock_functions:
        content.append("")
        for mock_func_name, class_name in mock_functions:
            content.append(f"def {mock_func_name}():")
            content.append(f"    # Create a valid instance of {class_name} for testing")
            # Use valid constructor inputs if available, otherwise use an empty list
            constructor_inputs = valid_constructor_inputs.get(class_name, [])
            content.append(f"    return {class_name}(*{repr(constructor_inputs)})")
            content.append("")

    # Generate function tests
    for func_name, test_cases in function_test_cases.items():
        content.append("")
        content.append(f"# Tests for function {func_name}")

        # Generate a parametrized test for regular test cases
        regular_cases = [tc for tc in test_cases if tc.raises is None]
        if regular_cases:
            def param_values_func(tc):
                serialized_inputs = repr(tc.inputs)
                serialized_expected = repr(tc.expected_output)
                return f"({serialized_inputs}, {serialized_expected})"

            def test_body_func():
                return [
                    f"    assert {func_name}(*inputs) == expected"
                ]

            _generate_parametrized_test(
                content,
                f"test_{func_name}",
                regular_cases,
                'inputs,expected',
                param_values_func,
                test_body_func
            )

        # Generate separate tests for test cases that raise exceptions
        exception_cases = [tc for tc in test_cases if tc.raises is not None]
        for i, tc in enumerate(exception_cases):
            def exception_code_func():
                return [
                    f"        {func_name}(*{repr(tc.inputs)})"
                ]

            _generate_exception_test(
                content,
                f"test_{func_name}_raises_{i}",
                tc,
                exception_code_func
            )

    # Generate class tests
    for cls_name, test_cases in class_test_cases.items():
        content.append("")
        class_content = _generate_class_pytest_content(cls_name, test_cases, mock_functions, valid_constructor_inputs)
        content.extend(class_content)

    final_content = "\n".join(content)

    # Save to file if output_path is provided
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_content)

    return final_content
