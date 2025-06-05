import os
import subprocess
import tkinter as tk
import importlib.util
import inspect
import sys
import csv
import webbrowser
from tkinter import filedialog, scrolledtext, ttk, simpledialog, messagebox
from typing import Dict, List, Any, Tuple, Type, Optional, Union, get_type_hints

# Import dialog classes
from src.dialogs import TestInputDialog, TestInputTableDialog, CSVMappingDialog
from src.utils import set_window_size_and_position
from src.coverage_analyzer import CoverageAnalyzer

# Import TestCase and ClassMethodTestCase from models
try:
    from src.test_case_generator.models import TestCase, ClassMethodTestCase
except ImportError:
    # Define placeholder classes if imports fail
    class TestCase:
        def __init__(self, inputs, expected_output, description="", raises=None):
            self.inputs = inputs
            self.expected_output = expected_output
            self.description = description
            self.raises = raises

    class ClassMethodTestCase:
        def __init__(self, class_type, constructor_inputs, method_name, method_inputs,
                     expected_output, description="", raises=None):
            self.class_type = class_type
            self.constructor_inputs = constructor_inputs
            self.method_name = method_name
            self.method_inputs = method_inputs
            self.expected_output = expected_output
            self.description = description
            self.raises = raises


class TestGeneratorApp:
    """
    GUI application for the test generator.
    """
    def __init__(self, root):
        self.results_text = None
        self.root = root
        self.root.title("Python Test Generator")
        set_window_size_and_position(self.root, 1200, 900)

        self.python_file = tk.StringVar()
        self.num_cases = tk.IntVar(value=5)  # Default to 5 test cases

        # Store analyzed module information
        self.module = None
        self.functions = {}
        self.classes = {}
        self.user_test_cases = {}
        self.user_class_test_cases = {}
        self.csv_file = None
        self.csv_function_mappings = {}
        self.csv_class_method_mappings = {}

        # Initialize coverage analyzer
        self.coverage_analyzer = CoverageAnalyzer()

        # Import generate_pytest_file function
        try:
            from src.test_case_generator import generate_pytest_file
            self.generate_pytest_file = generate_pytest_file
        except ImportError:
            self.generate_pytest_file = None
            print("Warning: test_case_generator module not found")

        self.create_widgets()

    def create_widgets(self):
        """Create the GUI widgets."""
        # Create a frame for file selection
        file_frame = ttk.Frame(self.root, padding="10")
        file_frame.pack(fill=tk.X)

        # Python file selection
        ttk.Label(file_frame, text="Python File:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(file_frame, textvariable=self.python_file, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(file_frame, text="Browse...", command=self.browse_python_file).grid(row=0, column=2, padx=5, pady=5)

        # Setup coverage UI
        self.setup_coverage_ui()

        # Number of test cases slider
        ttk.Label(file_frame, text="Number of Test Cases:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        test_cases_slider = ttk.Scale(file_frame, from_=1, to=10, orient=tk.HORIZONTAL,
                                     variable=self.num_cases, length=200)
        test_cases_slider.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(file_frame, textvariable=self.num_cases).grid(row=1, column=2, padx=5, pady=5)

        # Ensure slider only uses integer values
        def on_slider_change(event):
            # Round to nearest integer
            current_value = self.num_cases.get()
            rounded_value = round(current_value)
            self.num_cases.set(rounded_value)

        # Bind to both button release and motion events to ensure integer values
        test_cases_slider.bind("<ButtonRelease-1>", on_slider_change)
        test_cases_slider.bind("<B1-Motion>", on_slider_change)

        # Button frame
        button_frame = ttk.Frame(file_frame)
        button_frame.grid(row=2, column=1, pady=10)

        # Generate Tests button
        ttk.Button(button_frame, text="Auto Generate Tests", command=self.generate_tests).pack(side=tk.LEFT, padx=5)

        # Generate User Tests button
        ttk.Button(button_frame, text="Generate User Tests", command=self.generate_user_tests).pack(side=tk.LEFT, padx=5)

        # Generate Tests from CSV button
        ttk.Button(button_frame, text="Generate Tests from CSV", command=self.generate_tests_from_csv).pack(side=tk.LEFT, padx=5)

        # Run Tests button
        ttk.Button(button_frame, text="Run Tests", command=self.run_tests).pack(side=tk.LEFT, padx=5)

        # Results text area
        results_frame = ttk.LabelFrame(self.root, text="Test Results", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.results_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD, width=80, height=20)
        self.results_text.pack(fill=tk.BOTH, expand=True)
        self.results_text.config(state=tk.DISABLED)

        # Configure tags for coloring
        self.results_text.tag_configure("success", foreground="green")
        self.results_text.tag_configure("failure", foreground="red")

    def browse_python_file(self):
        """Open file dialog to select Python file."""
        filename = filedialog.askopenfilename(
            title="Select Python File",
            filetypes=[("Python Files", "*.py"), ("All Files", "*.*")]
        )
        if filename:
            self.python_file.set(filename)

    def setup_coverage_ui(self):
        """Add coverage-related UI elements."""
        # Add coverage frame after existing buttons
        coverage_frame = tk.Frame(self.root)
        coverage_frame.pack(pady=10, fill='x')

        # Coverage checkbox
        self.enable_coverage = tk.BooleanVar(value=True)
        coverage_checkbox = tk.Checkbutton(
            coverage_frame,
            text="Enable Code Coverage Analysis",
            variable=self.enable_coverage,
            font=('Arial', 10)
        )
        coverage_checkbox.pack(side='left', padx=5)


        # Coverage percentage label
        self.coverage_label = tk.Label(
            coverage_frame,
            text="Coverage: ---%",
            font=('Arial', 10, 'bold'),
            fg='gray'
        )
        self.coverage_label.pack(side='right', padx=5)


    def update_coverage_label(self, percentage: float):
        """Update the coverage percentage label with color coding."""
        self.coverage_label.config(text=f"Coverage: {percentage:.1f}%")

        # Color coding based on coverage percentage
        if percentage >= 90:
            color = 'green'
        elif percentage >= 70:
            color = 'orange'
        else:
            color = 'red'

        self.coverage_label.config(fg=color)

    def format_coverage_summary(self, coverage_report: Dict) -> str:
        """Format coverage report for display."""
        if not coverage_report or "error" in coverage_report:
            return "Coverage analysis failed."

        summary = f"\n{'='*50}\n"
        summary += f"CODE COVERAGE REPORT\n"
        summary += f"{'='*50}\n"
        summary += f"File: {coverage_report.get('filename', 'Unknown')}\n"
        summary += f"Total Coverage: {coverage_report.get('total_coverage', 0):.1f}%\n"
        summary += f"Lines Covered: {coverage_report.get('covered_lines', 0)}/{coverage_report.get('total_lines', 0)}\n"

        # Function-level coverage
        function_coverage = coverage_report.get('function_coverage', [])
        if function_coverage:
            summary += f"\nFunction Coverage:\n"
            summary += f"{'-'*30}\n"
            for func in function_coverage:
                if "error" not in func:
                    summary += f"  {func['name']}: {func['coverage_percentage']:.1f}% "
                    summary += f"({func['covered_lines']}/{func['total_lines']} lines)\n"

        # Missing lines
        missing_lines = coverage_report.get('missing_lines', [])
        if missing_lines:
            summary += f"\nUncovered Lines: {missing_lines}\n"

        summary += f"{'='*50}\n"

        return summary

    def display_coverage_results(self, result: Dict):
        """Display test results with coverage information."""
        coverage_percentage = result.get("coverage_percentage", 0)

        # Update coverage label
        self.update_coverage_label(coverage_percentage)

        # Display test output
        output = result.get("test_output", "")
        self.display_result(output, 'green' if result["success"] else 'red')

        # Add coverage summary
        if "coverage_str" in result:
            # Use the pre-formatted coverage string
            coverage_summary = result["coverage_str"]
        else:
            # Fall back to the old method for backward compatibility
            coverage_report = result.get("coverage_report", {})
            coverage_summary = self.format_coverage_summary(coverage_report)

        self.display_result(f"\n{coverage_summary}", 'blue')


    def _validate_and_prepare_file(self, message="Generating test cases...\n"):
        """
        Validate the selected Python file and prepare it for test generation.

        Args:
            message: Message to display when starting the process

        Returns:
            tuple: (file_for_test_generation, pytest_output_path, module_name) or (None, None, None) if validation fails
        """
        python_file = self.python_file.get()

        if not python_file:
            self.update_results_text("Error: Please select a Python file.")
            return None, None, None

        # Check if file exists
        if not os.path.isfile(python_file):
            self.update_results_text(f"Error: Python file '{python_file}' not found")
            return None, None, None

        # Clear results
        self.update_results_text(message)

        # Generate default output path for pytest file
        module_name = os.path.basename(python_file).replace('.py', '')

        # Create tests directory if it doesn't exist
        tests_dir = os.path.join("tests", module_name)
        os.makedirs(tests_dir, exist_ok=True)

        # Set the output path for the pytest file
        pytest_output_path = os.path.join(tests_dir, f"test_{module_name}.py")

        # Check if the file is outside the source_files directory
        source_files_dir = "source_files"
        os.makedirs(source_files_dir, exist_ok=True)

        # Determine the file path to use for test generation
        file_for_test_generation = python_file

        # If the file is not in the source_files directory, copy it there
        if not python_file.startswith(os.path.join(os.getcwd(), source_files_dir)) and not python_file.startswith(source_files_dir):
            file_for_test_generation = self._copy_to_source_files(python_file, source_files_dir)

        return file_for_test_generation, pytest_output_path, module_name

    def _copy_to_source_files(self, python_file, source_files_dir):
        """
        Copy a Python file to the source_files directory.

        Args:
            python_file: Path to the Python file
            source_files_dir: Path to the source_files directory

        Returns:
            str: Path to the copied file
        """
        self.results_text.config(state=tk.NORMAL)
        self.results_text.insert(tk.END, f"File is outside source_files directory. Copying to source_files...\n")
        self.results_text.config(state=tk.DISABLED)
        self.root.update()

        # Create a new file path in the source_files directory
        source_file_path = os.path.join(source_files_dir, os.path.basename(python_file))

        # Copy the file content
        with open(python_file, 'r', encoding='utf-8') as src_file:
            file_content = src_file.read()

        with open(source_file_path, 'w', encoding='utf-8') as dest_file:
            dest_file.write(file_content)

        # Use the new file path for test generation
        self.results_text.config(state=tk.NORMAL)
        self.results_text.insert(tk.END, f"File copied to {source_file_path}\n")
        self.results_text.config(state=tk.DISABLED)
        self.root.update()

        return source_file_path

    def generate_tests(self):
        """Generate test cases for the selected Python file using auto-generation."""
        try:
            file_for_test_generation, pytest_output_path, module_name = self._validate_and_prepare_file()
            if not file_for_test_generation:
                return

            # Generate test cases
            if self.generate_pytest_file:
                self.results_text.config(state=tk.NORMAL)
                self.results_text.insert(tk.END, f"Analyzing module {file_for_test_generation}...\n")
                self.results_text.config(state=tk.DISABLED)
                self.root.update()

                # Generate pytest file
                self.results_text.config(state=tk.NORMAL)
                self.results_text.insert(tk.END, f"Generating pytest file...\n")
                self.results_text.config(state=tk.DISABLED)
                self.root.update()

                # Generate the pytest file and get its content
                num_cases = self.num_cases.get()
                pytest_content = self.generate_pytest_file(file_for_test_generation, pytest_output_path, num_cases)

                # Show success message and file content
                self.results_text.config(state=tk.NORMAL)
                self.results_text.delete(1.0, tk.END)
                self.results_text.insert(tk.END, f"Pytest file generated and saved to {pytest_output_path}\n\n")
                self.results_text.insert(tk.END, "File content:\n\n")
                self.results_text.insert(tk.END, pytest_content)
                self.results_text.insert(tk.END, "\n\nYou can now click 'Run Tests' to execute the tests.\n")
                self.results_text.config(state=tk.DISABLED)
            else:
                self.update_results_text("Error: test_case_generator module not available.")

        except Exception as e:
            self.update_results_text(f"Error generating test cases: {str(e)}")

    def generate_user_tests(self):
        """Generate test cases for the selected Python file using user input."""
        try:
            file_for_test_generation, pytest_output_path, module_name = self._validate_and_prepare_file("Analyzing module...\n")
            if not file_for_test_generation:
                return

            # Step 1: Analyze the module
            if not self.analyze_module(file_for_test_generation):
                self.update_results_text("Error: Failed to analyze module.")
                return

            # Step 2: Show dialog for user input
            self.update_results_text("Please input test parameters for each function and method...")
            if not self.show_test_input_dialog():
                self.update_results_text("Error: Failed to collect user input.")
                return

            # Step 3: Generate tests using user input
            self.update_results_text("Generating tests with user input...")
            try:
                pytest_content = self.generate_tests_with_user_input(file_for_test_generation, pytest_output_path)

                # Show success message and file content
                self.results_text.config(state=tk.NORMAL)
                self.results_text.delete(1.0, tk.END)
                self.results_text.insert(tk.END, f"Pytest file generated and saved to {pytest_output_path}\n\n")
                self.results_text.insert(tk.END, "File content:\n\n")
                self.results_text.insert(tk.END, pytest_content)
                self.results_text.insert(tk.END, "\n\nYou can now click 'Run Tests' to execute the tests.\n")
                self.results_text.config(state=tk.DISABLED)
            except Exception as e:
                self.update_results_text(f"Error generating tests: {str(e)}")

        except Exception as e:
            self.update_results_text(f"Error generating test cases: {str(e)}")

    def generate_tests_from_csv(self):
        """Generate test cases for the selected Python file using data from a CSV file."""
        try:
            file_for_test_generation, pytest_output_path, module_name = self._validate_and_prepare_file("Analyzing module...\n")
            if not file_for_test_generation:
                return

            # Step 1: Analyze the module
            if not self.analyze_module(file_for_test_generation):
                self.update_results_text("Error: Failed to analyze module.")
                return

            # Step 2: Select CSV file
            self.update_results_text("Please select a CSV file with test data...")
            csv_file = filedialog.askopenfilename(
                title="Select CSV File",
                filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
            )

            if not csv_file:
                self.update_results_text("CSV file selection cancelled.")
                return

            # Normalize the CSV file path to ensure it works on all platforms
            self.csv_file = os.path.normpath(csv_file)

            # Step 3: Show dialog for mapping CSV columns to parameters
            self.update_results_text(f"Mapping columns from {os.path.basename(csv_file)}...")
            dialog = CSVMappingDialog(self.root, csv_file, self.functions, self.classes)
            self.root.wait_window(dialog)

            # Get mappings from dialog
            self.csv_function_mappings = dialog.function_mappings
            self.csv_class_method_mappings = dialog.class_method_mappings

            if not self.csv_function_mappings and not self.csv_class_method_mappings:
                self.update_results_text("No mappings defined. Test generation cancelled.")
                return

            # Step 4: Generate tests using CSV data
            self.update_results_text("Generating tests with CSV data...")
            try:
                pytest_content = self.generate_tests_with_csv_data(file_for_test_generation, pytest_output_path)

                # Show success message and file content
                self.results_text.config(state=tk.NORMAL)
                self.results_text.delete(1.0, tk.END)
                self.results_text.insert(tk.END, f"Pytest file generated and saved to {pytest_output_path}\n\n")
                self.results_text.insert(tk.END, "File content:\n\n")
                self.results_text.insert(tk.END, pytest_content)
                self.results_text.insert(tk.END, "\n\nYou can now click 'Run Tests' to execute the tests.\n")
                self.results_text.config(state=tk.DISABLED)
            except Exception as e:
                self.update_results_text(f"Error generating tests: {str(e)}")

        except Exception as e:
            self.update_results_text(f"Error generating test cases: {str(e)}")

    def update_results_text(self, text):
        """Update the results text area with the given text."""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, text)
        self.results_text.config(state=tk.DISABLED)

    def update_results_text_with_tags(self, tagged_text):
        """Update the results text area with tagged text.

        Args:
            tagged_text: List of (text, tag) tuples
        """
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)

        for text, tag in tagged_text:
            self.results_text.insert(tk.END, text, tag if tag else "")

        self.results_text.config(state=tk.DISABLED)

    def display_result(self, text, color=None):
        """Display text in the results area with optional color.

        Args:
            text: The text to display
            color: Optional color ('red', 'green', 'blue')
        """
        self.results_text.config(state=tk.NORMAL)

        # Configure blue tag if it doesn't exist
        if color == 'blue':
            try:
                self.results_text.tag_cget('blue', 'foreground')
            except tk.TclError:
                self.results_text.tag_configure('blue', foreground='blue')

        # Map color names to tag names
        tag = None
        if color == 'green':
            tag = 'success'
        elif color == 'red':
            tag = 'failure'
        elif color == 'blue':
            tag = 'blue'

        # Append text without clearing existing content
        if tag:
            self.results_text.insert(tk.END, text, tag)
        else:
            self.results_text.insert(tk.END, text)

        self.results_text.config(state=tk.DISABLED)
        self.results_text.see(tk.END)  # Scroll to the end

    def analyze_module(self, module_path: str) -> bool:
        """
        Analyze the module and extract functions and classes.

        Args:
            module_path: Path to the Python module file

        Returns:
            True if analysis was successful, False otherwise
        """
        try:
            # Clear previous analysis
            self.module = None
            self.functions = {}
            self.classes = {}
            self.user_test_cases = {}
            self.user_class_test_cases = {}

            # Import the module
            module_name = os.path.basename(module_path).replace('.py', '')
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec is None or spec.loader is None:
                self.update_results_text(f"Error: Could not load module from {module_path}")
                return False

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            self.module = module

            # Get all functions and classes from the module
            for name, obj in inspect.getmembers(module):
                if inspect.isfunction(obj) and obj.__module__ == module.__name__:
                    self.functions[name] = obj
                elif inspect.isclass(obj) and obj.__module__ == module.__name__:
                    self.classes[name] = obj

            # Update results text
            self.update_results_text(f"Module {module_name} analyzed successfully.\n\n"
                                    f"Found {len(self.functions)} functions and {len(self.classes)} classes.")

            # Clean up module from sys.modules
            if module_name in sys.modules:
                del sys.modules[module_name]

            return True
        except Exception as e:
            self.update_results_text(f"Error analyzing module: {str(e)}")
            return False

    def show_test_input_dialog(self):
        """
        Show dialog for user to input test parameters, expected outputs, and exception types.
        Uses a table-like interface to display all functions and methods in a single view.

        Returns:
            True if user input was collected successfully, False otherwise
        """
        try:
            # Clear previous user test cases
            self.user_test_cases = {}
            self.user_class_test_cases = {}

            # Show table dialog with all functions and methods
            dialog = TestInputTableDialog(self.root, self.functions, self.classes)
            self.root.wait_window(dialog)

            # Get test cases from dialog
            self.user_test_cases = dialog.user_test_cases
            self.user_class_test_cases = dialog.user_class_test_cases

            # Count the number of test cases
            num_function_tests = sum(len(tests) for tests in self.user_test_cases.values() if isinstance(tests[0], TestCase))
            num_method_tests = sum(
                sum(len(tests) for tests in cls_tests.values() if isinstance(tests[0], ClassMethodTestCase))
                for cls_tests in self.user_class_test_cases.values()
            )

            self.update_results_text(f"User input collected successfully.\n\n"
                                    f"Created {num_function_tests} function tests and {num_method_tests} method tests.")
            return True
        except Exception as e:
            self.update_results_text(f"Error collecting user input: {str(e)}")
            return False

    def generate_tests_with_csv_data(self, module_path: str, output_path: str) -> str:
        """
        Generate tests using data from a CSV file.

        Args:
            module_path: Path to the Python module file
            output_path: Path where the pytest file should be saved

        Returns:
            The content of the generated pytest file
        """
        try:
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

            # Read CSV data
            csv_data = []
            with open(self.csv_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    csv_data.append(row)

            if not csv_data:
                raise ValueError("CSV file is empty or has no valid data")

            # Create test cases from CSV data
            function_test_cases = {}
            class_method_test_cases = {}

            # Process function mappings
            for func_name, mapping in self.csv_function_mappings.items():
                function_test_cases[func_name] = []

                # Get the function object
                func = functions.get(func_name)
                if not func:
                    continue

                # Process each row in the CSV
                for row in csv_data:
                    # Get parameter values from CSV
                    param_values = []
                    for param_name, column_var in mapping["param_mappings"].items():
                        column_name = column_var.get()
                        if column_name and column_name in row:
                            # Try to convert the value to the appropriate type
                            value = row[column_name]
                            try:
                                # Try to evaluate as Python expression
                                param_values.append(eval(value))
                            except (SyntaxError, NameError):
                                # If not a valid expression, use as string
                                param_values.append(value)
                        else:
                            # If no mapping or column not found, use None
                            param_values.append(None)

                    # Get expected output
                    expected_output = None
                    output_column = mapping["expected_output_column"].get()
                    if output_column and output_column in row:
                        value = row[output_column]
                        try:
                            expected_output = eval(value)
                        except (SyntaxError, NameError):
                            expected_output = value

                    # Get exception
                    exception_class = None
                    exception_column = mapping["exception_column"].get()
                    if exception_column and exception_column in row:
                        exception_name = row[exception_column]
                        if exception_name and exception_name != "None":
                            try:
                                exception_class = eval(exception_name)
                            except (NameError, SyntaxError):
                                # If exception name is not valid, ignore it
                                pass

                    # Create test case
                    test_case = TestCase(
                        inputs=param_values,
                        expected_output=expected_output,
                        description=f"CSV-defined test for {func_name}",
                        raises=exception_class
                    )

                    function_test_cases[func_name].append(test_case)

            # Process class method mappings
            for cls_name, methods in self.csv_class_method_mappings.items():
                class_method_test_cases[cls_name] = {}

                # Get the class object
                cls = classes.get(cls_name)
                if not cls:
                    continue

                for method_name, mapping in methods.items():
                    class_method_test_cases[cls_name][method_name] = []

                    # Process each row in the CSV
                    for row in csv_data:
                        # Get parameter values from CSV
                        param_values = []
                        for param_name, column_var in mapping["param_mappings"].items():
                            column_name = column_var.get()
                            if column_name and column_name in row:
                                # Try to convert the value to the appropriate type
                                value = row[column_name]
                                try:
                                    # Try to evaluate as Python expression
                                    param_values.append(eval(value))
                                except (SyntaxError, NameError):
                                    # If not a valid expression, use as string
                                    param_values.append(value)
                            else:
                                # If no mapping or column not found, use None
                                param_values.append(None)

                        # Get expected output
                        expected_output = None
                        output_column = mapping["expected_output_column"].get()
                        if output_column and output_column in row:
                            value = row[output_column]
                            try:
                                expected_output = eval(value)
                            except (SyntaxError, NameError):
                                expected_output = value

                        # Get exception
                        exception_class = None
                        exception_column = mapping["exception_column"].get()
                        if exception_column and exception_column in row:
                            exception_name = row[exception_column]
                            if exception_name and exception_name != "None":
                                try:
                                    exception_class = eval(exception_name)
                                except (NameError, SyntaxError):
                                    # If exception name is not valid, ignore it
                                    pass

                        # Create test case
                        # For simplicity, we'll use empty constructor inputs
                        constructor_inputs = []

                        test_case = ClassMethodTestCase(
                            class_type=cls,
                            constructor_inputs=constructor_inputs,
                            method_name=method_name,
                            method_inputs=param_values,
                            expected_output=expected_output,
                            description=f"CSV-defined test for {cls_name}.{method_name}",
                            raises=exception_class
                        )

                        class_method_test_cases[cls_name][method_name].append(test_case)

            # Extract imports from source file
            import_statements = self._extract_imports_from_source(module_path, module_name)

            # Generate the pytest file content
            content = self._generate_pytest_file_header(module_name, functions, classes, import_statements, "CSV data")

            # Generate function tests
            for func_name, test_cases in function_test_cases.items():
                content.extend(self._generate_function_tests(func_name, test_cases))

            # Generate class tests
            for cls_name, method_test_cases in class_method_test_cases.items():
                content.extend(self._generate_class_tests(cls_name, method_test_cases))

            final_content = "\n".join(content)

            # Save to file if output_path is provided
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(final_content)

            # Clean up module from sys.modules
            if module_name in sys.modules:
                del sys.modules[module_name]

            return final_content
        except Exception as e:
            raise Exception(f"Error generating tests with CSV data: {str(e)}")

    def generate_tests_with_user_input(self, module_path: str, output_path: str) -> str:
        """
        Generate tests using user input.

        Args:
            module_path: Path to the Python module file
            output_path: Path where the pytest file should be saved

        Returns:
            The content of the generated pytest file
        """
        try:
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

            # Create a set to collect mock functions and a dictionary to store valid constructor inputs for each class
            mock_functions = set()
            valid_constructor_inputs = {}

            # Extract imports from source file
            import_statements = self._extract_imports_from_source(module_path, module_name)

            # Generate the pytest file content
            content = self._generate_pytest_file_header(module_name, functions, classes, import_statements, "user input")

            # Generate function tests
            for func_name, test_cases in self.user_test_cases.items():
                content.extend(self._generate_function_tests(func_name, test_cases))

            # Generate class tests
            for cls_name, method_test_cases in self.user_class_test_cases.items():
                content.extend(self._generate_class_tests(cls_name, method_test_cases))

            final_content = "\n".join(content)

            # Save to file if output_path is provided
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(final_content)

            # Clean up module from sys.modules
            if module_name in sys.modules:
                del sys.modules[module_name]

            return final_content
        except Exception as e:
            raise Exception(f"Error generating tests with user input: {str(e)}")

    def _extract_imports_from_source(self, module_path, module_name):
        """
        Extract import statements from the source file.

        Args:
            module_path: Path to the Python module file
            module_name: Name of the module

        Returns:
            list: List of import statements
        """
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

        return sorted(set(import_statements))

    def _generate_pytest_file_header(self, module_name, functions, classes, import_statements, source_type):
        """
        Generate the header section of a pytest file.

        Args:
            module_name: Name of the module
            functions: Dictionary of functions
            classes: Dictionary of classes
            import_statements: List of import statements
            source_type: Source of test data (e.g., "CSV data", "user input")

        Returns:
            list: List of lines for the pytest file header
        """
        content = [
            f"# Automatically generated tests for {module_name} using {source_type}",
            "import pytest",
            "import dataclasses",
            "import datetime",
            "import typing",
        ]

        # Add unique imports to content
        for import_stmt in import_statements:
            content.append(import_stmt)

        # Import statements for functions and classes
        if functions:
            content.append(f"from source_files.{module_name} import {', '.join(functions.keys())}")
        if classes:
            content.append(f"from source_files.{module_name} import {', '.join(classes.keys())}")

        content.extend([
            "",
            f"# This file was generated by the test_case_generator with {source_type}"
        ])

        return content

    def _generate_function_tests(self, func_name, test_cases):
        """
        Generate pytest tests for a function.

        Args:
            func_name: Name of the function
            test_cases: List of test cases for the function

        Returns:
            list: List of lines for the function tests
        """
        if not test_cases:
            return []

        content = ["", f"# Tests for function {func_name}"]

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

        return content

    def _generate_class_tests(self, cls_name, method_test_cases):
        """
        Generate pytest tests for a class.

        Args:
            cls_name: Name of the class
            method_test_cases: Dictionary of test cases for each method

        Returns:
            list: List of lines for the class tests
        """
        if not method_test_cases:
            return []

        content = []
        content.append("")
        content.append(f"# Tests for class {cls_name}")
        content.append("")

        # Create a fixture with valid constructor inputs if available
        if '__init__' in method_test_cases:
            valid_constructor_case = None
            for tc in method_test_cases['__init__']:
                if tc.raises is None:
                    valid_constructor_case = tc
                    break

            if valid_constructor_case:
                content.extend([
                    "@pytest.fixture",
                    f"def {cls_name.lower()}_instance():",
                    f"    # Create a valid instance of {cls_name} for testing",
                    f"    return {cls_name}(*{repr(valid_constructor_case.constructor_inputs)})",
                    ""
                ])

        # Generate tests for each method
        for method_name, test_cases in method_test_cases.items():
            if not test_cases:
                continue

            if method_name == '__init__':
                # Constructor tests
                content.append(f"# Tests for {cls_name} constructor")

                # Regular constructor cases
                regular_cases = [tc for tc in test_cases if tc.raises is None]
                if regular_cases:
                    content.append(f"@pytest.mark.parametrize('constructor_inputs', [")
                    for tc in regular_cases:
                        serialized_inputs = repr(tc.constructor_inputs)
                        content.append(f"    # {tc.description}")
                        content.append(f"    {serialized_inputs},")
                    content.append("])")
                    content.append(f"def test_{cls_name}_constructor(constructor_inputs):")
                    content.append(f"    instance = {cls_name}(*constructor_inputs)")
                    content.append(f"    assert instance is not None")
                    content.append("")

                # Exception constructor cases
                exception_cases = [tc for tc in test_cases if tc.raises is not None]
                for i, tc in enumerate(exception_cases):
                    content.append(f"def test_{cls_name}_constructor_raises_{i}():")
                    content.append(f"    # {tc.description}")
                    content.append(f"    with pytest.raises({tc.raises.__name__}):")
                    content.append(f"        {cls_name}(*{repr(tc.constructor_inputs)})")
                    content.append("")
            else:
                # Method tests
                content.append(f"# Tests for {cls_name}.{method_name} method")

                # Regular method cases
                regular_cases = [tc for tc in test_cases if tc.raises is None]
                if regular_cases:
                    content.append(f"@pytest.mark.parametrize('method_inputs,expected', [")
                    for tc in regular_cases:
                        serialized_inputs = repr(tc.method_inputs)
                        serialized_expected = repr(tc.expected_output)
                        content.append(f"    # {tc.description}")
                        content.append(f"    ({serialized_inputs}, {serialized_expected}),")
                    content.append("])")
                    content.append(f"def test_{cls_name}_{method_name}({cls_name.lower()}_instance, method_inputs, expected):")
                    content.append(f"    result = {cls_name.lower()}_instance.{method_name}(*method_inputs)")
                    content.append(f"    assert result == expected")
                    content.append("")

                # Exception method cases
                exception_cases = [tc for tc in test_cases if tc.raises is not None]
                for i, tc in enumerate(exception_cases):
                    content.append(f"def test_{cls_name}_{method_name}_raises_{i}({cls_name.lower()}_instance):")
                    content.append(f"    # {tc.description}")
                    content.append(f"    with pytest.raises({tc.raises.__name__}):")
                    content.append(f"        {cls_name.lower()}_instance.{method_name}(*{repr(tc.method_inputs)})")
                    content.append("")

        return content

    def run_tests(self):
        """Run pytest tests and display results."""
        python_file = self.python_file.get()

        if not python_file:
            self.update_results_text("Error: Please select a Python file.")
            return

        # Check if file exists
        if not os.path.isfile(python_file):
            self.update_results_text(f"Error: Python file '{python_file}' not found")
            return

        # Get the module name from the file name, regardless of its location
        module_name = os.path.basename(python_file).replace('.py', '')

        # Check if the file is outside the source_files directory
        source_files_dir = "source_files"
        source_file_path = os.path.join(source_files_dir, os.path.basename(python_file))

        # If the file exists in source_files, use that for the module name
        if os.path.isfile(source_file_path):
            module_name = os.path.basename(source_file_path).replace('.py', '')

        # Generate the expected pytest file path
        tests_dir = os.path.join("tests", module_name)
        pytest_file = os.path.join(tests_dir, f"test_{module_name}.py")

        # Check if the pytest file exists
        if os.path.isfile(pytest_file):
            # Use the pytest file
            pytest_file_to_run = pytest_file
        else:
            self.update_results_text(f"Error: Pytest file '{pytest_file}' not found. Please generate tests first.")
            return

        try:
            # Clear results
            self.update_results_text("Running pytest tests...\n")
            self.root.update()

            # Check if coverage is enabled
            if self.enable_coverage.get():
                # Run tests with coverage
                try:
                    result = self.coverage_analyzer.run_tests_with_coverage(
                        pytest_file_to_run,
                        python_file
                    )

                    if result["success"]:
                        self.display_coverage_results(result)
                    else:
                        self.display_result(f"Tests failed:\n{result.get('test_output', '')}", 'red')
                except Exception as e:
                    self.update_results_text(f"Error running tests with coverage: {str(e)}")
            else:
                # Run tests without coverage (original functionality)
                try:
                    # Get the project root directory
                    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

                    # Set up environment with PYTHONPATH to include project root
                    env = os.environ.copy()
                    if 'PYTHONPATH' in env:
                        env['PYTHONPATH'] = f"{project_root}{os.pathsep}{env['PYTHONPATH']}"
                    else:
                        env['PYTHONPATH'] = project_root

                    # Run pytest with verbose output and proper PYTHONPATH
                    process = subprocess.Popen(
                        ["pytest", pytest_file_to_run, "-v"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        env=env
                    )
                    stdout, stderr = process.communicate()

                    # Prepare the output with color tags
                    output = []

                    # Add stdout with appropriate color tags
                    for line in stdout.splitlines():
                        if "PASSED" in line:
                            output.append((line + "\n", "success"))
                        elif "FAILED" in line or "ERROR" in line:
                            output.append((line + "\n", "failure"))
                        else:
                            output.append((line + "\n", ""))

                    # Add stderr if there's any
                    if stderr:
                        output.append(("\nErrors:\n", "failure"))
                        for line in stderr.splitlines():
                            output.append((line + "\n", "failure"))

                    # Add summary
                    if process.returncode == 0:
                        output.append(("\nAll tests passed successfully!\n", "success"))
                    else:
                        output.append(("\nSome tests failed. See details above.\n", "failure"))

                    # Display results with color formatting
                    self.update_results_text_with_tags(output)

                except FileNotFoundError:
                    self.update_results_text("Error: pytest command not found. Please make sure pytest is installed.\n"
                                            "You can install it using: pip install pytest")

        except Exception as e:
            self.update_results_text(f"Error running tests: {str(e)}")


def main():
    """Main entry point for the GUI application."""
    root = tk.Tk()
    app = TestGeneratorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
