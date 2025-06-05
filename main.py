import csv
import importlib.util
import inspect
import os
import sys
import tkinter as tk
from typing import Dict, List, Any, Tuple, Callable

# Add the project root directory to the Python path to ensure imports work on all platforms
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.test_generator_app import TestGeneratorApp

def main():
    """
    Main function to run the test generator GUI.
    """
    root = tk.Tk()
    TestGeneratorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
