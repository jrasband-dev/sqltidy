from typing import List, Union, Optional
from ..base import BaseRule, ConfigField, FormatterContext
from sqltidy.tokenizer import Token, TokenGroup, TokenType, is_keyword


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
    supports_token_objects = True  # Use Token-based API
    
    # Self-describing configuration
    config_fields = {
        "uppercase_keywords": ConfigField(
            name="uppercase_keywords",
            default=None,  # None means use dialect default
            description="Convert SQL keywords to UPPERCASE (True) or lowercase (False)",
            field_type=Optional[bool],
            dialect_defaults={
                'sqlserver': True,
                'oracle': True,
                'postgresql': False,
                'mysql': False,
                'sqlite': False
            }
        )
    }
    
    # Dialect-specific defaults for keyword casing (kept for backwards compatibility)
    DIALECT_DEFAULTS = {
        'sqlserver': True,    # T-SQL convention: UPPERCASE
        'oracle': True,       # Oracle/PL-SQL convention: UPPERCASE
        'postgresql': False,  # PostgreSQL convention: lowercase
        'mysql': False,       # MySQL convention: lowercase
        'sqlite': False,      # SQLite convention: lowercase
    }
    
    def _should_uppercase(self, ctx: FormatterContext) -> bool:
        """Determine if keywords should be uppercase based on config and dialect."""
        # Check if user explicitly set uppercase_keywords
        uppercase = getattr(ctx.config, "uppercase_keywords", None)
        
        if uppercase is not None:
            # User explicitly set it, use their preference
            return uppercase
        
        # Use dialect default
        dialect = ctx.config.dialect
        return self.DIALECT_DEFAULTS.get(dialect, True)  # Default to True for unknown dialects
    
    def apply(self, tokens: List[Union[Token, TokenGroup]], ctx: FormatterContext) -> List[Union[Token, TokenGroup]]:
        """Apply keyword casing using Token objects."""
        should_uppercase = self._should_uppercase(ctx)
        dialect = ctx.config.dialect
        
        return self._process_tokens(tokens, should_uppercase, dialect)
    
    def _process_tokens(self, tokens: List[Union[Token, TokenGroup]], should_uppercase: bool, dialect: str) -> List[Union[Token, TokenGroup]]:
        """Recursively process tokens and convert keyword case."""
        result = []
        
        for token in tokens:
            if isinstance(token, Token):
                if token.type == TokenType.KEYWORD:
                    # Convert keyword case
                    new_value = token.value.upper() if should_uppercase else token.value.lower()
                    result.append(Token(new_value, token.type))
                else:
                    result.append(token)
            elif isinstance(token, TokenGroup):
                # Recursively process group contents
                processed_tokens = self._process_tokens(token.tokens, should_uppercase, dialect)
                result.append(TokenGroup(token.group_type, processed_tokens, token.name, token.metadata))
            else:
                result.append(token)
        
        return result


