# Configuration for sqltidy
# Each dialect can have its own config file (e.g., sqltidy_sqlserver.json, sqltidy_postgresql.json)

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any
import json
from pathlib import Path


# Supported SQL dialects
SUPPORTED_DIALECTS = ['sqlserver', 'postgresql', 'mysql', 'oracle', 'sqlite']


@dataclass
class SQLTidyConfig:
    """
    Unified configuration for SQL formatting and transformation.
    Combines both tidy (formatting) and rewrite (transformation) rules.
    
    Each dialect should have its own config file for clarity.
    """
    dialect: str = 'sqlserver'  # SQL dialect: 'sqlserver', 'postgresql', 'mysql', 'oracle', 'sqlite'
    
    # ===== TIDY RULES (Formatting) =====
    
    # Keyword casing (None = use dialect default)
    # Defaults: SQL Server/Oracle=UPPERCASE, PostgreSQL/MySQL/SQLite=lowercase
    uppercase_keywords: Optional[bool] = None
    
    # Formatting options
    newline_after_select: bool = True
    compact: bool = True
    leading_commas: bool = True
    indent_select_columns: bool = True
    newline_on_join: bool = True  # Move ON keyword to newline after JOIN
    
    # JOIN pattern formatting - adds blank line before JOIN keywords
    newline_join_pattern: bool = False
    
    # Identifier quoting (disabled by default)
    quote_identifiers: bool = False
    
    # ===== REWRITE RULES (Transformations) =====
    
    enable_subquery_to_cte: bool = True
    enable_alias_style_abc: bool = False
    enable_alias_style_t_numeric: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SQLTidyConfig':
        """Create config from dictionary."""
        return cls(**data)
    
    @classmethod
    def from_file(cls, filepath: str) -> 'SQLTidyConfig':
        """Load config from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    def save(self, filepath: str) -> None:
        """Save config to JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def get_dialect_defaults(cls, dialect: str) -> 'SQLTidyConfig':
        """Get default configuration for a specific dialect."""
        if dialect not in SUPPORTED_DIALECTS:
            raise ValueError(f"Unsupported dialect: {dialect}. Must be one of {SUPPORTED_DIALECTS}")
        
        # Base defaults
        config = cls(dialect=dialect)
        
        # Dialect-specific adjustments
        if dialect in ('postgresql', 'mysql', 'sqlite'):
            # These dialects prefer lowercase keywords
            config.uppercase_keywords = False
        elif dialect in ('sqlserver', 'oracle'):
            # These dialects prefer uppercase keywords
            config.uppercase_keywords = True
        
        return config


