"""
SQLite dialect tests.

Tests SQLite specific features:
- Keywords and functions
- Data types
- Syntax features (AUTOINCREMENT, etc.)
"""

from sqltidy.dialects import get_dialect
from sqltidy.tokenizer import is_keyword
from sqltidy import format_sql
from sqltidy.rulebook import SQLTidyConfig


class TestSQLiteDialect:
    """Test SQLite dialect registration and features."""

    def test_dialect_registered(self):
        """Test that SQLite dialect is registered."""
        dialect = get_dialect("sqlite")
        assert dialect is not None
        assert dialect.name == "sqlite"

    def test_sqlite_keywords(self):
        """Test SQLite specific keywords."""
        # SQLite specific
        assert is_keyword("AUTOINCREMENT", "sqlite")
        assert is_keyword("PRAGMA", "sqlite")

        # Common keywords
        assert is_keyword("SELECT", "sqlite")
        assert is_keyword("FROM", "sqlite")

    def test_sqlite_functions(self):
        """Test SQLite specific functions."""
        dialect = get_dialect("sqlite")

        assert "substr" in dialect.functions
        assert "length" in dialect.functions
        assert "datetime" in dialect.functions

    def test_sqlite_data_types(self):
        """Test SQLite data types."""
        dialect = get_dialect("sqlite")

        assert "text" in dialect.data_types
        assert "integer" in dialect.data_types
        assert "real" in dialect.data_types
        assert "blob" in dialect.data_types


class TestSQLiteFormatting:
    """Test SQLite specific formatting."""

    def test_lowercase_keywords_default(self):
        """Test that SQLite defaults to lowercase keywords."""
        sql = "SELECT id, name FROM users"
        config = SQLTidyConfig(
            dialect="sqlite",
            uppercase_keywords=None,  # Use default
            newline_after_select=False,
            compact=True,
        )
        result = format_sql(sql, config=config)

        assert "select" in result
        assert "from" in result

    def test_autoincrement(self):
        """Test AUTOINCREMENT keyword."""
        sql = "create table users (id integer primary key autoincrement, name text)"
        config = SQLTidyConfig(
            dialect="sqlite", newline_after_select=False, compact=True
        )
        result = format_sql(sql, config=config)

        assert "autoincrement" in result.lower()
