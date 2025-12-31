"""
SQL Server dialect tests.

Tests SQL Server/T-SQL specific features:
- Keywords and functions
- Data types
- Syntax features (TOP, WITH (NOLOCK), etc.)
"""
import pytest
from sqltidy.dialects import get_dialect
from sqltidy.tokenizer import is_keyword
from sqltidy import format_sql
from sqltidy.config import TidyConfig


class TestSQLServerDialect:
    """Test SQL Server dialect registration and features."""
    
    def test_dialect_registered(self):
        """Test that SQL Server dialect is registered."""
        dialect = get_dialect('sqlserver')
        assert dialect is not None
        assert dialect.name == 'sqlserver'
    
    def test_sqlserver_keywords(self):
        """Test SQL Server specific keywords."""
        # T-SQL specific
        assert is_keyword('NOLOCK', 'sqlserver')
        assert is_keyword('READUNCOMMITTED', 'sqlserver')
        assert is_keyword('OPTION', 'sqlserver')
        # MAXDOP is a hint option, not a keyword itself
        
        # Common keywords
        assert is_keyword('SELECT', 'sqlserver')
        assert is_keyword('FROM', 'sqlserver')
        assert is_keyword('WHERE', 'sqlserver')
    
    def test_sqlserver_functions(self):
        """Test SQL Server specific functions."""
        dialect = get_dialect('sqlserver')
        
        assert 'getdate' in dialect.functions
        assert 'newid' in dialect.functions
        assert 'row_number' in dialect.functions
        assert 'isnull' in dialect.functions
    
    def test_sqlserver_data_types(self):
        """Test SQL Server data types."""
        dialect = get_dialect('sqlserver')
        
        assert 'varchar' in dialect.data_types
        assert 'nvarchar' in dialect.data_types
        assert 'int' in dialect.data_types
        assert 'datetime' in dialect.data_types
        assert 'uniqueidentifier' in dialect.data_types


class TestSQLServerFormatting:
    """Test SQL Server specific formatting."""
    
    def test_uppercase_keywords_default(self):
        """Test that SQL Server defaults to uppercase keywords."""
        sql = "select id, name from users"
        config = TidyConfig(
            dialect='sqlserver',
            uppercase_keywords=None,  # Use default
            newline_after_select=False,
            compact=True
        )
        result = format_sql(sql, config=config)
        
        assert 'SELECT' in result
        assert 'FROM' in result
    
    def test_top_keyword_formatting(self):
        """Test TOP keyword formatting."""
        sql = "select top 10 id from users"
        config = TidyConfig(dialect='sqlserver')
        result = format_sql(sql, config=config)
        
        assert 'TOP' in result.upper()
    
    def test_with_nolock_hint(self):
        """Test WITH (NOLOCK) table hints."""
        sql = "select id from users with (nolock)"
        config = TidyConfig(
            dialect='sqlserver',
            newline_after_select=False,
            compact=True
        )
        result = format_sql(sql, config=config)
        
        assert 'NOLOCK' in result.upper()
