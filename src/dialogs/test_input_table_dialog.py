import tkinter as tk
from tkinter import ttk, messagebox
import inspect
from typing import get_type_hints

from src.test_case_generator.models import TestCase, ClassMethodTestCase
from src.utils import set_window_size_and_position


class TestInputTableDialog(tk.Toplevel):
    """
    Dialog for inputting test parameters in a table-like interface.
    Shows all functions and methods in a single view.
    """
    def __init__(self, parent, functions, classes):
        super().__init__(parent)
        self.title("Test Input Table")
        set_window_size_and_position(self, 900, 700)
        self.resizable(True, True)

        self.parent = parent
        self.functions = functions
        self.classes = classes

        # Store test cases
        self.user_test_cases = {}
        self.user_class_test_cases = {}

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create tabs for functions and classes
        self.create_functions_tab()
        self.create_classes_tab()

        # Create buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(button_frame, text="OK", command=self.on_ok).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=5)

    def create_functions_tab(self):
        """Create tab for functions."""
        if not self.functions:
            return

        # Create frame for functions tab
        functions_frame = ttk.Frame(self.notebook)
        self.notebook.add(functions_frame, text="Functions")

        # Create scrollable frame
        canvas = tk.Canvas(functions_frame)
        scrollbar = ttk.Scrollbar(functions_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Add function entries
        row = 0
        for func_name, func in self.functions.items():
            # Create frame for function
            func_frame = ttk.LabelFrame(scrollable_frame, text=f"Function: {func_name}")
            func_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=5)

            # Get function signature
            signature = inspect.signature(func)

            # Create entries for parameters
            param_entries = {}
            param_row = 0

            # Create header
            ttk.Label(func_frame, text="Parameter").grid(row=param_row, column=0, padx=5, pady=2, sticky="w")
            ttk.Label(func_frame, text="Type").grid(row=param_row, column=1, padx=5, pady=2, sticky="w")
            ttk.Label(func_frame, text="Value").grid(row=param_row, column=2, padx=5, pady=2, sticky="w")
            param_row += 1

            # Add parameter entries
            for param_name, param in signature.parameters.items():
                ttk.Label(func_frame, text=f"{param_name}:").grid(row=param_row, column=0, padx=5, pady=2, sticky="w")

                # Add parameter type hint if available
                param_type = "Any"
                try:
                    type_hints = get_type_hints(func)
                    if param_name in type_hints:
                        # Handle complex types like List[int], Union[str, int], etc.
                        param_type_obj = type_hints[param_name]
                        if hasattr(param_type_obj, "__origin__"):
                            # For generic types like List[int], Dict[str, int], etc.
                            origin = param_type_obj.__origin__.__name__
                            args = ", ".join(arg.__name__ if hasattr(arg, "__name__") else str(arg) for arg in param_type_obj.__args__)
                            param_type = f"{origin}[{args}]"
                        else:
                            # For simple types like int, str, etc.
                            param_type = param_type_obj.__name__
                except (TypeError, AttributeError):
                    pass

                ttk.Label(func_frame, text=param_type).grid(row=param_row, column=1, padx=5, pady=2, sticky="w")

                entry = ttk.Entry(func_frame, width=40)
                entry.grid(row=param_row, column=2, padx=5, pady=2, sticky="w")
                param_entries[param_name] = entry

                param_row += 1

            # Add expected output entry
            ttk.Label(func_frame, text="Expected Output:").grid(row=param_row, column=0, padx=5, pady=2, sticky="w")
            expected_output_entry = ttk.Entry(func_frame, width=40)
            expected_output_entry.grid(row=param_row, column=2, padx=5, pady=2, sticky="w")
            param_row += 1

            # Add exception dropdown
            ttk.Label(func_frame, text="Expected Exception:").grid(row=param_row, column=0, padx=5, pady=2, sticky="w")
            exception_var = tk.StringVar(value="None")
            exception_options = ["None", "ValueError", "TypeError", "IndexError", "KeyError", "ZeroDivisionError", "AttributeError"]
            exception_dropdown = ttk.Combobox(func_frame, textvariable=exception_var, values=exception_options)
            exception_dropdown.grid(row=param_row, column=2, padx=5, pady=2, sticky="w")

            # Store entries for later retrieval
            if func_name not in self.user_test_cases:
                self.user_test_cases[func_name] = []

            self.user_test_cases[func_name].append({
                "param_entries": param_entries,
                "expected_output_entry": expected_output_entry,
                "exception_var": exception_var,
                "func": func
            })

            row += 1

    def create_classes_tab(self):
        """Create tab for classes."""
        if not self.classes:
            return

        # Create frame for classes tab
        classes_frame = ttk.Frame(self.notebook)
        self.notebook.add(classes_frame, text="Classes")

        # Create scrollable frame
        canvas = tk.Canvas(classes_frame)
        scrollbar = ttk.Scrollbar(classes_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Add class entries
        row = 0
        for cls_name, cls in self.classes.items():
            # Create frame for class
            cls_frame = ttk.LabelFrame(scrollable_frame, text=f"Class: {cls_name}")
            cls_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=5)

            # Initialize class test cases
            if cls_name not in self.user_class_test_cases:
                self.user_class_test_cases[cls_name] = {}

            # Get all methods of the class
            method_row = 0
            for method_name, method in inspect.getmembers(cls, inspect.isfunction):
                # Skip private methods
                if method_name.startswith('_') and method_name != '__init__':
                    continue

                # Create frame for method
                method_frame = ttk.LabelFrame(cls_frame, text=f"Method: {method_name}")
                method_frame.grid(row=method_row, column=0, sticky="ew", padx=10, pady=5)

                # Get method signature
                signature = inspect.signature(method)

                # Create entries for parameters
                param_entries = {}
                param_row = 0

                # Create header
                ttk.Label(method_frame, text="Parameter").grid(row=param_row, column=0, padx=5, pady=2, sticky="w")
                ttk.Label(method_frame, text="Type").grid(row=param_row, column=1, padx=5, pady=2, sticky="w")
                ttk.Label(method_frame, text="Value").grid(row=param_row, column=2, padx=5, pady=2, sticky="w")
                param_row += 1

                # Add parameter entries
                for param_name, param in signature.parameters.items():
                    # Skip 'self' parameter
                    if param_name == 'self':
                        continue

                    ttk.Label(method_frame, text=f"{param_name}:").grid(row=param_row, column=0, padx=5, pady=2, sticky="w")

                    # Add parameter type hint if available
                    param_type = "Any"
                    try:
                        type_hints = get_type_hints(method)
                        if param_name in type_hints:
                            # Handle complex types like List[int], Union[str, int], etc.
                            param_type_obj = type_hints[param_name]
                            if hasattr(param_type_obj, "__origin__"):
                                # For generic types like List[int], Dict[str, int], etc.
                                origin = param_type_obj.__origin__.__name__
                                args = ", ".join(arg.__name__ if hasattr(arg, "__name__") else str(arg) for arg in param_type_obj.__args__)
                                param_type = f"{origin}[{args}]"
                            else:
                                # For simple types like int, str, etc.
                                param_type = param_type_obj.__name__
                    except (TypeError, AttributeError):
                        pass

                    ttk.Label(method_frame, text=param_type).grid(row=param_row, column=1, padx=5, pady=2, sticky="w")

                    entry = ttk.Entry(method_frame, width=40)
                    entry.grid(row=param_row, column=2, padx=5, pady=2, sticky="w")
                    param_entries[param_name] = entry

                    param_row += 1

                # Add expected output entry
                ttk.Label(method_frame, text="Expected Output:").grid(row=param_row, column=0, padx=5, pady=2, sticky="w")
                expected_output_entry = ttk.Entry(method_frame, width=40)
                expected_output_entry.grid(row=param_row, column=2, padx=5, pady=2, sticky="w")
                param_row += 1

                # Add exception dropdown
                ttk.Label(method_frame, text="Expected Exception:").grid(row=param_row, column=0, padx=5, pady=2, sticky="w")
                exception_var = tk.StringVar(value="None")
                exception_options = ["None", "ValueError", "TypeError", "IndexError", "KeyError", "ZeroDivisionError", "AttributeError"]
                exception_dropdown = ttk.Combobox(method_frame, textvariable=exception_var, values=exception_options)
                exception_dropdown.grid(row=param_row, column=2, padx=5, pady=2, sticky="w")

                # Store entries for later retrieval
                if method_name not in self.user_class_test_cases[cls_name]:
                    self.user_class_test_cases[cls_name][method_name] = []

                self.user_class_test_cases[cls_name][method_name].append({
                    "param_entries": param_entries,
                    "expected_output_entry": expected_output_entry,
                    "exception_var": exception_var,
                    "method": method,
                    "cls": cls
                })

                method_row += 1

            row += 1

    def on_ok(self):
        """Handle OK button click."""
        try:
            # Process function test cases
            for func_name, test_cases in self.user_test_cases.items():
                for i, test_case_data in enumerate(test_cases):
                    param_entries = test_case_data["param_entries"]
                    expected_output_entry = test_case_data["expected_output_entry"]
                    exception_var = test_case_data["exception_var"]
                    func = test_case_data["func"]

                    # Get parameter values
                    param_values = {}
                    # Get type hints for the function
                    try:
                        type_hints = get_type_hints(func)
                    except (TypeError, AttributeError):
                        type_hints = {}

                    for param_name, entry in param_entries.items():
                        param_text = entry.get().strip()
                        if param_text:
                            try:
                                # Try to evaluate as Python expression
                                param_value = eval(param_text)

                                # Check if parameter is expected to be a string
                                if param_name in type_hints and type_hints[param_name] == str:
                                    # Convert to string if it's not already a string
                                    if not isinstance(param_value, str):
                                        param_value = str(param_value)

                                param_values[param_name] = param_value
                            except (SyntaxError, NameError):
                                # If not a valid expression, use as string
                                param_values[param_name] = param_text
                        else:
                            param_values[param_name] = None

                    # Get expected output
                    expected_output_text = expected_output_entry.get().strip()
                    if expected_output_text:
                        try:
                            expected_output = eval(expected_output_text)

                            # Check if the function's return type is string
                            if 'return' in type_hints and type_hints['return'] == str:
                                # Convert expected output to string if it's not already
                                if not isinstance(expected_output, str):
                                    expected_output = str(expected_output)
                        except (SyntaxError, NameError):
                            expected_output = expected_output_text
                    else:
                        expected_output = None

                    # Get exception
                    exception_name = exception_var.get()
                    exception_class = None
                    if exception_name != "None":
                        exception_class = eval(exception_name)

                    # Create TestCase
                    test_case = TestCase(
                        inputs=list(param_values.values()),
                        expected_output=expected_output,
                        description=f"User-defined test for {func_name}",
                        raises=exception_class
                    )

                    # Replace the test case data with the actual TestCase object
                    test_cases[i] = test_case

            # Process class method test cases
            for cls_name, methods in self.user_class_test_cases.items():
                for method_name, test_cases in methods.items():
                    for i, test_case_data in enumerate(test_cases):
                        param_entries = test_case_data["param_entries"]
                        expected_output_entry = test_case_data["expected_output_entry"]
                        exception_var = test_case_data["exception_var"]
                        method = test_case_data["method"]
                        cls = test_case_data["cls"]

                        # Get parameter values
                        param_values = {}
                        # Get type hints for the method
                        try:
                            type_hints = get_type_hints(method)
                        except (TypeError, AttributeError):
                            type_hints = {}

                        for param_name, entry in param_entries.items():
                            param_text = entry.get().strip()
                            if param_text:
                                try:
                                    # Try to evaluate as Python expression
                                    param_value = eval(param_text)

                                    # Check if parameter is expected to be a string
                                    if param_name in type_hints and type_hints[param_name] == str:
                                        # Convert to string if it's not already a string
                                        if not isinstance(param_value, str):
                                            param_value = str(param_value)

                                    param_values[param_name] = param_value
                                except (SyntaxError, NameError):
                                    # If not a valid expression, use as string
                                    param_values[param_name] = param_text
                            else:
                                param_values[param_name] = None

                        # Get expected output
                        expected_output_text = expected_output_entry.get().strip()
                        if expected_output_text:
                            try:
                                expected_output = eval(expected_output_text)

                                # Check if the method's return type is string
                                if 'return' in type_hints and type_hints['return'] == str:
                                    # Convert expected output to string if it's not already
                                    if not isinstance(expected_output, str):
                                        expected_output = str(expected_output)
                            except (SyntaxError, NameError):
                                expected_output = expected_output_text
                        else:
                            expected_output = None

                        # Get exception
                        exception_name = exception_var.get()
                        exception_class = None
                        if exception_name != "None":
                            exception_class = eval(exception_name)

                        # Create ClassMethodTestCase
                        # For simplicity, we'll use empty constructor inputs
                        constructor_inputs = []

                        test_case = ClassMethodTestCase(
                            class_type=cls,
                            constructor_inputs=constructor_inputs,
                            method_name=method_name,
                            method_inputs=list(param_values.values()),
                            expected_output=expected_output,
                            description=f"User-defined test for {cls.__name__}.{method_name}",
                            raises=exception_class
                        )

                        # Replace the test case data with the actual ClassMethodTestCase object
                        test_cases[i] = test_case

            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Error creating test cases: {str(e)}")
