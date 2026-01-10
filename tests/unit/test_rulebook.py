"""
Unit tests for configuration classes.

Tests:
- SQLTidyConfig defaults and validation
- Dialect-specific config behavior
- Config file loading and saving
"""

import pytest
from sqltidy.rulebook import SQLTidyConfig, SUPPORTED_DIALECTS


class TestSQLTidyConfig:
    """Test SQLTidyConfig class."""

    def test_default_values(self):
        """Test that defaults are set correctly."""
        config = SQLTidyConfig()

        assert config.dialect == "sqlserver"
        assert config.uppercase_keywords is None  # Use dialect default
        assert config.newline_after_select is True
        assert config.compact is True
        assert config.leading_commas is True
        assert config.indent_select_columns is True
        assert config.quote_identifiers is False
        assert config.enable_subquery_to_cte is True
        assert config.enable_alias_style_abc is False
        assert config.enable_alias_style_t_numeric is False

    def test_custom_dialect(self):
        """Test setting custom dialect."""
        config = SQLTidyConfig(dialect="postgresql")
        assert config.dialect == "postgresql"

        config = SQLTidyConfig(dialect="mysql")
        assert config.dialect == "mysql"

        config = SQLTidyConfig(dialect="oracle")
        assert config.dialect == "oracle"

        config = SQLTidyConfig(dialect="sqlite")
        assert config.dialect == "sqlite"

    def test_uppercase_keywords_override(self):
        """Test explicit uppercase_keywords setting."""
        # Explicit True
        config = SQLTidyConfig(dialect="postgresql", uppercase_keywords=True)
        assert config.uppercase_keywords is True

        # Explicit False
        config = SQLTidyConfig(dialect="sqlserver", uppercase_keywords=False)
        assert config.uppercase_keywords is False

        # None (use dialect default)
        config = SQLTidyConfig(dialect="sqlserver", uppercase_keywords=None)
        assert config.uppercase_keywords is None

    def test_formatting_options(self):
        """Test formatting option settings."""
        config = SQLTidyConfig(
            newline_after_select=False,
            compact=False,
            leading_commas=False,
            indent_select_columns=False,
        )

        assert config.newline_after_select is False
        assert config.compact is False
        assert config.leading_commas is False
        assert config.indent_select_columns is False

    def test_quote_identifiers(self):
        """Test quote_identifiers option."""
        config = SQLTidyConfig(quote_identifiers=True)
        assert config.quote_identifiers is True

        config = SQLTidyConfig(quote_identifiers=False)
        assert config.quote_identifiers is False

    def test_rewrite_rules(self):
        """Test enabling/disabling rewrite rules."""
        config = SQLTidyConfig(
            enable_subquery_to_cte=False,
            enable_alias_style_abc=True,
            enable_alias_style_t_numeric=True,
        )

        assert config.enable_subquery_to_cte is False
        assert config.enable_alias_style_abc is True
        assert config.enable_alias_style_t_numeric is True

    def test_get_dialect_defaults(self):
        """Test get_dialect_defaults returns correct settings per dialect."""
        # SQL Server and Oracle should default to uppercase
        sqlserver_config = SQLTidyConfig.get_dialect_defaults("sqlserver")
        assert sqlserver_config.dialect == "sqlserver"
        assert sqlserver_config.uppercase_keywords is True

        oracle_config = SQLTidyConfig.get_dialect_defaults("oracle")
        assert oracle_config.dialect == "oracle"
        assert oracle_config.uppercase_keywords is True

        # PostgreSQL, MySQL, SQLite should default to lowercase
        postgresql_config = SQLTidyConfig.get_dialect_defaults("postgresql")
        assert postgresql_config.dialect == "postgresql"
        assert postgresql_config.uppercase_keywords is False

        mysql_config = SQLTidyConfig.get_dialect_defaults("mysql")
        assert mysql_config.dialect == "mysql"
        assert mysql_config.uppercase_keywords is False

        sqlite_config = SQLTidyConfig.get_dialect_defaults("sqlite")
        assert sqlite_config.dialect == "sqlite"
        assert sqlite_config.uppercase_keywords is False

    def test_invalid_dialect(self):
        """Test that invalid dialect raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported dialect"):
            SQLTidyConfig.get_dialect_defaults("invalid_dialect")

    def test_to_dict(self):
        """Test config conversion to dictionary."""
        config = SQLTidyConfig(dialect="postgresql", uppercase_keywords=False)
        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert config_dict["dialect"] == "postgresql"
        assert config_dict["uppercase_keywords"] is False

    def test_from_dict(self):
        """Test config creation from dictionary."""
        data = {
            "dialect": "mysql",
            "uppercase_keywords": False,
            "newline_after_select": False,
            "compact": False,
            "leading_commas": False,
            "indent_select_columns": False,
            "quote_identifiers": True,
            "enable_subquery_to_cte": False,
            "enable_alias_style_abc": True,
            "enable_alias_style_t_numeric": False,
        }

        config = SQLTidyConfig.from_dict(data)

        assert config.dialect == "mysql"
        assert config.uppercase_keywords is False
        assert config.newline_after_select is False
        assert config.compact is False
        assert config.leading_commas is False
        assert config.indent_select_columns is False
        assert config.quote_identifiers is True
        assert config.enable_subquery_to_cte is False
        assert config.enable_alias_style_abc is True
        assert config.enable_alias_style_t_numeric is False
