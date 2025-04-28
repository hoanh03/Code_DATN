import csv
import importlib.util
import inspect
import os
import sys
import tkinter as tk
from typing import Dict, List, Any, Tuple, Callable

from src.test_generator_app import TestGeneratorApp


def load_module_from_file(file_path: str) -> Any:
    """
    Load a Python module from a file path.

    Args:
        file_path: Path to the Python file

    Returns:
        The loaded module
    """
    module_name = os.path.basename(file_path).replace('.py', '')
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {file_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def get_functions_from_module(module: Any) -> Dict[str, Callable]:
    """
    Extract all functions from a module using reflection.

    Args:
        module: The module to extract functions from

    Returns:
        Dictionary mapping function names to function objects
    """
    functions = {}
    for name, obj in inspect.getmembers(module, inspect.isfunction):
        # Only include functions defined in this module (not imported)
        if obj.__module__ == module.__name__:
            functions[name] = obj
    return functions


def get_function_info(func: Callable) -> Dict[str, Any]:
    """
    Get detailed information about a function using reflection.

    Args:
        func: The function to analyze

    Returns:
        Dictionary with function information
    """
    sig = inspect.signature(func)

    # Get parameter information
    params = {}
    for name, param in sig.parameters.items():
        param_info = {
            'name': name,
            'annotation': param.annotation.__name__ if param.annotation != inspect.Parameter.empty else 'Any',
            'default': param.default if param.default != inspect.Parameter.empty else None,
            'has_default': param.default != inspect.Parameter.empty
        }
        params[name] = param_info

    # Get return type
    return_type = sig.return_annotation.__name__ if sig.return_annotation != inspect.Signature.empty else 'Any'

    # Get docstring
    docstring = inspect.getdoc(func) or ""

    return {
        'name': func.__name__,
        'parameters': params,
        'return_type': return_type,
        'docstring': docstring
    }


def parse_csv_test_cases(csv_file: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Parse test cases from a CSV file.

    Expected CSV format:
    function_name,param1,param2,...,expected_result

    Args:
        csv_file: Path to the CSV file

    Returns:
        Dictionary mapping function names to lists of test cases
    """
    test_cases = {}

    with open(csv_file, 'r', newline='') as f:
        reader = csv.reader(f)
        header = next(reader)  # Get header row

        if len(header) < 2:
            raise ValueError("CSV file must have at least function_name and expected_result columns")

        for row in reader:
            if not row or len(row) < 2:
                continue  # Skip empty rows

            function_name = row[0]
            expected_result = row[-1]

            # Parameters are all columns between function name and expected result
            params = row[1:-1]

            if function_name not in test_cases:
                test_cases[function_name] = []

            test_cases[function_name].append({
                'params': params,
                'expected': expected_result
            })

    return test_cases


def convert_param_value(value: str, param_type: str) -> Any:
    """
    Convert a string parameter value to the appropriate type.

    Args:
        value: The string value from CSV
        param_type: The expected parameter type

    Returns:
        Converted value
    """
    if param_type == 'int':
        return int(value)
    elif param_type == 'float':
        return float(value)
    elif param_type == 'bool':
        return value.lower() in ('true', 'yes', '1', 't', 'y')
    # For other types, return as string
    return value


def run_tests(functions: Dict[str, Callable], function_info: Dict[str, Dict[str, Any]], 
              test_cases: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Run tests for functions using the provided test cases.

    Args:
        functions: Dictionary of function objects
        function_info: Dictionary of function information
        test_cases: Dictionary of test cases

    Returns:
        Dictionary of test results
    """
    results = {}

    for func_name, cases in test_cases.items():
        if func_name not in functions:
            print(f"Warning: Function '{func_name}' not found in module")
            continue

        func = functions[func_name]
        info = function_info[func_name]
        results[func_name] = []

        for case in cases:
            # Convert parameters to appropriate types
            param_values = []
            param_info = list(info['parameters'].values())

            # Make sure we have the right number of parameters
            if len(case['params']) != len(param_info):
                print(f"Warning: Test case for {func_name} has {len(case['params'])} parameters, "
                      f"but function expects {len(param_info)}")
                continue

            for i, param_value in enumerate(case['params']):
                param_type = param_info[i]['annotation']
                try:
                    converted_value = convert_param_value(param_value, param_type)
                    param_values.append(converted_value)
                except ValueError:
                    print(f"Warning: Could not convert parameter '{param_value}' to {param_type}")
                    break

            # If we couldn't convert all parameters, skip this test case
            if len(param_values) != len(param_info):
                continue

            # Run the function and compare result
            try:
                actual_result = func(*param_values)
                expected_result = convert_param_value(case['expected'], info['return_type'])

                success = actual_result == expected_result

                results[func_name].append({
                    'params': case['params'],
                    'expected': expected_result,
                    'actual': actual_result,
                    'success': success
                })

            except Exception as e:
                results[func_name].append({
                    'params': case['params'],
                    'expected': case['expected'],
                    'error': str(e),
                    'success': False
                })

    return results


def format_results(results: Dict[str, List[Dict[str, Any]]]) -> str:
    """
    Format test results as a string.

    Args:
        results: Dictionary of test results

    Returns:
        Formatted results as a string
    """
    total_tests = 0
    passed_tests = 0
    output = ["===== TEST RESULTS ====="]

    for func_name, test_results in results.items():
        output.append(f"\nFunction: {func_name}")
        output.append("-" * (len(func_name) + 10))

        for i, result in enumerate(test_results, 1):
            total_tests += 1

            output.append(f"Test #{i}:")
            output.append(f"  Parameters: {', '.join(result['params'])}")
            output.append(f"  Expected: {result['expected']}")

            if 'error' in result:
                output.append(f"  Error: {result['error']}")
                output.append(f"  Result: FAILED")
            else:
                output.append(f"  Actual: {result['actual']}")
                output.append(f"  Result: {'PASSED' if result['success'] else 'FAILED'}")

                if result['success']:
                    passed_tests += 1

            output.append("")

    output.append("===== SUMMARY =====")
    output.append(f"Total tests: {total_tests}")
    output.append(f"Passed: {passed_tests}")
    output.append(f"Failed: {total_tests - passed_tests}")
    if total_tests > 0:
        output.append(f"Success rate: {passed_tests / total_tests * 100:.2f}%")
    else:
        output.append("Success rate: N/A")

    return "\n".join(output)


def format_results_with_color(results: Dict[str, List[Dict[str, Any]]]) -> List[Tuple[str, str]]:
    """
    Format test results with color tags.

    Args:
        results: Dictionary of test results

    Returns:
        List of (text, tag) tuples where tag is either "success", "failure", or ""
    """
    total_tests = 0
    passed_tests = 0
    output = [("===== TEST RESULTS =====\n", "")]

    # Header

    for func_name, test_results in results.items():
        output.append((f"Function: {func_name}\n", ""))
        output.append((f"{'-' * (len(func_name) + 10)}\n", ""))

        for i, result in enumerate(test_results, 1):
            total_tests += 1

            output.append((f"Test #{i}:\n", ""))
            output.append((f"  Parameters: {', '.join(result['params'])}\n", ""))
            output.append((f"  Expected: {result['expected']}\n", ""))

            if 'error' in result:
                output.append((f"  Error: {result['error']}\n", ""))
                output.append((f"  Result: FAILED\n", "failure"))
            else:
                output.append((f"  Actual: {result['actual']}\n", ""))
                if result['success']:
                    output.append((f"  Result: PASSED\n", "success"))
                    passed_tests += 1
                else:
                    output.append((f"  Result: FAILED\n", "failure"))

            output.append(("\n", ""))

    # Summary
    output.append(("===== SUMMARY =====\n", ""))
    output.append((f"Total tests: {total_tests}\n", ""))
    output.append((f"Passed: {passed_tests}\n", "success" if passed_tests > 0 else ""))
    output.append((f"Failed: {total_tests - passed_tests}\n", "failure" if (total_tests - passed_tests) > 0 else ""))

    if total_tests > 0:
        success_rate = passed_tests / total_tests * 100
        output.append((f"Success rate: {success_rate:.2f}%\n", "success" if success_rate >= 50 else "failure"))
    else:
        output.append(("Success rate: N/A\n", ""))

    return output


def print_results(results: Dict[str, List[Dict[str, Any]]]) -> None:
    """
    Print test results in a readable format.

    Args:
        results: Dictionary of test results
    """
    print(format_results(results))


def main():
    """
    Main function to run the test generator GUI.
    """
    root = tk.Tk()
    TestGeneratorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
