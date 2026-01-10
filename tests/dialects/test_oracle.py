"""
Oracle dialect tests.

Tests Oracle/PL-SQL specific features:
- Keywords and functions
- Data types (VARCHAR2, NUMBER, etc.)
- Syntax features (DUAL, ROWNUM, CONNECT BY, etc.)
"""

from sqltidy.dialects import get_dialect
from sqltidy.tokenizer import is_keyword
from sqltidy import format_sql
from sqltidy.rulebook import SQLTidyConfig


class TestOracleDialect:
    """Test Oracle dialect registration and features."""

    def test_dialect_registered(self):
        """Test that Oracle dialect is registered."""
        dialect = get_dialect("oracle")
        assert dialect is not None
        assert dialect.name == "oracle"

    def test_oracle_keywords(self):
        """Test Oracle specific keywords."""
        # Oracle specific
        assert is_keyword("DUAL", "oracle")
        assert is_keyword("ROWNUM", "oracle")
        assert is_keyword("CONNECT", "oracle")
        assert is_keyword("PRIOR", "oracle")
        assert is_keyword("SYSDATE", "oracle")

        # Common keywords
        assert is_keyword("SELECT", "oracle")
        assert is_keyword("FROM", "oracle")

    def test_oracle_functions(self):
        """Test Oracle specific functions."""
        dialect = get_dialect("oracle")

        assert "nvl" in dialect.functions
        assert "decode" in dialect.functions
        assert "to_char" in dialect.functions
        assert "to_date" in dialect.functions

    def test_oracle_data_types(self):
        """Test Oracle data types."""
        dialect = get_dialect("oracle")

        assert "varchar2" in dialect.data_types
        assert "number" in dialect.data_types
        assert "clob" in dialect.data_types
        assert "blob" in dialect.data_types


class TestOracleFormatting:
    """Test Oracle specific formatting."""

    def test_uppercase_keywords_default(self):
        """Test that Oracle defaults to uppercase keywords."""
        sql = "select id, name from users"
        config = SQLTidyConfig(
            dialect="oracle",
            uppercase_keywords=None,  # Use default
            newline_after_select=False,
            compact=True,
        )
        result = format_sql(sql, config=config)

        assert "SELECT" in result
        assert "FROM" in result

    def test_dual_table(self):
        """Test DUAL table usage."""
        sql = "select sysdate from dual"
        config = SQLTidyConfig(
            dialect="oracle", newline_after_select=False, compact=True
        )
        result = format_sql(sql, config=config)

        assert "DUAL" in result.upper()

    def test_connect_by_clause(self):
        """Test hierarchical CONNECT BY queries."""
        sql = "select * from employees start with manager_id is null connect by prior employee_id = manager_id"
        config = SQLTidyConfig(dialect="oracle")
        result = format_sql(sql, config=config)

        assert "CONNECT" in result.upper()
        assert "PRIOR" in result.upper()
