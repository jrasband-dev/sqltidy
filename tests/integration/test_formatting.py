"""
Integration tests for end-to-end SQL formatting.

Tests complete workflows from input SQL to formatted output.
"""
import pytest
from sqltidy import format_sql
from sqltidy.config import TidyConfig


class TestEndToEndFormatting:
    """Test complete formatting workflows."""
    
    def test_simple_select(self, simple_sql, default_config):
        """Test formatting a simple SELECT statement."""
        result = format_sql(simple_sql, config=default_config)
        
        assert result is not None
        assert len(result) > 0
        assert 'SELECT' in result or 'select' in result
    
    def test_complex_query(self, complex_sql, sqlserver_config):
        """Test formatting a complex query with joins and aggregations."""
        result = format_sql(complex_sql, config=sqlserver_config)
        
        assert 'SELECT' in result
        assert 'FROM' in result
        assert 'JOIN' in result or 'INNER' in result
        assert 'GROUP BY' in result or 'group by' in result
    
    def test_all_dialects_produce_output(self, simple_sql, all_dialects):
        """Test that all dialects can format SQL successfully."""
        config = TidyConfig(dialect=all_dialects)
        result = format_sql(simple_sql, config=config)
        
        assert result is not None
        assert len(result) > 0


class TestDialectConsistency:
    """Test consistent behavior across dialects."""
    
    def test_keyword_casing_by_dialect(self, simple_sql):
        """Test that keyword casing follows dialect conventions."""
        # SQL Server and Oracle: UPPERCASE
        for dialect in ['sqlserver', 'oracle']:
            config = TidyConfig(
                dialect=dialect,
                uppercase_keywords=None,
                newline_after_select=False,
                compact=True
            )
            result = format_sql(simple_sql, config=config)
            assert 'SELECT' in result
            assert 'FROM' in result
        
        # PostgreSQL, MySQL, SQLite: lowercase
        for dialect in ['postgresql', 'mysql', 'sqlite']:
            config = TidyConfig(
                dialect=dialect,
                uppercase_keywords=None,
                newline_after_select=False,
                compact=True
            )
            result = format_sql(simple_sql, config=config)
            assert 'select' in result
            assert 'from' in result
    
    def test_config_overrides_work(self, simple_sql):
        """Test that config overrides apply correctly."""
        # Force uppercase on PostgreSQL (normally lowercase)
        config = TidyConfig(
            dialect='postgresql',
            uppercase_keywords=True,
            newline_after_select=False,
            compact=True
        )
        result = format_sql(simple_sql, config=config)
        assert 'SELECT' in result
        
        # Force lowercase on SQL Server (normally uppercase)
        config = TidyConfig(
            dialect='sqlserver',
            uppercase_keywords=False,
            newline_after_select=False,
            compact=True
        )
        result = format_sql(simple_sql, config=config)
        assert 'select' in result


class TestFormattingOptions:
    """Test various formatting options."""
    
    def test_newline_after_select(self, simple_sql):
        """Test newline_after_select option."""
        config = TidyConfig(
            newline_after_select=True,
            uppercase_keywords=True
        )
        result = format_sql(simple_sql, config=config)
        
        # Should have newlines after SELECT
        assert '\n' in result
    
    def test_compact_whitespace(self):
        """Test compact whitespace option."""
        sql = "SELECT    id,     name   FROM    users"
        
        config = TidyConfig(compact=True, newline_after_select=False)
        result = format_sql(sql, config=config)
        
        # Should not have multiple consecutive spaces
        assert '  ' not in result or '\n' in result
    
    def test_leading_commas(self):
        """Test leading commas formatting."""
        sql = "select id, name, email from users"
        
        config = TidyConfig(
            leading_commas=True,
            newline_after_select=True,
            uppercase_keywords=False
        )
        result = format_sql(sql, config=config)
        
        # Should have commas at line start (after newline)
        lines = result.split('\n')
        comma_lines = [line for line in lines if line.strip().startswith(',')]
        assert len(comma_lines) > 0
    
    def test_quote_identifiers(self):
        """Test identifier quoting."""
        sql = "select id, name from users"
        
        # SQL Server: brackets
        config = TidyConfig(
            dialect='sqlserver',
            quote_identifiers=True,
            newline_after_select=False
        )
        result = format_sql(sql, config=config)
        assert '[' in result or ']' in result
        
        # MySQL: backticks
        config = TidyConfig(
            dialect='mysql',
            quote_identifiers=True,
            newline_after_select=False
        )
        result = format_sql(sql, config=config)
        assert '`' in result


class TestEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_empty_string(self):
        """Test formatting empty string."""
        result = format_sql("", config=TidyConfig())
        assert result == ""
    
    def test_whitespace_only(self):
        """Test formatting whitespace-only string."""
        result = format_sql("   \n  \t  ", config=TidyConfig())
        assert result.strip() == ""
    
    def test_single_keyword(self):
        """Test formatting single keyword."""
        result = format_sql("SELECT", config=TidyConfig())
        assert 'SELECT' in result or 'select' in result
    
    def test_preserves_literals(self):
        """Test that string literals are preserved."""
        sql = "SELECT 'John Doe' AS name"
        result = format_sql(sql, config=TidyConfig())
        
        assert 'John Doe' in result or 'John' in result
    
    def test_preserves_numbers(self):
        """Test that numbers are preserved."""
        sql = "SELECT id FROM users WHERE age > 25"
        result = format_sql(sql, config=TidyConfig(newline_after_select=False))
        
        assert '25' in result
