# Configuration for sqltidy
# Each dialect can have its own config file (e.g., sqltidy_sqlserver.json, sqltidy_postgresql.json)

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import json
from pathlib import Path


# Supported SQL dialects
SUPPORTED_DIALECTS = ['sqlserver', 'postgresql', 'mysql', 'oracle', 'sqlite']


@dataclass
class SQLTidyConfig:
    """
    Unified configuration for SQL formatting and transformation.
    Uses nested structure to organize tidy (formatting) and rewrite (transformation) rules.
    
    Fields are dynamically populated from rule declarations - no hardcoded fields.
    Each dialect should have its own config file for clarity.
    
    JSON structure:
    {
      "dialect": "postgresql",
      "tidy": {
        "uppercase_keywords": false,
        "leading_commas": true,
        ...
      },
      "rewrite": {
        "enable_subquery_to_cte": false,
        "enable_alias_style_abc": false,
        ...
      }
    }
    """
    dialect: str = 'sqlserver'
    tidy: Dict[str, Any] = field(default_factory=dict)
    rewrite: Dict[str, Any] = field(default_factory=dict)
    
    def __getattr__(self, name: str) -> Any:
        """
        Provide backward-compatible flat access to nested fields.
        
        Rules can access config.uppercase_keywords instead of config.tidy["uppercase_keywords"]
        Checks tidy first, then rewrite.
        """
        # Avoid infinite recursion for dataclass internals
        if name in ('tidy', 'rewrite', 'dialect'):
            raise AttributeError(f"Use direct access for '{name}'")
        
        # Check tidy section first
        if name in self.tidy:
            return self.tidy[name]
        
        # Then check rewrite section
        if name in self.rewrite:
            return self.rewrite[name]
        
        # Not found in either section
        raise AttributeError(f"Config has no field '{name}' in tidy or rewrite sections")
    
    def get_tidy(self, key: str, default=None) -> Any:
        """Get a tidy rule value with optional default."""
        return self.tidy.get(key, default)
    
    def get_rewrite(self, key: str, default=None) -> Any:
        """Get a rewrite rule value with optional default."""
        return self.rewrite.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to nested dictionary structure."""
        return {
            'dialect': self.dialect,
            'tidy': self.tidy.copy(),
            'rewrite': self.rewrite.copy()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SQLTidyConfig':
        """
        Create config from dictionary.
        
        Supports both nested (new) and flat (old) formats for migration.
        """
        # Check if it's the new nested format
        if 'tidy' in data or 'rewrite' in data:
            # New nested format
            return cls(
                dialect=data.get('dialect', 'sqlserver'),
                tidy=data.get('tidy', {}),
                rewrite=data.get('rewrite', {})
            )
        
        # Old flat format - migrate to nested
        tidy = {}
        rewrite = {}
        
        # List of known tidy fields (for migration from old configs)
        tidy_field_names = {
            'uppercase_keywords', 'newline_after_select', 'compact', 
            'leading_commas', 'indent_select_columns', 'newline_on_join',
            'newline_join_pattern', 'quote_identifiers'
        }
        
        # List of known rewrite fields (for migration from old configs)
        rewrite_field_names = {
            'enable_subquery_to_cte', 'enable_alias_style_abc', 
            'enable_alias_style_t_numeric'
        }
        
        for key, value in data.items():
            if key == 'dialect':
                continue
            elif key in tidy_field_names:
                tidy[key] = value
            elif key in rewrite_field_names:
                rewrite[key] = value
            else:
                # Unknown field - guess based on name prefix
                if key.startswith('enable_'):
                    rewrite[key] = value
                else:
                    tidy[key] = value
        
        return cls(
            dialect=data.get('dialect', 'sqlserver'),
            tidy=tidy,
            rewrite=rewrite
        )
    
    @classmethod
    def from_file(cls, filepath: str) -> 'SQLTidyConfig':
        """Load config from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    def save(self, filepath: str) -> None:
        """Save config to JSON file in nested format."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def get_dialect_defaults(cls, dialect: str) -> 'SQLTidyConfig':
        """
        Get default configuration for a specific dialect.
        
        Note: This returns an empty config. Use generate_dialect_config() 
        from config_schema.py to get a config populated from rule metadata.
        """
        if dialect not in SUPPORTED_DIALECTS:
            raise ValueError(f"Unsupported dialect: {dialect}. Must be one of {SUPPORTED_DIALECTS}")
        
        return cls(dialect=dialect, tidy={}, rewrite={})


