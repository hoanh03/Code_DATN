# class_analyzer.py
# Contains functionality for analyzing Python classes

import inspect
import logging
from typing import Any, Dict, List, Set, Type, get_type_hints


class ClassAnalyzer:
    """Analyzes Python classes using reflection with support for inheritance."""

    @staticmethod
    def analyze_class(cls: Type) -> Dict[str, Any]:
        """
        Analyze a class using reflection, including inherited members.

        Args:
            cls: The class to analyze

        Returns:
            Dictionary with class information
        """
        try:
            class_info = {
                'name': cls.__name__,
                'methods': {},
                'properties': {},
                'class_methods': {},
                'static_methods': {},
                'special_methods': {},  # New category for magic/dunder methods
                'base_classes': [base.__name__ for base in cls.__bases__ if base is not object],
            }

            # Track processed methods to avoid duplicates from multiple inheritance paths
            processed_methods: Set[str] = set()
            processed_properties: Set[str] = set()

            # Get the class hierarchy
            class_hierarchy = ClassAnalyzer._get_class_hierarchy(cls)

            # First pass: Identify static and class methods in all classes in the hierarchy
            # This is necessary because static and class methods are not directly accessible in derived classes
            for current_cls in class_hierarchy:
                ClassAnalyzer._identify_special_method_types(current_cls, class_info, processed_methods)

            # Second pass: Process all other methods and properties
            # Process the class hierarchy from bottom to top
            # This ensures derived class methods override base class methods
            for current_cls in class_hierarchy:
                ClassAnalyzer._analyze_class_members(current_cls, class_info, processed_methods, processed_properties)

            return class_info
        except Exception as e:
            logging.error(f"Error analyzing class {cls.__name__}: {str(e)}")
            # Return partial information if available, or a minimal structure
            return class_info if 'name' in locals().get('class_info', {}) else {
                'name': getattr(cls, '__name__', 'Unknown'),
                'methods': {},
                'properties': {},
                'class_methods': {},
                'static_methods': {},
                'special_methods': {},
                'base_classes': [],
                'error': str(e)
            }

    @staticmethod
    def _get_class_hierarchy(cls: Type) -> List[Type]:
        """
        Get the class hierarchy from derived to base classes.

        Args:
            cls: The class to analyze

        Returns:
            List of classes in the hierarchy, starting with the derived class
        """
        hierarchy = [cls]
        for base in cls.__bases__:
            if base is not object:  # Skip the 'object' base class
                hierarchy.extend(ClassAnalyzer._get_class_hierarchy(base))
        return hierarchy

    @staticmethod
    def _identify_special_method_types(cls: Type, class_info: Dict[str, Any], processed_methods: Set[str]) -> None:
        """
        Identify static methods and class methods in a class.

        Args:
            cls: The class to analyze
            class_info: Dictionary to update with class information
            processed_methods: Set of method names that have already been processed
        """
        try:
            # Analyze class attributes to identify static and class methods
            for name, value in cls.__dict__.items():
                # Skip if already processed (from a more derived class)
                if name in processed_methods:
                    continue

                try:
                    # Identify static methods and class methods from class __dict__
                    if isinstance(value, staticmethod):
                        processed_methods.add(name)
                        method = value.__func__  # Get the underlying function
                        sig = inspect.signature(method)
                        class_info['static_methods'][name] = {
                            'signature': sig,
                            'parameters': {param_name: param for param_name, param in sig.parameters.items()},
                            'type_hints': get_type_hints(method),
                            'defined_in': cls.__name__
                        }
                    elif isinstance(value, classmethod):
                        processed_methods.add(name)
                        method = value.__func__  # Get the underlying function
                        sig = inspect.signature(method)
                        class_info['class_methods'][name] = {
                            'signature': sig,
                            'parameters': {param_name: param for param_name, param in sig.parameters.items()
                                          if param_name != 'cls'},
                            'type_hints': get_type_hints(method),
                            'defined_in': cls.__name__
                        }
                except Exception as e:
                    logging.warning(f"Error analyzing method {name} of {cls.__name__}: {str(e)}")
        except Exception as e:
            logging.error(f"Error identifying special method types in class {cls.__name__}: {str(e)}")

    @staticmethod
    def _analyze_class_members(cls: Type, class_info: Dict[str, Any],
                              processed_methods: Set[str], processed_properties: Set[str]) -> None:
        """
        Analyze members of a specific class and update the class_info dictionary.

        Args:
            cls: The class to analyze
            class_info: Dictionary to update with class information
            processed_methods: Set of method names that have already been processed
            processed_properties: Set of property names that have already been processed
        """
        try:
            # Analyze constructor if not already processed
            if 'constructor' not in class_info and hasattr(cls, '__init__'):
                try:
                    init_method = cls.__init__
                    sig = inspect.signature(init_method)
                    class_info['constructor'] = {
                        'signature': sig,
                        'parameters': {name: param for name, param in sig.parameters.items() if name != 'self'},
                        'type_hints': get_type_hints(init_method),
                        'defined_in': cls.__name__
                    }
                except Exception as e:
                    logging.warning(f"Error analyzing constructor of {cls.__name__}: {str(e)}")

            # Analyze regular methods and special methods
            for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
                # Skip if already processed (from a more derived class or as static/class method)
                if name in processed_methods:
                    continue

                processed_methods.add(name)

                try:
                    # Handle special methods (magic/dunder methods)
                    if name.startswith('__') and name.endswith('__'):
                        if name != '__init__':  # Skip __init__ as it's handled separately
                            method_dict = class_info['special_methods']
                        else:
                            continue
                    # Skip other private methods
                    elif name.startswith('_'):
                        continue
                    else:
                        # Regular instance method
                        method_dict = class_info['methods']

                    sig = inspect.signature(method)
                    method_dict[name] = {
                        'signature': sig,
                        'parameters': {name: param for name, param in sig.parameters.items()
                                    if name != 'self' and name != 'cls'},
                        'type_hints': get_type_hints(method),
                        'defined_in': cls.__name__
                    }
                except Exception as e:
                    logging.warning(f"Error analyzing method {name} of {cls.__name__}: {str(e)}")

            # Analyze properties
            for name, prop in inspect.getmembers(cls, predicate=lambda x: isinstance(x, property)):
                # Skip if already processed (from a more derived class)
                if name in processed_properties:
                    continue

                processed_properties.add(name)

                try:
                    type_hints = {}
                    if prop.fget:
                        try:
                            type_hints = get_type_hints(prop.fget)
                        except Exception:
                            pass  # Ignore errors in getting type hints

                    class_info['properties'][name] = {
                        'has_getter': prop.fget is not None,
                        'has_setter': prop.fset is not None,
                        'has_deleter': prop.fdel is not None,
                        'type_hints': type_hints,
                        'defined_in': cls.__name__
                    }
                except Exception as e:
                    logging.warning(f"Error analyzing property {name} of {cls.__name__}: {str(e)}")

        except Exception as e:
            logging.error(f"Error analyzing members of class {cls.__name__}: {str(e)}")
            # Continue with other classes in the hierarchy
