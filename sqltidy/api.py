from typing import Optional, Union
from pathlib import Path
from .rulebook import SQLTidyConfig, SUPPORTED_DIALECTS
from .core import SQLFormatter
from .generator import (
    get_bundled_rulebook_path,
    load_rulebook_file,
    get_user_rulebooks_dir,
)


"""API utilities for formatting SQL.

The CLI constructs and passes `SQLTidyConfig` explicitly. For library users
calling these functions without a config, `_format_sql` will resolve a config
by checking the user's rulebook, bundled rulebook, or generating defaults.
"""

# Removed runtime rule registration from API. Plugins are loaded automatically
# from the user's rules directory via the plugins system.


def _format_sql(
    sql: str,
    config: Optional[SQLTidyConfig] = None,
    dialect: Optional[str] = None,
    rule_type: Optional[str] = None,
    return_metadata: bool = False,
) -> Union[str, dict]:
    """
    Internal function to format SQL with specified rule type.

    Args:
        sql (str): The SQL string to format.
        config (SQLTidyConfig, optional): Formatter configuration. If not provided,
            will use dialect parameter or default configuration.
        dialect (str, optional): SQL dialect shorthand. One of: 'sqlserver', 'postgresql',
            'mysql', 'oracle', 'sqlite'. Ignored if config is provided.
        rule_type (str, optional): Filter rules by type ('tidy' or 'rewrite'). None loads all.
        return_metadata (bool, optional): If True, return dict with 'sql' and 'applied_rules'.

    Returns:
        str or dict: Formatted SQL string, or metadata dict if return_metadata=True.

    Raises:
        ValueError: If dialect is provided but not in SUPPORTED_DIALECTS.
    """
    # Resolve config from dialect if provided
    if config is None:
        # Default dialect
        dialect = dialect or "sqlserver"
        if dialect not in SUPPORTED_DIALECTS:
            raise ValueError(
                f"Unsupported dialect: '{dialect}'. "
                f"Must be one of: {', '.join(SUPPORTED_DIALECTS)}"
            )

        # Priority order:
        # 1. User's custom rulebook (~/.sqltidy/rulebooks/sqltidy_{dialect}.json)
        # 2. Bundled rulebook (sqltidy/rulebooks/sqltidy_{dialect}.json) if exists
        # 3. Auto-generate from rule metadata (fallback)
        user_rulebook_path = get_user_rulebooks_dir() / f"sqltidy_{dialect}.json"
        if user_rulebook_path.exists():
            rulebook_data = load_rulebook_file(str(user_rulebook_path))
            config = SQLTidyConfig.from_dict(rulebook_data)
        else:
            bundled_path = get_bundled_rulebook_path(dialect)
            if bundled_path.exists():
                rulebook_data = load_rulebook_file(str(bundled_path))
                config = SQLTidyConfig.from_dict(rulebook_data)
            else:
                from .config_schema import generate_dialect_config

                config_dict = generate_dialect_config(dialect, include_plugins=False)
                config = SQLTidyConfig.from_dict(config_dict)

    formatter = SQLFormatter(config=config, rule_type=rule_type)

    # Auto-load user plugin rules and inject them into the formatter
    # so CLI "rules add" continues to work without API runtime registration.
    try:
        from .plugins import auto_load_user_rules, get_registered_rules

        auto_load_user_rules()
        for rule_cls in get_registered_rules():
            rule = rule_cls()
            if rule_type is None or getattr(rule, "rule_type", None) == rule_type:
                formatter.rules.append(rule)
    except Exception as e:
        # Be resilient: if plugin loading fails, continue with built-in rules
        import logging
        logging.debug(f"Failed to load user plugins: {e}")

    return formatter.format(sql, return_metadata=return_metadata)


def tidy_sql(
    sql: str,
    dialect_or_config: Union[str, SQLTidyConfig, None] = None,
    config: Optional[SQLTidyConfig] = None,
    dialect: Optional[str] = None,
) -> str:
    """
    Apply formatting (tidy) rules to SQL without structural transformations.

    This function only applies cosmetic formatting rules like keyword casing,
    indentation, and whitespace normalization. It does not modify the SQL structure.

    Args:
        sql (str): The SQL string to format.
        dialect_or_config (str or SQLTidyConfig): SQL dialect name or config object (2nd positional).
        config (SQLTidyConfig, optional): Custom configuration.
        dialect (str, optional): SQL dialect (if not using dialect_or_config).

    Returns:
        str: Formatted SQL string.

    Example:
        >>> sql = "select name,email from users where active=1"
        >>> tidy_sql(sql, dialect='postgresql')
        'select\n    name\n    ,email\nfrom users\nwhere active=1'
        >>> tidy_sql(sql, config=SQLTidyConfig(dialect='postgresql'))
        'select\n    name\n    ,email\nfrom users\nwhere active=1'
    """
    # Handle both positional config and named dialect
    if dialect_or_config is not None:
        if isinstance(dialect_or_config, SQLTidyConfig):
            config = dialect_or_config
            dialect = None
        else:
            dialect = dialect_or_config

    # Default dialect
    if dialect is None and config is None:
        dialect = "sqlserver"

    return _format_sql(sql, config=config, dialect=dialect, rule_type="tidy")


