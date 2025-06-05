# test_generator_methods.py
# Contains additional methods for the TestCaseGenerator class

import signal
import json
import hashlib
from typing import Any, Dict, List, Type, Callable, Set, Tuple, Hashable

from .models import ClassMethodTestCase
from .exceptions import TimeoutException, timeout_handler
from .value_generators import ValueGenerator
from .class_analyzer import ClassAnalyzer

# Flag to check if we're on Windows
import platform

IS_WINDOWS = platform.system() == 'Windows'


def _are_functionally_equivalent(inputs1: List[Any], inputs2: List[Any]) -> bool:
    """
    Check if two sets of inputs are functionally equivalent.
    This uses Python's built-in comparison operators and repr() for complex objects.
    """
    if len(inputs1) != len(inputs2):
        return False

    for i, (val1, val2) in enumerate(zip(inputs1, inputs2)):
        # For basic types, use direct comparison
        if isinstance(val1, (int, float, str, bool)) and isinstance(val2, (int, float, str, bool)):
            if val1 != val2:
                return False
        # For collections, try direct comparison first
        elif isinstance(val1, (list, tuple)) and isinstance(val2, (list, tuple)):
            if len(val1) != len(val2):
                return False
            for item1, item2 in zip(val1, val2):
                if not _are_functionally_equivalent([item1], [item2]):
                    return False
        # For dictionaries
        elif isinstance(val1, dict) and isinstance(val2, dict):
            if len(val1) != len(val2):
                return False
            for key in val1:
                if key not in val2 or not _are_functionally_equivalent([val1[key]], [val2[key]]):
                    return False
        # For other objects, compare their string representation
        else:
            try:
                if repr(val1) != repr(val2):
                    return False
            except:
                # If repr fails, consider them different
                return False

    return True


def _generate_constructor_test_cases(self, cls: Type, constructor_info: Dict[str, Any],
                                     num_cases: int) -> List[ClassMethodTestCase]:
    """Generate test cases for a class constructor."""
    test_cases = []

    # Generate edge cases for constructor parameters
    param_edge_values = {}
    for param_name, param in constructor_info['parameters'].items():
        param_type = constructor_info['type_hints'].get(param_name, Any)
        param_edge_values[param_name] = ValueGenerator.get_edge_cases_for_type(param_type)

    # Generate combinations of edge values for constructor
    param_names = list(constructor_info['parameters'].keys())
    if not param_names:
        # No parameters, just create an instance with no args
        try:
            cls()  # Just test if constructor succeeds
            test_cases.append(ClassMethodTestCase(
                class_type=cls,
                constructor_inputs=[],
                method_name='__init__',
                method_inputs=[],
                expected_output=None,
                description="Constructor with no arguments"
            ))
        except Exception as e:
            test_cases.append(ClassMethodTestCase(
                class_type=cls,
                constructor_inputs=[],
                method_name='__init__',
                method_inputs=[],
                expected_output=None,
                description=f"Constructor with no arguments (raises {type(e).__name__})",
                raises=type(e)
            ))
        return test_cases

    # Track used inputs to prevent duplicates
    used_inputs = []

    # For each parameter, try its edge values
    for index, param_name in enumerate(param_names):
        for edge_value in param_edge_values[param_name]:
            inputs = []
            for inner_idx, inner_param in enumerate(param_names):
                if inner_idx == index:
                    inputs.append(edge_value)
                else:
                    # Use a "typical" value
                    param_type = constructor_info['type_hints'].get(inner_param, Any)
                    value = self._generate_value_for_type(param_type, inner_param, cls)
                    inputs.append(value)

            # Check for duplicates or functionally equivalent inputs
            is_duplicate = False
            for existing_inputs in used_inputs:
                if _are_functionally_equivalent(inputs, existing_inputs):
                    is_duplicate = True
                    break

            if is_duplicate:
                continue  # Skip duplicate or functionally equivalent input combinations

            used_inputs.append(inputs.copy())

            try:
                if not IS_WINDOWS:
                    signal.signal(signal.SIGALRM, signal.SIG_DFL)
                    signal.alarm(3)

                try:
                    cls(*inputs)  # Just test if constructor succeeds
                    test_cases.append(ClassMethodTestCase(
                        class_type=cls,
                        constructor_inputs=inputs,
                        method_name='__init__',
                        method_inputs=[],
                        expected_output=None,
                        description=f"Constructor with {param_name}={edge_value}"
                    ))
                except TimeoutException:
                    print(f"Warning: Constructor execution timed out for {cls.__name__} with {param_name}={edge_value}")
                    continue
                except Exception as e:
                    test_cases.append(ClassMethodTestCase(
                        class_type=cls,
                        constructor_inputs=inputs,
                        method_name='__init__',
                        method_inputs=[],
                        expected_output=None,
                        description=f"Constructor with {param_name}={edge_value} (raises {type(e).__name__})",
                        raises=type(e)
                    ))
                finally:
                    if not IS_WINDOWS:
                        signal.alarm(0)
            except Exception as e:
                print(f"Error generating constructor test case: {str(e)}")
                continue

    # Generate random test cases for constructor
    for _ in range(num_cases):
        inputs = []
        for param_name, param in constructor_info['parameters'].items():
            param_type = constructor_info['type_hints'].get(param_name, Any)
            # Generate valid values for parameters
            value = self._generate_value_for_type(param_type, param_name, cls)
            inputs.append(value)

        try:
            if not IS_WINDOWS:
                signal.signal(signal.SIGALRM, signal.SIG_DFL)
                signal.alarm(3)

            try:
                cls(*inputs)  # Just test if constructor succeeds
                test_cases.append(ClassMethodTestCase(
                    class_type=cls,
                    constructor_inputs=inputs,
                    method_name='__init__',
                    method_inputs=[],
                    expected_output=None,
                    description=f"Constructor with inputs: {inputs}"
                ))
            except TimeoutException:
                print(f"Warning: Constructor execution timed out for {cls.__name__} with inputs {inputs}")
                continue
            except Exception as e:
                test_cases.append(ClassMethodTestCase(
                    class_type=cls,
                    constructor_inputs=inputs,
                    method_name='__init__',
                    method_inputs=[],
                    expected_output=None,
                    description=f"Constructor with inputs: {inputs} (raises {type(e).__name__})",
                    raises=type(e)
                ))
            finally:
                if not IS_WINDOWS:
                    signal.alarm(0)
        except Exception as e:
            print(f"Error generating constructor test case: {str(e)}")
            continue

    return test_cases


