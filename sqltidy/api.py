from typing import List, Optional, Union
from .config import SQLTidyConfig, SUPPORTED_DIALECTS
from .rules.base import BaseRule
from .core import SQLFormatter
from .plugins import load_plugin_file, load_plugins_from_directory
from .generator import get_user_plugins_dir
from pathlib import Path

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

def format_sql(
    sql: str,
    config: Optional[SQLTidyConfig] = None,
    dialect: Optional[str] = None,
    custom_rules: Optional[List[BaseRule]] = None,
    rule_type: Optional[str] = None
) -> str:
    """
    Format a SQL string using all registered rules, including runtime plugins.

    Args:
        sql (str): The SQL string to format.
        config (SQLTidyConfig, optional): Formatter configuration. If not provided,
            will use dialect parameter or default configuration.
        dialect (str, optional): SQL dialect shorthand. One of: 'sqlserver', 'postgresql',
            'mysql', 'oracle', 'sqlite'. Ignored if config is provided.
        custom_rules (List[BaseRule], optional): Additional custom rules to apply.
        rule_type (str, optional): Filter rules by type ('tidy' or 'rewrite'). None loads all.

    Returns:
        str: Formatted SQL string.
        
    Raises:
        ValueError: If dialect is provided but not in SUPPORTED_DIALECTS.
    """
    # Resolve config from dialect if provided
    if config is None:
        if dialect is not None:
            if dialect not in SUPPORTED_DIALECTS:
                raise ValueError(
                    f"Unsupported dialect: '{dialect}'. "
                    f"Must be one of: {', '.join(SUPPORTED_DIALECTS)}"
                )
            config = SQLTidyConfig.get_dialect_defaults(dialect)
        else:
            config = SQLTidyConfig()
    
    formatter = SQLFormatter(config=config, rule_type=rule_type)

    # Inject runtime plugins into the formatter
    formatter.rules.extend(_extra_plugins)
    
    # Inject custom rules if provided
    if custom_rules:
        formatter.rules.extend(custom_rules)

    return formatter.format(sql)


def tidy_sql(sql: str, dialect: str = 'sqlserver', config: Optional[SQLTidyConfig] = None) -> str:
    """
    Apply formatting (tidy) rules to SQL without structural transformations.
    
    This function only applies cosmetic formatting rules like keyword casing,
    indentation, and whitespace normalization. It does not modify the SQL structure.

    Args:
        sql (str): The SQL string to format.
        dialect (str): SQL dialect. One of: 'sqlserver', 'postgresql', 'mysql',
            'oracle', 'sqlite'. Default is 'sqlserver'.
        config (SQLTidyConfig, optional): Custom configuration. If provided, dialect is ignored.

    Returns:
        str: Formatted SQL string.
        
    Example:
        >>> sql = "select name,email from users where active=1"
        >>> tidy_sql(sql, dialect='postgresql')
        'select\n    name\n    ,email\nfrom users\nwhere active=1'
    """
    return format_sql(sql, config=config, dialect=dialect, rule_type='tidy')


def rewrite_sql(sql: str, dialect: str = 'sqlserver', config: Optional[SQLTidyConfig] = None) -> str:
    """
    Apply transformation (rewrite) rules to SQL.
    
    This function applies structural transformations like converting subqueries to CTEs
    or standardizing alias styles. It does not apply formatting rules.

    Args:
        sql (str): The SQL string to transform.
        dialect (str): SQL dialect. One of: 'sqlserver', 'postgresql', 'mysql',
            'oracle', 'sqlite'. Default is 'sqlserver'.
        config (SQLTidyConfig, optional): Custom configuration. If provided, dialect is ignored.

    Returns:
        str: Transformed SQL string.
        
    Example:
        >>> sql = "SELECT (SELECT COUNT(*) FROM users) as total FROM orders"
        >>> rewrite_sql(sql)
        'WITH cte_1 AS (SELECT COUNT(*) FROM users) SELECT total FROM orders'
    """
    return format_sql(sql, config=config, dialect=dialect, rule_type='rewrite')


def tidy_and_rewrite_sql(
    sql: str,
    dialect: str = 'sqlserver',
    config: Optional[SQLTidyConfig] = None
) -> str:
    """
    Apply both transformation and formatting rules to SQL.
    
    This function first applies rewrite rules (structural transformations), then
    applies tidy rules (formatting). This is equivalent to running rewrite_sql()
    followed by tidy_sql().

    Args:
        sql (str): The SQL string to transform and format.
        dialect (str): SQL dialect. One of: 'sqlserver', 'postgresql', 'mysql',
            'oracle', 'sqlite'. Default is 'sqlserver'.
        config (SQLTidyConfig, optional): Custom configuration. If provided, dialect is ignored.

    Returns:
        str: Transformed and formatted SQL string.
        
    Example:
        >>> sql = "select (select count(*) from users) as total from orders"
        >>> tidy_and_rewrite_sql(sql, dialect='postgresql')
        'with cte_1 as (\n    select count(*)\n    from users\n)\nselect\n    total\nfrom orders'
    """
    # First apply rewrite rules
    sql = format_sql(sql, config=config, dialect=dialect, rule_type='rewrite')
    # Then apply tidy rules
    sql = format_sql(sql, config=config, dialect=dialect, rule_type='tidy')
    return sql


def load_user_plugins() -> List[type]:
    """
    Load all plugins from the user's plugin directory (~/.sqltidy/plugins/).
    
    Returns:
        List[type]: List of rule classes found in user plugins.
        
    Example:
        >>> rules = load_user_plugins()
        >>> for rule_cls in rules:
        ...     register_plugin(rule_cls())
    """
    plugins_dir = get_user_plugins_dir()
    
    if not plugins_dir.exists():
        return []
    
    return load_plugins_from_directory(str(plugins_dir))


def load_plugin(filepath: str) -> List[type]:
    """
    Load plugin rules from a Python file.
    
    Args:
        filepath (str): Path to the plugin Python file.
        
    Returns:
        List[type]: List of rule classes found in the plugin file.
        
    Example:
        >>> rules = load_plugin('my_custom_rules.py')
        >>> for rule_cls in rules:
        ...     register_plugin(rule_cls())
    """
    return load_plugin_file(filepath)
