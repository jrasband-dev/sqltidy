# Default Rules

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TidyConfig:
    """
    Configuration for SQL formatting (tidy) rules.
    
    Dialect Support:
        Most options support None (use dialect default), True (enable), or False (disable).
    """
    dialect: str = 'sqlserver'  # SQL dialect: 'sqlserver', 'postgresql', 'mysql', 'oracle', 'sqlite'
    
    # Keyword casing (None = use dialect default)
    # Defaults: SQL Server/Oracle=UPPERCASE, PostgreSQL/MySQL/SQLite=lowercase
    uppercase_keywords: Optional[bool] = None
    
    # Formatting options
    newline_after_select: bool = True
    compact: bool = True
    leading_commas: bool = True
    indent_select_columns: bool = True
    
    # Identifier quoting (disabled by default)
    quote_identifiers: bool = False


@dataclass
class RewriteConfig:
    """Configuration for SQL transformation (rewrite) rules."""
    dialect: str = 'sqlserver'  # SQL dialect: 'sqlserver', 'postgresql', 'mysql', 'oracle', 'sqlite'
    enable_subquery_to_cte: bool = True
    enable_alias_style_abc: bool = False
    enable_alias_style_t_numeric: bool = False