def _generate_method_test_cases(self, cls: Type, method_name: str, method_info: Dict[str, Any],
                              method_type: str, num_cases: int) -> List[ClassMethodTestCase]:
    """Generate test cases for a class method."""
    test_cases = []

    # Track used inputs to prevent duplicates
    used_inputs = []

    # Create a valid instance for testing instance methods
    valid_instance = None
    constructor_inputs = []

    if method_type == 'methods':  # Instance method needs an instance
        try:
            # Try to create an instance with default constructor
            valid_instance = cls()
        except Exception as e:
            # If that fails, try to analyze constructor and create with valid inputs
            class_info = ClassAnalyzer.analyze_class(cls)
            if 'constructor' in class_info:
                constructor_info = class_info['constructor']
                constructor_inputs = []
                for param_name, param in constructor_info['parameters'].items():
                    param_type = constructor_info['type_hints'].get(param_name, Any)
                    value = self._generate_value_for_type(param_type, param_name, cls)
                    constructor_inputs.append(value)
                try:
                    valid_instance = cls(*constructor_inputs)
                except Exception as e:
                    print(f"Warning: Could not create instance of {cls.__name__} for testing: {str(e)}")
                    if method_type == 'methods':
                        # For instance methods, we need an instance
                        # But instead of returning, we'll mark this test case as one that will raise an exception
                        # during instance creation, so it can still be used for testing expected failures
                        test_cases.append(ClassMethodTestCase(
                            class_type=cls,
                            constructor_inputs=constructor_inputs,
                            method_name=method_name,
                            method_inputs=[],
                            expected_output=None,
                            description=f"Instance method {method_name} - constructor fails with {type(e).__name__}: {str(e)}",
                            raises=type(e)
                        ))
                    # Continue anyway to test class methods and static methods

    # If we couldn't create an instance but we're trying to test an instance method,
    # we can't proceed with parameter-based tests
    if method_type == 'methods' and valid_instance is None:
        return test_cases

    # Generate edge cases for method parameters
    param_edge_values = {}
    for param_name, param in method_info['parameters'].items():
        param_type = method_info['type_hints'].get(param_name, Any)
        param_edge_values[param_name] = ValueGenerator.get_edge_cases_for_type(param_type)

    # Generate combinations of edge values for method
    param_names = list(method_info['parameters'].keys())
    if not param_names:
        # No parameters, just call the method with no args
        try:
            if not IS_WINDOWS:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(3)

            try:
                if method_type == 'methods':
                    # Instance method - create a new instance for each test case to avoid state contamination
                    instance = cls(*constructor_inputs)
                    method = getattr(instance, method_name)
                    expected_output = method()
                elif method_type == 'class_methods':
                    # Class method
                    method = getattr(cls, method_name)
                    expected_output = method()
                else:
                    # Static method
                    method = getattr(cls, method_name)
                    expected_output = method()

                test_cases.append(ClassMethodTestCase(
                    class_type=cls,
                    constructor_inputs=constructor_inputs,
                    method_name=method_name,
                    method_inputs=[],
                    expected_output=expected_output,
                    description=f"{method_type[:-1].capitalize()} {method_name} with no arguments"
                ))
            except TimeoutException:
                print(f"Warning: Method execution timed out for {cls.__name__}.{method_name} with no arguments")
            except Exception as e:
                test_cases.append(ClassMethodTestCase(
                    class_type=cls,
                    constructor_inputs=constructor_inputs,
                    method_name=method_name,
                    method_inputs=[],
                    expected_output=None,
                    description=f"{method_type[:-1].capitalize()} {method_name} with no arguments (raises {type(e).__name__})",
                    raises=type(e)
                ))
            finally:
                if not IS_WINDOWS:
                    signal.alarm(0)
        except Exception as e:
            print(f"Error generating method test case: {str(e)}")

        return test_cases

    # For each parameter, try its edge values
    for idx, param_name in enumerate(param_names):
        for edge_value in param_edge_values[param_name]:
            inputs = []
            for inner_idx, inner_param in enumerate(param_names):
                if inner_idx == idx:
                    inputs.append(edge_value)
                else:
                    # Use a "typical" value for other parameters
                    param_type = method_info['type_hints'].get(inner_param, Any)
                    # Generate valid values for parameters
                    value = self._generate_value_for_type(param_type, inner_param, cls)
                    inputs.append(value)

            # Check for duplicates or functionally equivalent inputs
            is_duplicate = False
            for existing_inputs in used_inputs:
                if _are_functionally_equivalent(inputs, existing_inputs):
                    is_duplicate = True
                    break

            if is_duplicate:
                continue  # Skip duplicate or functionally equivalent input combinations

            used_inputs.append(inputs.copy())

            try:
                if not IS_WINDOWS:
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(3)

                try:
                    if method_type == 'methods':
                        # Instance method - create a new instance for each test case to avoid state contamination
                        instance = cls(*constructor_inputs)
                        method = getattr(instance, method_name)
                        expected_output = method(*inputs)
                    elif method_type == 'class_methods':
                        # Class method
                        method = getattr(cls, method_name)
                        expected_output = method(*inputs)
                    else:
                        # Static method
                        method = getattr(cls, method_name)
                        expected_output = method(*inputs)

                    test_cases.append(ClassMethodTestCase(
                        class_type=cls,
                        constructor_inputs=constructor_inputs,
                        method_name=method_name,
                        method_inputs=inputs,
                        expected_output=expected_output,
                        description=f"{method_type[:-1].capitalize()} {method_name} with {param_name}={edge_value}"
                    ))
                except TimeoutException:
                    print(f"Warning: Method execution timed out for {cls.__name__}.{method_name} with {param_name}={edge_value}")
                    continue
                except Exception as e:
                    test_cases.append(ClassMethodTestCase(
                        class_type=cls,
                        constructor_inputs=constructor_inputs,
                        method_name=method_name,
                        method_inputs=inputs,
                        expected_output=None,
                        description=f"{method_type[:-1].capitalize()} {method_name} with {param_name}={edge_value} (raises {type(e).__name__})",
                        raises=type(e)
                    ))
                finally:
                    if not IS_WINDOWS:
                        signal.alarm(0)
            except Exception as e:
                print(f"Error generating method test case: {str(e)}")
                continue

    # Generate random test cases for method
    for _ in range(num_cases):
        inputs = []
        for param_name, param in method_info['parameters'].items():
            param_type = method_info['type_hints'].get(param_name, Any)
            # Generate valid values for parameters
            value = self._generate_value_for_type(param_type, param_name, cls)
            inputs.append(value)

        # Check for duplicates or functionally equivalent inputs
        is_duplicate = False
        for existing_inputs in used_inputs:
            if _are_functionally_equivalent(inputs, existing_inputs):
                is_duplicate = True
                break

        if is_duplicate:
            continue  # Skip duplicate or functionally equivalent input combinations

        used_inputs.append(inputs.copy())

        try:
            if not IS_WINDOWS:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(3)

            try:
                if method_type == 'methods':
                    # Instance method - create a new instance for each test case to avoid state contamination
                    instance = cls(*constructor_inputs)
                    method = getattr(instance, method_name)
                    expected_output = method(*inputs)
                elif method_type == 'class_methods':
                    # Class method
                    method = getattr(cls, method_name)
                    expected_output = method(*inputs)
                else:
                    # Static method
                    method = getattr(cls, method_name)
                    expected_output = method(*inputs)

                test_cases.append(ClassMethodTestCase(
                    class_type=cls,
                    constructor_inputs=constructor_inputs,
                    method_name=method_name,
                    method_inputs=inputs,
                    expected_output=expected_output,
                    description=f"{method_type[:-1].capitalize()} {method_name} with inputs: {inputs}"
                ))
            except TimeoutException:
                print(f"Warning: Method execution timed out for {cls.__name__}.{method_name} with inputs {inputs}")
                continue
            except Exception as e:
                test_cases.append(ClassMethodTestCase(
                    class_type=cls,
                    constructor_inputs=constructor_inputs,
                    method_name=method_name,
                    method_inputs=inputs,
                    expected_output=None,
                    description=f"{method_type[:-1].capitalize()} {method_name} with inputs: {inputs} (raises {type(e).__name__})",
                    raises=type(e)
                ))
            finally:
                if not IS_WINDOWS:
                    signal.alarm(0)
        except Exception as e:
            print(f"Error generating method test case: {str(e)}")
            continue

    return test_cases


