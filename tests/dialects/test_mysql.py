"""
MySQL dialect tests.

Tests MySQL specific features:
- Keywords and functions
- Data types
- Syntax features (LIMIT, backticks, etc.)
"""

from sqltidy.dialects import get_dialect
from sqltidy.tokenizer import is_keyword
from sqltidy import format_sql
from sqltidy.rulebook import SQLTidyConfig


class TestMySQLDialect:
    """Test MySQL dialect registration and features."""

    def test_dialect_registered(self):
        """Test that MySQL dialect is registered."""
        dialect = get_dialect("mysql")
        assert dialect is not None
        assert dialect.name == "mysql"

    def test_mysql_keywords(self):
        """Test MySQL specific keywords."""
        # MySQL specific
        assert is_keyword("LIMIT", "mysql")
        assert is_keyword("REGEXP", "mysql")
        assert is_keyword(
            "AUTO_INCREMENT", "mysql"
        )  # MySQL uses AUTO_INCREMENT not AUTOINCREMENT

        # Common keywords
        assert is_keyword("SELECT", "mysql")
        assert is_keyword("FROM", "mysql")

    def test_mysql_functions(self):
        """Test MySQL specific functions."""
        dialect = get_dialect("mysql")

        assert "now" in dialect.functions
        assert "concat" in dialect.functions
        assert "substring" in dialect.functions

    def test_mysql_data_types(self):
        """Test MySQL data types."""
        dialect = get_dialect("mysql")

        assert "varchar" in dialect.data_types
        assert "int" in dialect.data_types
        assert "tinyint" in dialect.data_types
        assert "mediumtext" in dialect.data_types


class TestMySQLFormatting:
    """Test MySQL specific formatting."""

    def test_lowercase_keywords_default(self):
        """Test that MySQL defaults to lowercase keywords."""
        sql = "SELECT id, name FROM users"
        config = SQLTidyConfig(
            dialect="mysql",
            uppercase_keywords=None,  # Use default
            newline_after_select=False,
            compact=True,
        )
        result = format_sql(sql, config=config)

        assert "select" in result
        assert "from" in result

    def test_limit_clause(self):
        """Test LIMIT clause formatting."""
        sql = "select id from users limit 10"
        config = SQLTidyConfig(
            dialect="mysql", newline_after_select=False, compact=True
        )
        result = format_sql(sql, config=config)

        assert "limit" in result.lower()

    def test_backtick_identifiers(self):
        """Test backtick identifier quoting."""
        sql = "select id from users"
        config = SQLTidyConfig(
            dialect="mysql", quote_identifiers=True, newline_after_select=False
        )
        result = format_sql(sql, config=config)

        # MySQL uses backticks
        assert "`" in result
