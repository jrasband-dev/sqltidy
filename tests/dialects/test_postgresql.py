"""
PostgreSQL dialect tests.

Tests PostgreSQL specific features:
- Keywords and functions
- Data types
- Syntax features (RETURNING, ILIKE, etc.)
"""
import pytest
from sqltidy.dialects import get_dialect
from sqltidy.tokenizer import is_keyword
from sqltidy import format_sql
from sqltidy.rulebook import SQLTidyConfig


class TestPostgreSQLDialect:
    """Test PostgreSQL dialect registration and features."""
    
    def test_dialect_registered(self):
        """Test that PostgreSQL dialect is registered."""
        dialect = get_dialect('postgresql')
        assert dialect is not None
        assert dialect.name == 'postgresql'
    
    def test_postgresql_keywords(self):
        """Test PostgreSQL specific keywords."""
        # PostgreSQL specific
        assert is_keyword('RETURNING', 'postgresql')
        assert is_keyword('ILIKE', 'postgresql')
        assert is_keyword('SERIAL', 'postgresql')
        assert is_keyword('BIGSERIAL', 'postgresql')
        
        # Common keywords
        assert is_keyword('SELECT', 'postgresql')
        assert is_keyword('FROM', 'postgresql')
    
    def test_postgresql_functions(self):
        """Test PostgreSQL specific functions."""
        dialect = get_dialect('postgresql')
        
        assert 'now' in dialect.functions
        assert 'coalesce' in dialect.functions
        assert 'array_agg' in dialect.functions
    
    def test_postgresql_data_types(self):
        """Test PostgreSQL data types."""
        dialect = get_dialect('postgresql')
        
        assert 'text' in dialect.data_types
        assert 'json' in dialect.data_types
        assert 'jsonb' in dialect.data_types
        assert 'uuid' in dialect.data_types
        assert 'serial' in dialect.data_types


class TestPostgreSQLFormatting:
    """Test PostgreSQL specific formatting."""
    
    def test_lowercase_keywords_default(self):
        """Test that PostgreSQL defaults to lowercase keywords."""
        sql = "SELECT id, name FROM users"
        config = SQLTidyConfig(
            dialect='postgresql',
            uppercase_keywords=None,  # Use default
            newline_after_select=False,
            compact=True
        )
        result = format_sql(sql, config=config)
        
        assert 'select' in result
        assert 'from' in result
    
    def test_returning_clause(self):
        """Test RETURNING clause formatting."""
        sql = "insert into users (name) values ('John') returning id"
        config = SQLTidyConfig(
            dialect='postgresql',
            newline_after_select=False,
            compact=True
        )
        result = format_sql(sql, config=config)
        
        assert 'returning' in result.lower()