def _generate_property_getter_test_cases(self, cls: Type, prop_name: str, prop_info: Dict[str, Any],
                                         num_cases: int) -> List[ClassMethodTestCase]:
    """Generate test cases for a property getter."""
    test_cases = []

    # Create a valid instance for testing property
    valid_instance = None
    constructor_inputs = []
    try:
        # Try to create an instance with default constructor
        valid_instance = cls()
    except Exception:
        # If that fails, try to analyze constructor and create with valid inputs
        class_info = ClassAnalyzer.analyze_class(cls)
        if 'constructor' in class_info:
            constructor_info = class_info['constructor']
            constructor_inputs = []
            for param_name, param in constructor_info['parameters'].items():
                param_type = constructor_info['type_hints'].get(param_name, Any)
                # Generate valid values for parameters
                value = self._generate_value_for_type(param_type, param_name, cls)
                constructor_inputs.append(value)
            try:
                valid_instance = cls(*constructor_inputs)
            except Exception as e:
                print(f"Warning: Could not create instance of {cls.__name__} for testing property: {str(e)}")
                return []  # Can't test properties without an instance

    # Test the property getter
    try:
        if not IS_WINDOWS:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(3)

        try:
            # Get the property value
            expected_output = getattr(valid_instance, prop_name)

            test_cases.append(ClassMethodTestCase(
                class_type=cls,
                constructor_inputs=constructor_inputs,
                method_name=f"get_{prop_name}",
                method_inputs=[],
                expected_output=expected_output,
                description=f"Property getter for {prop_name}",
                is_property_getter=True
            ))
        except TimeoutException:
            print(f"Warning: Property getter execution timed out for {cls.__name__}.{prop_name}")
        except Exception as e:
            test_cases.append(ClassMethodTestCase(
                class_type=cls,
                constructor_inputs=constructor_inputs,
                method_name=f"get_{prop_name}",
                method_inputs=[],
                expected_output=None,
                description=f"Property getter for {prop_name} (raises {type(e).__name__})",
                raises=type(e),
                is_property_getter=True
            ))
        finally:
            if not IS_WINDOWS:
                signal.alarm(0)
    except Exception as e:
        print(f"Error generating property getter test case: {str(e)}")

    return test_cases


