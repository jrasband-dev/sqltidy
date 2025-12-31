"""
Unit tests for configuration classes.

Tests:
- TidyConfig defaults and validation
- RewriteConfig defaults and validation
- Dialect-specific config behavior
"""
import pytest
from sqltidy.config import TidyConfig, RewriteConfig


class TestTidyConfig:
    """Test TidyConfig class."""
    
    def test_default_values(self):
        """Test that defaults are set correctly."""
        config = TidyConfig()
        
        assert config.dialect == 'sqlserver'
        assert config.uppercase_keywords is None  # Use dialect default
        assert config.newline_after_select is True
        assert config.compact is True
        assert config.leading_commas is True
        assert config.indent_select_columns is True
        assert config.quote_identifiers is False
    
    def test_custom_dialect(self):
        """Test setting custom dialect."""
        config = TidyConfig(dialect='postgresql')
        assert config.dialect == 'postgresql'
        
        config = TidyConfig(dialect='mysql')
        assert config.dialect == 'mysql'
        
        config = TidyConfig(dialect='oracle')
        assert config.dialect == 'oracle'
        
        config = TidyConfig(dialect='sqlite')
        assert config.dialect == 'sqlite'
    
    def test_uppercase_keywords_override(self):
        """Test explicit uppercase_keywords setting."""
        # Explicit True
        config = TidyConfig(dialect='postgresql', uppercase_keywords=True)
        assert config.uppercase_keywords is True
        
        # Explicit False
        config = TidyConfig(dialect='sqlserver', uppercase_keywords=False)
        assert config.uppercase_keywords is False
        
        # None (use dialect default)
        config = TidyConfig(dialect='sqlserver', uppercase_keywords=None)
        assert config.uppercase_keywords is None
    
    def test_formatting_options(self):
        """Test formatting option settings."""
        config = TidyConfig(
            newline_after_select=False,
            compact=False,
            leading_commas=False,
            indent_select_columns=False
        )
        
        assert config.newline_after_select is False
        assert config.compact is False
        assert config.leading_commas is False
        assert config.indent_select_columns is False
    
    def test_quote_identifiers(self):
        """Test quote_identifiers option."""
        config = TidyConfig(quote_identifiers=True)
        assert config.quote_identifiers is True
        
        config = TidyConfig(quote_identifiers=False)
        assert config.quote_identifiers is False


class TestRewriteConfig:
    """Test RewriteConfig class."""
    
    def test_default_values(self):
        """Test that defaults are set correctly."""
        config = RewriteConfig()
        
        assert config.dialect == 'sqlserver'
        assert config.enable_subquery_to_cte is True
        assert config.enable_alias_style_abc is False
        assert config.enable_alias_style_t_numeric is False
    
    def test_custom_dialect(self):
        """Test setting custom dialect."""
        config = RewriteConfig(dialect='postgresql')
        assert config.dialect == 'postgresql'
    
    def test_rewrite_rules(self):
        """Test enabling/disabling rewrite rules."""
        config = RewriteConfig(
            enable_subquery_to_cte=False,
            enable_alias_style_abc=True,
            enable_alias_style_t_numeric=True
        )
        
        assert config.enable_subquery_to_cte is False
        assert config.enable_alias_style_abc is True
        assert config.enable_alias_style_t_numeric is True
