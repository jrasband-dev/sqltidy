"""
Rule plugin system for SQLTidy.

Provides a decorator-based rule registration system similar to Polars,
allowing users to easily extend SQLTidy with custom formatting rules.

Example:
    # my_rule.py
    from sqltidy.rules import sqltidy_rule

    @sqltidy_rule(rule_type="tidy", order=50)
    def remove_semicolons(tokens, ctx):
        '''Remove trailing semicolons.'''
        if tokens and tokens[-1] == ';':
            return tokens[:-1]
        return tokens

    # Use from CLI:
    # sqltidy format input.sql --rule my_rule.py

    # Or from Python:
    # from sqltidy.rules import load_rules
    # load_rules('my_rule.py')
"""

import importlib.util
import sys
from pathlib import Path
from typing import Callable, Optional, Set, List, Union, Dict
from sqltidy.rules.base import BaseRule


# Global registry of rules
_RULE_PLUGIN_REGISTRY = []

# Track which files have been loaded to avoid duplicates
_LOADED_PLUGIN_FILES = set()


def get_user_rules_directory() -> Path:
    """Get the user's custom rules directory (~/.sqltidy/rules/)."""
    return Path.home() / ".sqltidy" / "rules"


def auto_load_user_rules() -> List[type]:
    """
    Automatically load all custom rules from user's rules directory.

    Looks for Python files in ~/.sqltidy/rules/ and loads them.
    Creates the directory if it doesn't exist.
    Skips files that have already been loaded to avoid duplicates.

    Returns:
        List of rule classes that were loaded
    """
    rules_dir = get_user_rules_directory()

    # Create directory if it doesn't exist
    rules_dir.mkdir(parents=True, exist_ok=True)

    # Load all .py files from the directory
    loaded_rules = []
    if rules_dir.exists():
        for filepath in rules_dir.glob("*.py"):
            if filepath.name.startswith("_"):
                continue  # Skip private files

            # Skip if already loaded
            file_key = str(filepath.absolute())
            if file_key in _LOADED_PLUGIN_FILES:
                continue

            try:
                rules = load_rule_file(filepath)
                loaded_rules.extend(rules)
                _LOADED_PLUGIN_FILES.add(file_key)
            except Exception as e:
                # Silently skip files that can't be loaded
                # (they might not be rule files)
                import logging
                logging.debug(f"Skipping file {filepath}: {e}")

    return loaded_rules


def sqltidy_rule(
    rule_type: str = "tidy",
    order: int = 50,
    supported_dialects: Optional[Set[str]] = None,
    name: Optional[str] = None,
    config_fields: Optional[Dict] = None,
):
    """
    Decorator to register a function as a SQLTidy rule.

    This decorator allows you to turn any function into a formatting rule
    without having to create a class or understand the internals.

    Args:
        rule_type: "tidy" (formatting) or "rewrite" (transformation)
        order: Execution order (lower runs first)
        supported_dialects: Set of dialects this rule applies to, or None for all
        name: Optional custom name for the rule class
        config_fields: Optional dict of ConfigField declarations for this rule

    Returns:
        Decorator function

    Example:
        @sqltidy_rule(rule_type="tidy", order=100, config_fields={
            "my_option": ConfigField(name="my_option", default=True, ...)
        })
        def my_rule(tokens, ctx):
            '''Remove trailing semicolons.'''
            if tokens and tokens[-1] == ';':
                return tokens[:-1]
            return tokens

    The decorated function should have signature:
        def rule_func(tokens: List[str], ctx: FormatterContext) -> List[str]
    """

    def decorator(func: Callable) -> Callable:
        # Create a rule class from the function
        class_name = name or f"{func.__name__.title().replace('_', '')}Rule"

        class PluginRule(BaseRule):
            pass

        # Set class attributes
        PluginRule.__name__ = class_name
        PluginRule.__qualname__ = class_name
        PluginRule.rule_type = rule_type
        PluginRule.order = order
        PluginRule.__doc__ = func.__doc__

        if supported_dialects:
            PluginRule.supported_dialects = supported_dialects

        # Set config_fields if provided as decorator parameter
        if config_fields:
            PluginRule.config_fields = config_fields
        # Or copy config_fields if defined on the function (for backward compatibility)
        elif hasattr(func, "config_fields"):
            PluginRule.config_fields = func.config_fields

        # Override apply method to call the function
        def apply(self, tokens, ctx):
            return func(tokens, ctx)

        PluginRule.apply = apply

        # Register the rule class
        _RULE_PLUGIN_REGISTRY.append(PluginRule)

        # Store reference on the function for introspection
        func._sqltidy_rule_class = PluginRule
        func._sqltidy_rule = True

        return func

    return decorator


def register_rule_class(rule_class: type):
    """
    Register a rule class directly.

    Use this if you prefer to define classes rather than functions.

    Args:
        rule_class: A BaseRule subclass

    Example:
        from sqltidy.rules import register_rule_class

        class MyRule(BaseRule):
            rule_type = "tidy"
            order = 50

            def apply(self, tokens, ctx):
                return tokens

        register_rule_class(MyRule)
    """
    if not issubclass(rule_class, BaseRule):
        raise TypeError(f"{rule_class} must be a subclass of BaseRule")

    _RULE_PLUGIN_REGISTRY.append(rule_class)


def get_registered_rules() -> List[type]:
    """
    Get all registered rules.

    Returns:
        List of rule classes
    """
    return _RULE_PLUGIN_REGISTRY.copy()