def rewrite_sql(
    sql: str,
    dialect_or_config: Union[str, SQLTidyConfig, None] = None,
    config: Optional[SQLTidyConfig] = None,
    dialect: Optional[str] = None,
) -> str:
    """
    Apply transformation (rewrite) rules to SQL.

    This function applies structural transformations like converting subqueries to CTEs
    or standardizing alias styles. It does not apply formatting rules.

    Args:
        sql (str): The SQL string to transform.
        dialect_or_config (str or SQLTidyConfig): SQL dialect name or config object (2nd positional).
        config (SQLTidyConfig, optional): Custom configuration.
        dialect (str, optional): SQL dialect (if not using dialect_or_config).

    Returns:
        str: Transformed SQL string.

    Example:
        >>> sql = "SELECT (SELECT COUNT(*) FROM users) as total FROM orders"
        >>> rewrite_sql(sql)
        'WITH cte_1 AS (SELECT COUNT(*) FROM users) SELECT total FROM orders'
    """
    # Handle both positional config and named dialect
    if dialect_or_config is not None:
        if isinstance(dialect_or_config, SQLTidyConfig):
            config = dialect_or_config
            dialect = None
        else:
            dialect = dialect_or_config

    # Default dialect
    if dialect is None and config is None:
        dialect = "sqlserver"

    return _format_sql(sql, config=config, dialect=dialect, rule_type="rewrite")


def tidy_and_rewrite_sql(
    sql: str,
    dialect_or_config: Union[str, SQLTidyConfig, None] = None,
    config: Optional[SQLTidyConfig] = None,
    dialect: Optional[str] = None,
) -> str:
    """
    Apply both transformation and formatting rules to SQL.

    This function first applies rewrite rules (structural transformations), then
    applies tidy rules (formatting). This is equivalent to running rewrite_sql()
    followed by tidy_sql().

    Args:
        sql (str): The SQL string to transform and format.
        dialect_or_config (str or SQLTidyConfig): SQL dialect name or config object.
            Can be passed as 2nd positional arg.
        config (SQLTidyConfig, optional): Custom configuration.
        dialect (str, optional): SQL dialect (if not using dialect_or_config).

    Returns:
        str: Transformed and formatted SQL string.

    Example:
        >>> sql = "select (select count(*) from users) as total from orders"
        >>> tidy_and_rewrite_sql(sql, dialect='postgresql')
        'with cte_1 as (\n    select count(*)\n    from users\n)\nselect\n    total\nfrom orders'
    """
    # Handle both positional config and named dialect
    if dialect_or_config is not None:
        if isinstance(dialect_or_config, SQLTidyConfig):
            config = dialect_or_config
            dialect = None
        else:
            dialect = dialect_or_config

    # Default dialect
    if dialect is None and config is None:
        dialect = "sqlserver"

    # First apply rewrite rules
    sql = _format_sql(sql, config=config, dialect=dialect, rule_type="rewrite")
    # Then apply tidy rules
    sql = _format_sql(sql, config=config, dialect=dialect, rule_type="tidy")
    return sql


def format_sql_file(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    config: Optional[SQLTidyConfig] = None,
    dialect: Optional[str] = None,
    in_place: bool = True,
) -> None:
    """
    Format a SQL file and optionally save to a different location.

    Args:
        input_path (str | Path): Path to the input SQL file.
        output_path (str | Path, optional): Path to save formatted SQL. If None and in_place=True,
            overwrites input file. If None and in_place=False, does nothing.
        config (SQLTidyConfig, optional): Formatter configuration.
        dialect (str, optional): SQL dialect shorthand.
        in_place (bool): If True and output_path is None, overwrites input file. Default True.

    Raises:
        FileNotFoundError: If input file doesn't exist.
        ValueError: If dialect is invalid.
    """
    input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Read the SQL file
    with open(input_path, "r", encoding="utf-8") as f:
        sql = f.read()

    # Format the SQL
    formatted_sql = _format_sql(sql, config=config, dialect=dialect)

    # Determine output path
    if output_path is None:
        if in_place:
            output_path = input_path
        else:
            return
    else:
        output_path = Path(output_path)

    # Write the formatted SQL
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(formatted_sql)


def format_sql_folder(
    folder_path: Union[str, Path],
    output_folder: Optional[Union[str, Path]] = None,
    config: Optional[SQLTidyConfig] = None,
    dialect: Optional[str] = None,
    pattern: str = "*.sql",
    recursive: bool = False,
    in_place: bool = True,
) -> dict:
    """
    Format all SQL files in a folder.

    Args:
        folder_path (str | Path): Path to the folder containing SQL files.
        output_folder (str | Path, optional): Path to save formatted SQL files. If None and in_place=True,
            overwrites original files. If None and in_place=False, skips writing.
        config (SQLTidyConfig, optional): Formatter configuration.
        dialect (str, optional): SQL dialect shorthand.
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
    results = {"success": 0, "failed": 0, "total": len(sql_files), "errors": []}

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
                in_place=in_place,
            )

            results["success"] += 1

        except Exception as e:
            results["failed"] += 1
            results["errors"].append({"file": str(sql_file), "error": str(e)})

    return results
