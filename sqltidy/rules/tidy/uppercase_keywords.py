from typing import Optional
from ..base import BaseRule
from sqltidy.tokenizer import is_keyword


class UppercaseKeywordsRule(BaseRule):
    """
    Convert SQL keywords to uppercase or lowercase based on dialect conventions.
    
    Dialect Defaults:
        - SQL Server: UPPERCASE (T-SQL convention)
        - Oracle: UPPERCASE (PL/SQL convention)
        - PostgreSQL: lowercase (community convention)
        - MySQL: lowercase (community convention)
        - SQLite: lowercase (community convention)
    
    Configuration:
        - Set uppercase_keywords=True to force uppercase
        - Set uppercase_keywords=False to force lowercase
        - Set uppercase_keywords=None (or omit) to use dialect default
    """
    rule_type = "tidy"
    order = 10
    
    # Dialect-specific defaults for keyword casing
    DIALECT_DEFAULTS = {
        'sqlserver': True,    # T-SQL convention: UPPERCASE
        'oracle': True,       # Oracle/PL-SQL convention: UPPERCASE
        'postgresql': False,  # PostgreSQL convention: lowercase
        'mysql': False,       # MySQL convention: lowercase
        'sqlite': False,      # SQLite convention: lowercase
    }
    
    def _should_uppercase(self, ctx) -> bool:
        """Determine if keywords should be uppercase based on config and dialect."""
        # Check if user explicitly set uppercase_keywords
        uppercase = getattr(ctx.config, "uppercase_keywords", None)
        
        if uppercase is not None:
            # User explicitly set it, use their preference
            return uppercase
        
        # Use dialect default
        dialect = ctx.config.dialect
        return self.DIALECT_DEFAULTS.get(dialect, True)  # Default to True for unknown dialects
    
    def apply(self, tokens, ctx):
        should_uppercase = self._should_uppercase(ctx)
        dialect = ctx.config.dialect
        
        if should_uppercase:
            return [t.upper() if is_keyword(t, dialect) else t for t in tokens]
        else:
            return [t.lower() if is_keyword(t, dialect) else t for t in tokens]


