import tkinter as tk
from tkinter import ttk, messagebox
import inspect
from typing import get_type_hints

from src.test_case_generator.models import TestCase, ClassMethodTestCase
from src.utils import set_window_size_and_position


class TestInputDialog(tk.Toplevel):
    """
    Dialog for inputting test parameters, expected outputs, and exception types.
    """
    def __init__(self, parent, function_name, function_obj, is_method=False, class_obj=None, method_name=None):
        super().__init__(parent)
        self.title(f"Test Input for {'Method' if is_method else 'Function'}: {function_name}")
        set_window_size_and_position(self, 600, 500)
        self.resizable(True, True)

        self.parent = parent
        self.function_name = function_name
        self.function_obj = function_obj
        self.is_method = is_method
        self.class_obj = class_obj
        self.method_name = method_name

        # Get function signature
        self.signature = inspect.signature(function_obj)
        self.param_entries = {}
        self.expected_output_entry = None
        self.exception_var = tk.StringVar(value="None")
        self.exception_options = ["None", "ValueError", "TypeError", "IndexError", "KeyError", "ZeroDivisionError", "AttributeError"]

        self.result = None  # Will store the result when OK is clicked

        self.create_widgets()

    def create_widgets(self):
        """Create the dialog widgets."""
        # Main frame
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Function/Method info
        if self.is_method:
            info_text = f"Class: {self.class_obj.__name__}, Method: {self.method_name}"
        else:
            info_text = f"Function: {self.function_name}"

        ttk.Label(main_frame, text=info_text, font=("", 12, "bold")).pack(pady=(0, 10))

        # Parameters frame
        params_frame = ttk.LabelFrame(main_frame, text="Parameters", padding="10")
        params_frame.pack(fill=tk.X, pady=5)

        # Add parameter entries
        row = 0
        for param_name, param in self.signature.parameters.items():
            ttk.Label(params_frame, text=f"{param_name}:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
            entry = ttk.Entry(params_frame, width=40)
            entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
            self.param_entries[param_name] = entry

            # Add parameter type hint if available
            param_type = "Any"
            try:
                type_hints = get_type_hints(self.function_obj)
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

            ttk.Label(params_frame, text=f"Type: {param_type}").grid(row=row, column=2, sticky=tk.W, padx=5, pady=2)
            row += 1

        # Expected output frame
        output_frame = ttk.LabelFrame(main_frame, text="Expected Output", padding="10")
        output_frame.pack(fill=tk.X, pady=5)

        ttk.Label(output_frame, text="Expected Output:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.expected_output_entry = ttk.Entry(output_frame, width=40)
        self.expected_output_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)

        # Exception frame
        exception_frame = ttk.LabelFrame(main_frame, text="Exception", padding="10")
        exception_frame.pack(fill=tk.X, pady=5)

        ttk.Label(exception_frame, text="Expected Exception:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        exception_dropdown = ttk.Combobox(exception_frame, textvariable=self.exception_var, values=self.exception_options)
        exception_dropdown.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(button_frame, text="OK", command=self.on_ok).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=5)

    def on_ok(self):
        """Handle OK button click."""
        try:
            # Get parameter values
            param_values = {}
            for param_name, entry in self.param_entries.items():
                param_text = entry.get().strip()
                if param_text:
                    try:
                        # Try to evaluate as Python expression
                        param_values[param_name] = eval(param_text)
                    except (SyntaxError, NameError):
                        # If not a valid expression, use as string
                        param_values[param_name] = param_text
                else:
                    param_values[param_name] = None

            # Get expected output
            expected_output_text = self.expected_output_entry.get().strip()
            if expected_output_text:
                try:
                    expected_output = eval(expected_output_text)
                except (SyntaxError, NameError):
                    expected_output = expected_output_text
            else:
                expected_output = None

            # Get exception
            exception_name = self.exception_var.get()
            exception_class = None
            if exception_name != "None":
                exception_class = eval(exception_name)

            # Create result
            if self.is_method:
                # For methods, we need constructor inputs too
                # For simplicity, we'll use empty constructor inputs
                constructor_inputs = []

                self.result = ClassMethodTestCase(
                    class_type=self.class_obj,
                    constructor_inputs=constructor_inputs,
                    method_name=self.method_name,
                    method_inputs=list(param_values.values()),
                    expected_output=expected_output,
                    description=f"User-defined test for {self.class_obj.__name__}.{self.method_name}",
                    raises=exception_class
                )
            else:
                self.result = TestCase(
                    inputs=list(param_values.values()),
                    expected_output=expected_output,
                    description=f"User-defined test for {self.function_name}",
                    raises=exception_class
                )

            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Error creating test case: {str(e)}")
