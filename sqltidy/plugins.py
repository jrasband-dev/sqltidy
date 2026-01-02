"""
Plugin system for SQLTidy.

Provides a decorator-based plugin registration system similar to Polars,
allowing users to easily extend SQLTidy with custom formatting rules.

Example:
    # my_plugin.py
    from sqltidy.plugins import sqltidy_plugin
    
    @sqltidy_plugin(rule_type="tidy", order=50)
    def remove_semicolons(tokens, ctx):
        '''Remove trailing semicolons.'''
        if tokens and tokens[-1] == ';':
            return tokens[:-1]
        return tokens
    
    # Use from CLI:
    # sqltidy format input.sql --plugin my_plugin.py
    
    # Or from Python:
    # from sqltidy.plugins import load_plugins
    # load_plugins('my_plugin.py')
"""

import importlib.util
import sys
from pathlib import Path
from typing import Callable, Optional, Set, List, Union
from sqltidy.rules.base import BaseRule


# Global registry of plugins
_PLUGIN_REGISTRY = []


def sqltidy_plugin(
    rule_type: str = "tidy",
    order: int = 50,
    supported_dialects: Optional[Set[str]] = None,
    name: Optional[str] = None
):
    """
    Decorator to register a function as a SQLTidy plugin rule.
    
    This decorator allows you to turn any function into a formatting rule
    without having to create a class or understand the internals.
    
    Args:
        rule_type: "tidy" (formatting) or "rewrite" (transformation)
        order: Execution order (lower runs first)
        supported_dialects: Set of dialects this rule applies to, or None for all
        name: Optional custom name for the rule class
    
    Returns:
        Decorator function
    
    Example:
        @sqltidy_plugin(rule_type="tidy", order=100)
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
        
        # Override apply method to call the function
        def apply(self, tokens, ctx):
            return func(tokens, ctx)
        
        PluginRule.apply = apply
        
        # Register the rule class
        _PLUGIN_REGISTRY.append(PluginRule)
        
        # Store reference on the function for introspection
        func._sqltidy_rule_class = PluginRule
        func._sqltidy_plugin = True
        
        return func
    
    return decorator


def register_rule_class(rule_class: type):
    """
    Register a rule class directly.
    
    Use this if you prefer to define classes rather than functions.
    
    Args:
        rule_class: A BaseRule subclass
    
    Example:
        from sqltidy.plugins import register_rule_class
        
        class MyRule(BaseRule):
            rule_type = "tidy"
            order = 50
            
            def apply(self, tokens, ctx):
                return tokens
        
        register_rule_class(MyRule)
    """
    if not issubclass(rule_class, BaseRule):
        raise TypeError(f"{rule_class} must be a subclass of BaseRule")
    
    _PLUGIN_REGISTRY.append(rule_class)


def get_registered_plugins() -> List[type]:
    """
    Get all registered plugin rules.
    
    Returns:
        List of rule classes
    """
    return _PLUGIN_REGISTRY.copy()


def clear_plugins():
    """Clear all registered plugins."""
    _PLUGIN_REGISTRY.clear()


def load_plugin_file(filepath: Union[str, Path]) -> List[type]:
    """
    Load plugins from a Python file.
    
    The file should contain functions decorated with @sqltidy_plugin
    or classes registered with register_rule_class().
    
    Args:
        filepath: Path to Python file containing plugins
    
    Returns:
        List of rule classes that were loaded
    
    Raises:
        FileNotFoundError: If file doesn't exist
        ImportError: If file can't be imported
    
    Example:
        from sqltidy.plugins import load_plugin_file
        
        # Load plugins from file
        rules = load_plugin_file('my_plugins.py')
        
        # Add to formatter
        formatter.rules.extend([r() for r in rules])
    """
    filepath = Path(filepath)
    
    if not filepath.exists():
        raise FileNotFoundError(f"Plugin file not found: {filepath}")
    
    # Track plugins before loading
    before_count = len(_PLUGIN_REGISTRY)
    
    # Load the module
    spec = importlib.util.spec_from_file_location(
        f"sqltidy_plugin_{filepath.stem}",
        filepath
    )
    
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load plugin file: {filepath}")
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        raise ImportError(f"Error loading plugin file {filepath}: {e}") from e
    
    # Return newly registered plugins
    new_plugins = _PLUGIN_REGISTRY[before_count:]
    
    return new_plugins


def load_plugins_from_directory(directory: Union[str, Path]) -> List[type]:
    """
    Load all plugin files from a directory.
    
    Searches for all .py files in the directory and loads them as plugins.
    
    Args:
        directory: Path to directory containing plugin files
    
    Returns:
        List of all rule classes that were loaded
    
    Example:
        from sqltidy.plugins import load_plugins_from_directory
        
        # Load all plugins from directory
        rules = load_plugins_from_directory('~/.sqltidy/plugins')
        
        # Add to formatter
        formatter.rules.extend([r() for r in rules])
    """
    directory = Path(directory).expanduser()
    
    if not directory.exists():
        raise FileNotFoundError(f"Plugin directory not found: {directory}")
    
    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")
    
    all_plugins = []
    
    for filepath in directory.glob("*.py"):
        if filepath.name.startswith("_"):
            continue  # Skip private files
        
        try:
            plugins = load_plugin_file(filepath)
            all_plugins.extend(plugins)
        except Exception as e:
            print(f"Warning: Could not load plugin {filepath}: {e}")
    
    return all_plugins


def load_plugin_module(module_name: str) -> List[type]:
    """
    Load plugins from an installed Python module.
    
    Args:
        module_name: Name of Python module to import
    
    Returns:
        List of rule classes that were loaded
    
    Example:
        from sqltidy.plugins import load_plugin_module
        
        # Load from installed package
        rules = load_plugin_module('my_company.sqltidy_plugins')
    """
    before_count = len(_PLUGIN_REGISTRY)
    
    try:
        importlib.import_module(module_name)
    except ImportError as e:
        raise ImportError(f"Could not import module {module_name}: {e}") from e
    
    # Return newly registered plugins
    new_plugins = _PLUGIN_REGISTRY[before_count:]
    
    return new_plugins


def create_plugin_formatter(
    config=None,
    plugin_files: Optional[List[Union[str, Path]]] = None,
    plugin_dirs: Optional[List[Union[str, Path]]] = None,
    plugin_modules: Optional[List[str]] = None
):
    """
    Create a SQLFormatter with plugins loaded.
    
    Convenience function that creates a formatter and loads all specified plugins.
    
    Args:
        config: SQLTidyConfig
        plugin_files: List of plugin file paths to load
        plugin_dirs: List of plugin directories to load
        plugin_modules: List of module names to import
    
    Returns:
        SQLFormatter with plugins loaded
    
    Example:
        from sqltidy.plugins import create_plugin_formatter
        from sqltidy.config import SQLTidyConfig
        
        formatter = create_plugin_formatter(
            config=SQLTidyConfig(dialect='postgresql'),
            plugin_files=['my_rules.py'],
            plugin_dirs=['~/.sqltidy/plugins']
        )
        
        result = formatter.format(sql)
    """
    from sqltidy.core import SQLFormatter
    from sqltidy.config import SQLTidyConfig
    
    formatter = SQLFormatter(config or SQLTidyConfig())
    
    # Load plugins from files
    if plugin_files:
        for filepath in plugin_files:
            try:
                plugins = load_plugin_file(filepath)
                formatter.rules.extend([p() for p in plugins])
            except Exception as e:
                print(f"Warning: Could not load plugin file {filepath}: {e}")
    
    # Load plugins from directories
    if plugin_dirs:
        for directory in plugin_dirs:
            try:
                plugins = load_plugins_from_directory(directory)
                formatter.rules.extend([p() for p in plugins])
            except Exception as e:
                print(f"Warning: Could not load plugins from {directory}: {e}")
    
    # Load plugins from modules
    if plugin_modules:
        for module_name in plugin_modules:
            try:
                plugins = load_plugin_module(module_name)
                formatter.rules.extend([p() for p in plugins])
            except Exception as e:
                print(f"Warning: Could not load plugin module {module_name}: {e}")
    
    return formatter


# Convenience aliases
plugin = sqltidy_plugin  # Shorter alias
register = register_rule_class  # Shorter alias