def _generate_property_setter_test_cases(self, cls: Type, prop_name: str, prop_info: Dict[str, Any],
                                         num_cases: int) -> List[ClassMethodTestCase]:
    """Generate test cases for a property setter."""
    test_cases = []

    # Track used inputs to prevent duplicates
    used_inputs = []

    # Create a valid instance for testing property
    valid_instance = None
    constructor_inputs = []
    try:
        # Try to create an instance with default constructor
        valid_instance = cls()
    except Exception:
        # If that fails, try to analyze constructor and create with valid inputs
        class_info = ClassAnalyzer.analyze_class(cls)
        if 'constructor' in class_info:
            constructor_info = class_info['constructor']
            constructor_inputs = []
            for param_name, param in constructor_info['parameters'].items():
                param_type = constructor_info['type_hints'].get(param_name, Any)
                # Generate valid values for parameters
                value = self._generate_value_for_type(param_type, param_name, cls)
                constructor_inputs.append(value)
            try:
                valid_instance = cls(*constructor_inputs)
            except Exception as e:
                print(f"Warning: Could not create instance of {cls.__name__} for testing property: {str(e)}")
                return []  # Can't test properties without an instance

    # Determine the property type
    prop_type = prop_info['type_hints'].get('return', Any)

    # Generate edge cases for property setter
    edge_values = ValueGenerator.get_edge_cases_for_type(prop_type)

    # Test the property setter with edge values
    for value in edge_values:
        # Check for duplicates or functionally equivalent inputs
        is_duplicate = False
        for existing_input in used_inputs:
            if _are_functionally_equivalent([value], [existing_input]):
                is_duplicate = True
                break

        if is_duplicate:
            continue  # Skip duplicate or functionally equivalent input

        used_inputs.append(value)

        try:
            if not IS_WINDOWS:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(3)

            try:
                # Create a new instance for each test to avoid state contamination
                instance = cls(*constructor_inputs)

                # Set the property value
                setattr(instance, prop_name, value)

                # Verify the property was set correctly
                expected_output = getattr(instance, prop_name)

                test_cases.append(ClassMethodTestCase(
                    class_type=cls,
                    constructor_inputs=constructor_inputs,
                    method_name=f"set_{prop_name}",
                    method_inputs=[value],
                    expected_output=expected_output,
                    description=f"Property setter for {prop_name} with value={value}"
                ))
            except TimeoutException:
                print(f"Warning: Property setter execution timed out for {cls.__name__}.{prop_name} with value={value}")
                continue
            except Exception as e:
                test_cases.append(ClassMethodTestCase(
                    class_type=cls,
                    constructor_inputs=constructor_inputs,
                    method_name=f"set_{prop_name}",
                    method_inputs=[value],
                    expected_output=None,
                    description=f"Property setter for {prop_name} with value={value} (raises {type(e).__name__})",
                    raises=type(e)
                ))
            finally:
                if not IS_WINDOWS:
                    signal.alarm(0)
        except Exception as e:
            print(f"Error generating property setter test case: {str(e)}")
            continue

    # Generate random test cases for property setter
    for _ in range(num_cases):
        # Generate valid values for property
        value = self._generate_value_for_type(prop_type, prop_name, cls)

        # Check for duplicates or functionally equivalent inputs
        is_duplicate = False
        for existing_input in used_inputs:
            if _are_functionally_equivalent([value], [existing_input]):
                is_duplicate = True
                break

        if is_duplicate:
            continue  # Skip duplicate or functionally equivalent input

        used_inputs.append(value)

        try:
            if not IS_WINDOWS:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(3)

            try:
                # Create a new instance for each test to avoid state contamination
                instance = cls(*constructor_inputs)

                # Set the property value
                setattr(instance, prop_name, value)

                # Verify the property was set correctly
                expected_output = getattr(instance, prop_name)

                test_cases.append(ClassMethodTestCase(
                    class_type=cls,
                    constructor_inputs=constructor_inputs,
                    method_name=f"set_{prop_name}",
                    method_inputs=[value],
                    expected_output=expected_output,
                    description=f"Property setter for {prop_name} with value={value}"
                ))
            except TimeoutException:
                print(f"Warning: Property setter execution timed out for {cls.__name__}.{prop_name} with value={value}")
                continue
            except Exception as e:
                test_cases.append(ClassMethodTestCase(
                    class_type=cls,
                    constructor_inputs=constructor_inputs,
                    method_name=f"set_{prop_name}",
                    method_inputs=[value],
                    expected_output=None,
                    description=f"Property setter for {prop_name} with value={value} (raises {type(e).__name__})",
                    raises=type(e)
                ))
            finally:
                if not IS_WINDOWS:
                    signal.alarm(0)
        except Exception as e:
            print(f"Error generating property setter test case: {str(e)}")
            continue

    return test_cases
