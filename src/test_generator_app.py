import os
import subprocess
import tkinter as tk
import shutil
from tkinter import filedialog, scrolledtext, ttk
from typing import Dict, List, Any, Tuple


class TestGeneratorApp:
    """
    GUI application for the test generator.
    """
    def __init__(self, root):
        self.results_text = None
        self.root = root
        self.root.title("Python Test Generator")
        self.root.geometry("1200x900")

        self.python_file = tk.StringVar()
        self.num_cases = tk.IntVar(value=5)  # Default to 5 test cases

        # Import test_case_generator module
        try:
            from test_case_generator import test_case_generator
            self.test_generator = test_case_generator
        except ImportError:
            self.test_generator = None
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
        ttk.Button(button_frame, text="Generate Tests", command=self.generate_tests).pack(side=tk.LEFT, padx=5)

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


    def generate_tests(self):
        """Generate test cases for the selected Python file."""
        python_file = self.python_file.get()

        if not python_file:
            self.update_results_text("Error: Please select a Python file.")
            return

        # Check if file exists
        if not os.path.isfile(python_file):
            self.update_results_text(f"Error: Python file '{python_file}' not found")
            return

        try:
            # Clear results
            self.update_results_text("Generating test cases...\n")

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
                self.results_text.config(state=tk.NORMAL)
                self.results_text.insert(tk.END, f"File is outside source_files directory. Copying to source_files...\n")
                self.results_text.config(state=tk.DISABLED)
                self.root.update()

                # Create a new file path in the source_files directory
                source_file_path = os.path.join(source_files_dir, os.path.basename(python_file))

                # Copy the file content
                with open(python_file, 'r') as src_file:
                    file_content = src_file.read()

                with open(source_file_path, 'w') as dest_file:
                    dest_file.write(file_content)

                # Use the new file path for test generation
                file_for_test_generation = source_file_path

                self.results_text.config(state=tk.NORMAL)
                self.results_text.insert(tk.END, f"File copied to {source_file_path}\n")
                self.results_text.config(state=tk.DISABLED)
                self.root.update()

            # Generate test cases
            if self.test_generator:
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
                pytest_content = self.test_generator.generate_pytest_file(file_for_test_generation, pytest_output_path, num_cases)

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

        # Check if pytest file exists
        if not os.path.isfile(pytest_file):
            self.update_results_text(f"Error: Pytest file '{pytest_file}' not found. Please generate tests first.")
            return

        try:
            # Clear results
            self.update_results_text("Running pytest tests...\n")
            self.root.update()

            # Run pytest using subprocess
            try:
                # Run pytest with verbose output
                process = subprocess.Popen(
                    ["pytest", pytest_file, "-v"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
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
