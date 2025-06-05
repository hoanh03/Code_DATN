import os
import csv
import tkinter as tk
from tkinter import ttk, messagebox
import inspect
from typing import get_type_hints
from src.utils import set_window_size_and_position


class CSVMappingDialog(tk.Toplevel):
    """
    Dialog for mapping CSV columns to test parameters.
    """
    def __init__(self, parent, csv_file, functions, classes):
        super().__init__(parent)
        self.title(f"Map CSV Columns - {os.path.basename(csv_file)}")
        set_window_size_and_position(self, 900, 700)
        self.resizable(True, True)

        self.parent = parent
        # Normalize the CSV file path to ensure it works on all platforms
        self.csv_file = os.path.normpath(csv_file)
        self.functions = functions
        self.classes = classes

        # Read CSV headers and first few rows for preview
        self.headers, self.preview_data = self.read_csv_preview()

        # Store mappings
        self.function_mappings = {}
        self.class_method_mappings = {}

        # Create widgets
        self.create_widgets()

    def read_csv_preview(self, preview_rows=5):
        """Read CSV headers and first few rows for preview."""
        try:
            with open(self.csv_file, 'r', newline='') as f:
                reader = csv.reader(f)
                headers = next(reader)  # First row as headers
                preview_data = []
                for i, row in enumerate(reader):
                    if i >= preview_rows:
                        break
                    preview_data.append(row)
            return headers, preview_data
        except Exception as e:
            messagebox.showerror("Error", f"Error reading CSV file: {str(e)}")
            return [], []

    def create_widgets(self):
        """Create the dialog widgets."""
        # Main frame
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # CSV preview frame
        preview_frame = ttk.LabelFrame(main_frame, text="CSV Preview", padding="10")
        preview_frame.pack(fill=tk.X, pady=10)

        # Create a treeview for CSV preview
        preview_tree = ttk.Treeview(preview_frame)
        preview_tree.pack(fill=tk.X, expand=True)

        # Configure columns for the treeview
        preview_tree["columns"] = self.headers
        preview_tree["show"] = "headings"  # Hide the first empty column

        # Set column headings
        for header in self.headers:
            preview_tree.heading(header, text=header)
            preview_tree.column(header, width=100)

        # Add preview data
        for i, row in enumerate(self.preview_data):
            preview_tree.insert("", "end", values=row)

        # Create notebook for functions and classes
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=10)

        # Functions tab
        if self.functions:
            functions_frame = ttk.Frame(notebook)
            notebook.add(functions_frame, text="Functions")
            self.create_functions_tab(functions_frame)

        # Classes tab
        if self.classes:
            classes_frame = ttk.Frame(notebook)
            notebook.add(classes_frame, text="Classes")
            self.create_classes_tab(classes_frame)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(button_frame, text="OK", command=self.on_ok).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=5)

    def create_functions_tab(self, functions_frame):
        """Create tab for mapping CSV columns to function parameters."""

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

        # Add function mappings
        row = 0
        for func_name, func in self.functions.items():
            # Create frame for function
            func_frame = ttk.LabelFrame(scrollable_frame, text=f"Function: {func_name}")
            func_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=5)

            # Get function signature
            signature = inspect.signature(func)

            # Initialize mapping for this function
            self.function_mappings[func_name] = {
                "param_mappings": {},
                "expected_output_column": tk.StringVar(value=""),
                "exception_column": tk.StringVar(value="")
            }

            # Create header
            ttk.Label(func_frame, text="Parameter").grid(row=0, column=0, padx=5, pady=2, sticky="w")
            ttk.Label(func_frame, text="Type").grid(row=0, column=1, padx=5, pady=2, sticky="w")
            ttk.Label(func_frame, text="CSV Column").grid(row=0, column=2, padx=5, pady=2, sticky="w")

            # Add parameter mappings
            param_row = 1
            for param_name, param in signature.parameters.items():
                ttk.Label(func_frame, text=f"{param_name}:").grid(row=param_row, column=0, padx=5, pady=2, sticky="w")

                # Add parameter type hint if available
                param_type = "Any"
                try:
                    type_hints = get_type_hints(func)
                    if param_name in type_hints:
                        param_type_obj = type_hints[param_name]
                        if hasattr(param_type_obj, "__origin__"):
                            origin = param_type_obj.__origin__.__name__
                            args = ", ".join(arg.__name__ if hasattr(arg, "__name__") else str(arg) for arg in param_type_obj.__args__)
                            param_type = f"{origin}[{args}]"
                        else:
                            param_type = param_type_obj.__name__
                except (TypeError, AttributeError):
                    pass

                ttk.Label(func_frame, text=param_type).grid(row=param_row, column=1, padx=5, pady=2, sticky="w")

                # Add dropdown for CSV column mapping
                column_var = tk.StringVar(value="")

                # Auto-select matching column if available
                for header in self.headers:
                    if header.lower() == param_name.lower():
                        column_var.set(header)
                        break

                column_dropdown = ttk.Combobox(func_frame, textvariable=column_var, values=[""] + self.headers)
                column_dropdown.grid(row=param_row, column=2, padx=5, pady=2, sticky="w")

                # Store mapping
                self.function_mappings[func_name]["param_mappings"][param_name] = column_var

                param_row += 1

            # Add expected output mapping
            ttk.Label(func_frame, text="Expected Output:").grid(row=param_row, column=0, padx=5, pady=2, sticky="w")
            output_var = self.function_mappings[func_name]["expected_output_column"]

            # Auto-select matching output column if available
            # Try different patterns for expected output column names
            output_patterns = [
                f"{func_name.lower()}_result",  # e.g., add_result
                f"{func_name.lower()}_{param_name.lower()}" if len(signature.parameters) == 1 else None,  # e.g., absolute_a
            ]

            for pattern in output_patterns:
                if pattern is None:
                    continue

                for header in self.headers:
                    if header.lower() == pattern:
                        output_var.set(header)
                        break

                if output_var.get():  # If we found a match, stop looking
                    break

            output_dropdown = ttk.Combobox(func_frame, textvariable=output_var, values=[""] + self.headers)
            output_dropdown.grid(row=param_row, column=2, padx=5, pady=2, sticky="w")
            param_row += 1

            # Add exception mapping
            ttk.Label(func_frame, text="Exception:").grid(row=param_row, column=0, padx=5, pady=2, sticky="w")
            exception_var = self.function_mappings[func_name]["exception_column"]

            # Auto-select exception column if available
            for header in self.headers:
                if header.lower() == "exception":
                    exception_var.set(header)
                    break

            exception_dropdown = ttk.Combobox(func_frame, textvariable=exception_var, values=[""] + self.headers)
            exception_dropdown.grid(row=param_row, column=2, padx=5, pady=2, sticky="w")

            row += 1

    def create_classes_tab(self, classes_frame):
        """Create tab for mapping CSV columns to class method parameters."""

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

        # Add class mappings
        row = 0
        for cls_name, cls in self.classes.items():
            # Create frame for class
            cls_frame = ttk.LabelFrame(scrollable_frame, text=f"Class: {cls_name}")
            cls_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=5)

            # Initialize mapping for this class
            self.class_method_mappings[cls_name] = {}

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

                # Initialize mapping for this method
                self.class_method_mappings[cls_name][method_name] = {
                    "param_mappings": {},
                    "expected_output_column": tk.StringVar(value=""),
                    "exception_column": tk.StringVar(value="")
                }

                # Create header
                ttk.Label(method_frame, text="Parameter").grid(row=0, column=0, padx=5, pady=2, sticky="w")
                ttk.Label(method_frame, text="Type").grid(row=0, column=1, padx=5, pady=2, sticky="w")
                ttk.Label(method_frame, text="CSV Column").grid(row=0, column=2, padx=5, pady=2, sticky="w")

                # Add parameter mappings
                param_row = 1
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
                            param_type_obj = type_hints[param_name]
                            if hasattr(param_type_obj, "__origin__"):
                                origin = param_type_obj.__origin__.__name__
                                args = ", ".join(arg.__name__ if hasattr(arg, "__name__") else str(arg) for arg in param_type_obj.__args__)
                                param_type = f"{origin}[{args}]"
                            else:
                                param_type = param_type_obj.__name__
                    except (TypeError, AttributeError):
                        pass

                    ttk.Label(method_frame, text=param_type).grid(row=param_row, column=1, padx=5, pady=2, sticky="w")

                    # Add dropdown for CSV column mapping
                    column_var = tk.StringVar(value="")

                    # Auto-select matching column if available
                    for header in self.headers:
                        if header.lower() == param_name.lower():
                            column_var.set(header)
                            break

                    column_dropdown = ttk.Combobox(method_frame, textvariable=column_var, values=[""] + self.headers)
                    column_dropdown.grid(row=param_row, column=2, padx=5, pady=2, sticky="w")

                    # Store mapping
                    self.class_method_mappings[cls_name][method_name]["param_mappings"][param_name] = column_var

                    param_row += 1

                # Add expected output mapping
                ttk.Label(method_frame, text="Expected Output:").grid(row=param_row, column=0, padx=5, pady=2, sticky="w")
                output_var = self.class_method_mappings[cls_name][method_name]["expected_output_column"]

                # Auto-select matching output column if available
                # Try different patterns for expected output column names
                param_names = list(signature.parameters.keys())
                if 'self' in param_names:
                    param_names.remove('self')

                output_patterns = [
                    f"{method_name.lower()}_result",  # e.g., add_result
                    f"{method_name.lower()}_{param_names[0].lower()}" if len(param_names) == 1 else None,  # e.g., absolute_a
                ]

                for pattern in output_patterns:
                    if pattern is None:
                        continue

                    for header in self.headers:
                        if header.lower() == pattern:
                            output_var.set(header)
                            break

                    if output_var.get():  # If we found a match, stop looking
                        break

                output_dropdown = ttk.Combobox(method_frame, textvariable=output_var, values=[""] + self.headers)
                output_dropdown.grid(row=param_row, column=2, padx=5, pady=2, sticky="w")
                param_row += 1

                # Add exception mapping
                ttk.Label(method_frame, text="Exception:").grid(row=param_row, column=0, padx=5, pady=2, sticky="w")
                exception_var = self.class_method_mappings[cls_name][method_name]["exception_column"]

                # Auto-select exception column if available
                for header in self.headers:
                    if header.lower() == "exception":
                        exception_var.set(header)
                        break

                exception_dropdown = ttk.Combobox(method_frame, textvariable=exception_var, values=[""] + self.headers)
                exception_dropdown.grid(row=param_row, column=2, padx=5, pady=2, sticky="w")

                method_row += 1

            row += 1

    def on_ok(self):
        """Handle OK button click."""
        # Process function mappings
        functions_to_remove = []
        for func_name, mapping in self.function_mappings.items():
            # Check if any mappings are set
            has_mappings = False
            for param_name, column_var in mapping["param_mappings"].items():
                if column_var.get():
                    has_mappings = True
                    break

            if not has_mappings and not mapping["expected_output_column"].get() and not mapping["exception_column"].get():
                # No mappings for this function, mark it for removal
                functions_to_remove.append(func_name)

        # Remove functions with no mappings
        for func_name in functions_to_remove:
            self.function_mappings.pop(func_name)

        # Process class method mappings
        classes_to_remove = []
        for cls_name in self.class_method_mappings.keys():
            methods_to_remove = []
            for method_name, mapping in self.class_method_mappings[cls_name].items():
                # Check if any mappings are set
                has_mappings = False
                for param_name, column_var in mapping["param_mappings"].items():
                    if column_var.get():
                        has_mappings = True
                        break

                if not has_mappings and not mapping["expected_output_column"].get() and not mapping["exception_column"].get():
                    # No mappings for this method, mark it for removal
                    methods_to_remove.append(method_name)

            # Remove methods with no mappings
            for method_name in methods_to_remove:
                self.class_method_mappings[cls_name].pop(method_name)

            # If no methods left for this class, mark it for removal
            if not self.class_method_mappings[cls_name]:
                classes_to_remove.append(cls_name)

        # Remove classes with no methods
        for cls_name in classes_to_remove:
            self.class_method_mappings.pop(cls_name)

        self.destroy()
