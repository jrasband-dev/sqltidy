from typing import List, Optional, Union
from .rulebook import SQLTidyConfig, SUPPORTED_DIALECTS
from .rules.base import BaseRule
from .core import SQLFormatter
from .plugins import load_rule_file, load_rules_from_directory
from .generator import get_user_rules_dir, get_bundled_rulebook_path, load_rulebook_file, get_user_rulebooks_dir
from pathlib import Path

# In-memory list to hold extra rule rules registered at runtime
_extra_rules = []


def _load_config_for_dialect(dialect: str) -> SQLTidyConfig:
    """
    Load configuration for a specific dialect.
    Checks user rulebook first, then falls back to bundled rulebook.
    
    Args:
        dialect: SQL dialect name
        
    Returns:
        SQLTidyConfig: Loaded configuration
    """
    user_rulebook_path = get_user_rulebooks_dir() / f"sqltidy_{dialect}.json"
    if user_rulebook_path.exists():
        rulebook_data = load_rulebook_file(str(user_rulebook_path))
    else:
        rulebook_path = get_bundled_rulebook_path(dialect)
        rulebook_data = load_rulebook_file(str(rulebook_path))
    return SQLTidyConfig.from_dict(rulebook_data)

def register_rule(rule: BaseRule):
    """
    Register a rule at runtime.

    Args:
        rule (BaseRule): An instance of a rule to apply.
    """
    if not isinstance(rule, BaseRule):
        raise TypeError("Rule must be an instance of BaseRule")
    _extra_rules.append(rule)

def clear_rules():
    """
    Clear all runtime-registered rules.
    """
    _extra_rules.clear()

def format_sql(
    sql: str,
    config: Optional[SQLTidyConfig] = None,
    dialect: Optional[str] = None,
    custom_rules: Optional[List[BaseRule]] = None,
    rule_type: Optional[str] = None
) -> str:
    """
    Format a SQL string using all registered rules, including custom rules.

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
            config = _load_config_for_dialect(dialect)
        else:
            # Default to sqlserver
            config = _load_config_for_dialect('sqlserver')
    
    formatter = SQLFormatter(config=config, rule_type=rule_type)

    # Inject runtime rules into the formatter
    formatter.rules.extend(_extra_rules)
    
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


def load_user_rules() -> List[type]:
    """
    Load all rules from the user's rule plugin directory (~/.sqltidy/rules/).
    
    Returns:
        List[type]: List of rule classes found in user rules.
        
    Example:
        >>> rules = load_user_rules()
        >>> for rule_cls in rules:
        ...     register_rule(rule_cls())
    """
    rules_dir = get_user_rules_dir()
    
    if not rules_dir.exists():
        return []
    
    return load_rules_from_directory(str(rules_dir))


def load_rule(filepath: str) -> List[type]:
    """
    Load rules from a Python file.
    
    Args:
        filepath (str): Path to the rule Python file.
        
    Returns:
        List[type]: List of rule classes found in the rule file.
        
    Example:
        >>> rules = load_rule('my_custom_rules.py')
        >>> for rule_cls in rules:
        ...     register_rule(rule_cls())
    """
    return load_rule_file(filepath)


def format_sql_file(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    config: Optional[SQLTidyConfig] = None,
    dialect: Optional[str] = None,
    custom_rules: Optional[List[BaseRule]] = None,
    rule_type: Optional[str] = None,
    in_place: bool = True
) -> None:
    """
    Format a SQL file and optionally save to a different location.
    
    Args:
        input_path (str | Path): Path to the input SQL file.
        output_path (str | Path, optional): Path to save formatted SQL. If None and in_place=True,
            overwrites input file. If None and in_place=False, does nothing.
        config (SQLTidyConfig, optional): Formatter configuration.
        dialect (str, optional): SQL dialect shorthand.
        custom_rules (List[BaseRule], optional): Additional custom rules to apply.
        rule_type (str, optional): Filter rules by type ('tidy' or 'rewrite'). None loads all.
        in_place (bool): If True and output_path is None, overwrites input file. Default True.
        
    Raises:
        FileNotFoundError: If input file doesn't exist.
        ValueError: If dialect is invalid.
    """
    input_path = Path(input_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Read the SQL file
    with open(input_path, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    # Format the SQL
    formatted_sql = format_sql(
        sql,
        config=config,
        dialect=dialect,
        custom_rules=custom_rules,
        rule_type=rule_type
    )
    
    # Determine output path
    if output_path is None:
        if in_place:
            output_path = input_path
        else:
            return
    else:
        output_path = Path(output_path)
    
    # Write the formatted SQL
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(formatted_sql)


def format_sql_folder(
    folder_path: Union[str, Path],
    output_folder: Optional[Union[str, Path]] = None,
    config: Optional[SQLTidyConfig] = None,
    dialect: Optional[str] = None,
    custom_rules: Optional[List[BaseRule]] = None,
    rule_type: Optional[str] = None,
    pattern: str = "*.sql",
    recursive: bool = False,
    in_place: bool = True
) -> dict:
    """
    Format all SQL files in a folder.
    
    Args:
        folder_path (str | Path): Path to the folder containing SQL files.
        output_folder (str | Path, optional): Path to save formatted SQL files. If None and in_place=True,
            overwrites original files. If None and in_place=False, skips writing.
        config (SQLTidyConfig, optional): Formatter configuration.
        dialect (str, optional): SQL dialect shorthand.
        custom_rules (List[BaseRule], optional): Additional custom rules to apply.
        rule_type (str, optional): Filter rules by type ('tidy' or 'rewrite'). None loads all.
        pattern (str): Glob pattern for matching SQL files. Default "*.sql".
        recursive (bool): If True, search subdirectories recursively. Default False.
        in_place (bool): If True and output_folder is None, overwrites files. Default True.
        
    Returns:
        dict: Results with keys 'success', 'failed', 'total' and list of 'errors'.
        
    Raises:
        FileNotFoundError: If folder doesn't exist.
        ValueError: If dialect is invalid.
        
    Example:
        >>> results = format_sql_folder('sql_scripts', dialect='postgresql', recursive=True)
        >>> print(f"Formatted {results['success']}/{results['total']} files")
    """
    folder_path = Path(folder_path)
    
    if not folder_path.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")
    
    if not folder_path.is_dir():
        raise ValueError(f"Path is not a directory: {folder_path}")
    
    # Find all SQL files
    if recursive:
        sql_files = list(folder_path.rglob(pattern))
    else:
        sql_files = list(folder_path.glob(pattern))
    
    # Track results
    results = {
        'success': 0,
        'failed': 0,
        'total': len(sql_files),
        'errors': []
    }
    
    # Process each file
    for sql_file in sql_files:
        try:
            # Determine output path
            if output_folder is None:
                out_path = None if not in_place else sql_file
            else:
                output_folder_path = Path(output_folder)
                # Preserve relative directory structure
                rel_path = sql_file.relative_to(folder_path)
                out_path = output_folder_path / rel_path
                # Create parent directories if needed
                out_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Format the file
            format_sql_file(
                input_path=sql_file,
                output_path=out_path,
                config=config,
                dialect=dialect,
                custom_rules=custom_rules,
                rule_type=rule_type,
                in_place=in_place
            )
            
            results['success'] += 1
            
        except Exception as e:
            results['failed'] += 1
            results['errors'].append({
                'file': str(sql_file),
                'error': str(e)
            })
    
    return results