def clear_rules():
    """Clear all registered rules and reset loaded files tracker."""
    _RULE_PLUGIN_REGISTRY.clear()
    _LOADED_PLUGIN_FILES.clear()


def load_rule_file(filepath: Union[str, Path]) -> List[type]:
    """
    Load rules from a Python file.

    The file should contain functions decorated with @sqltidy_rule
    or classes registered with register_rule_class().

    Args:
        filepath: Path to Python file containing rules

    Returns:
        List of rule classes that were loaded

    Raises:
        FileNotFoundError: If file doesn't exist
        ImportError: If file can't be imported

    Example:
        from sqltidy.rules import load_rule_file

        # Load rules from file
        rules = load_rule_file('my_rules.py')

        # Add to formatter
        formatter.rules.extend([r() for r in rules])
    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"rule file not found: {filepath}")

    # Track rules before loading
    before_count = len(_RULE_PLUGIN_REGISTRY)

    # Load the module
    spec = importlib.util.spec_from_file_location(
        f"sqltidy_rule_{filepath.stem}", filepath
    )

    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load rule file: {filepath}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module

    try:
        spec.loader.exec_module(module)
    except Exception as e:
        raise ImportError(f"Error loading rule file {filepath}: {e}") from e

    # Return newly registered rules
    new_rules = _RULE_PLUGIN_REGISTRY[before_count:]

    return new_rules


def load_rules_from_directory(directory: Union[str, Path]) -> List[type]:
    """
    Load all rule files from a directory.

    Searches for all .py files in the directory and loads them as rules.

    Args:
        directory: Path to directory containing rule files

    Returns:
        List of all rule classes that were loaded

    Example:
        from sqltidy.rules import load_rules_from_directory

        # Load all rules from directory
        rules = load_rules_from_directory('~/.sqltidy/rules')

        # Add to formatter
        formatter.rules.extend([r() for r in rules])
    """
    directory = Path(directory).expanduser()

    if not directory.exists():
        raise FileNotFoundError(f"rule directory not found: {directory}")

    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")

    all_rules = []

    for filepath in directory.glob("*.py"):
        if filepath.name.startswith("_"):
            continue  # Skip private files

        try:
            rules = load_rule_file(filepath)
            all_rules.extend(rules)
        except Exception as e:
            print(f"Warning: Could not load rule {filepath}: {e}")

    return all_rules


def load_rules_module(module_name: str) -> List[type]:
    """
    Load rules from an installed Python module.

    Args:
        module_name: Name of Python module to import

    Returns:
        List of rule classes that were loaded

    Example:
        from sqltidy.rules import load_rule_module

        # Load from installed package
        rules = load_rule_module('my_company.sqltidy_rules')
    """
    before_count = len(_RULE_PLUGIN_REGISTRY)

    try:
        importlib.import_module(module_name)
    except ImportError as e:
        raise ImportError(f"Could not import module {module_name}: {e}") from e

    # Return newly registered rules
    new_rules = _RULE_PLUGIN_REGISTRY[before_count:]

    return new_rules


def create_rule_formatter(
    config=None,
    rule_files: Optional[List[Union[str, Path]]] = None,
    rule_dirs: Optional[List[Union[str, Path]]] = None,
    rule_modules: Optional[List[str]] = None,
):
    """
    Create a SQLFormatter with rules loaded.

    Convenience function that creates a formatter and loads all specified rules.

    Args:
        config: SQLTidyConfig
        rule_files: List of rule file paths to load
        rule_dirs: List of rule directories to load
        rule_modules: List of module names to import

    Returns:
        SQLFormatter with rules loaded

    Example:
        from sqltidy.rules import create_rule_formatter
        from sqltidy.rulebook import SQLTidyConfig

        formatter = create_rule_formatter(
            config=SQLTidyConfig(dialect='postgresql'),
            rule_files=['my_rules.py'],
            rule_dirs=['~/.sqltidy/rules']
        )

        result = formatter.format(sql)
    """
    from sqltidy.core import SQLFormatter
    from sqltidy.rulebook import SQLTidyConfig

    formatter = SQLFormatter(config or SQLTidyConfig())

    # Load rules from files
    if rule_files:
        for filepath in rule_files:
            try:
                rules = load_rule_file(filepath)
                formatter.rules.extend([p() for p in rules])
            except Exception as e:
                print(f"Warning: Could not load rule file {filepath}: {e}")

    # Load rules from directories
    if rule_dirs:
        for directory in rule_dirs:
            try:
                rules = load_rules_from_directory(directory)
                formatter.rules.extend([p() for p in rules])
            except Exception as e:
                print(f"Warning: Could not load rules from {directory}: {e}")

    # Load rules from modules
    if rule_modules:
        for module_name in rule_modules:
            try:
                # Note: This functionality needs to be implemented
                # rules = load_rule_module(module_name)
                # formatter.rules.extend([p() for p in rules])
                pass
            except Exception as e:
                print(f"Warning: Could not load rule module {module_name}: {e}")

    return formatter


# Convenience aliases for backwards compatibility
rule = sqltidy_rule  # Shorter alias
register = register_rule_class  # Shorter alias
plugin = sqltidy_rule  # Backwards compatibility
sqltidy_plugin = sqltidy_rule  # Backwards compatibility
get_registered_plugins = get_registered_rules  # Backwards compatibility
clear_plugins = clear_rules  # Backwards compatibility
load_plugin_file = load_rule_file  # Backwards compatibility
load_plugins_from_directory = load_rules_from_directory  # Backwards compatibility
create_plugin_formatter = create_rule_formatter  # Backwards compatibility
