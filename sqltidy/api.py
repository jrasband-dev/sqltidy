from typing import List, Optional
from .config import TidyConfig
from .rules.base import BaseRule
from .core import SQLFormatter

# In-memory list to hold extra plugin rules registered at runtime
_extra_plugins = []

def register_plugin(rule: BaseRule):
    """
    Register a plugin rule at runtime.

    Args:
        rule (BaseRule): An instance of a rule to apply.
    """
    if not isinstance(rule, BaseRule):
        raise TypeError("Plugin must be an instance of BaseRule")
    _extra_plugins.append(rule)

def clear_plugins():
    """
    Clear all runtime-registered plugin rules.
    """
    _extra_plugins.clear()

def format_sql(sql: str, config: TidyConfig = None, custom_rules: Optional[List[BaseRule]] = None) -> str:
    """
    Format a SQL string using all registered rules, including runtime plugins.

    Args:
        sql (str): The SQL string to format.
        config (TidyConfig, optional): Formatter configuration.
        custom_rules (List[BaseRule], optional): Additional custom rules to apply.

    Returns:
        str: Formatted SQL string.
    """
    formatter = SQLFormatter(config=config)

    # Inject runtime plugins into the formatter
    formatter.rules.extend(_extra_plugins)
    
    # Inject custom rules if provided
    if custom_rules:
        formatter.rules.extend(custom_rules)

    return formatter.format(sql)
