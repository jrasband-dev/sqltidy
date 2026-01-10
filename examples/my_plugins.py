"""
Example SQLTidy plugins using decorator-based registration.

This file demonstrates how to create custom formatting rules using the
@sqltidy_rule decorator, similar to Polars' plugin system.

Usage:
    # From command line:
    sqltidy tidy input.sql --rule my_plugins.py

    # Load from directory:
    sqltidy tidy input.sql --rule-dir ~/.sqltidy/rules

    # From Python:
    from sqltidy.plugins import load_rule_file
    from sqltidy.api import format_sql

    load_rule_file('my_plugins.py')
    result = format_sql(sql)

Naming Convention for Config Fields:
    - Rewrite rules (transformations): Use 'enable_' prefix
      Example: enable_my_transformation

    - Tidy rules (formatting): No prefix
      Example: my_formatting_option
"""

from sqltidy.plugins import sqltidy_rule
from sqltidy.rules.base import ConfigField


@sqltidy_rule(
    rule_type="tidy",
    order=100,
    config_fields={
        "remove_trailing_semicolons": ConfigField(
            name="remove_trailing_semicolons",
            default=True,
            description="Remove trailing semicolons from SQL statements?",
            field_type=bool,
        )
    },
)
def remove_trailing_semicolons(tokens, ctx):
    """Remove trailing semicolons from SQL."""
    # Check config option (tidy rules don't use 'enable_' prefix)
    if not getattr(ctx.config, "remove_trailing_semicolons", True):
        return tokens

    if tokens and tokens[-1] == ";":
        return tokens[:-1]
    return tokens


@sqltidy_rule(rule_type="tidy", order=10)
def add_newline_after_from(tokens, ctx):
    """Add a newline after FROM keyword."""
    result = []
    for i, token in enumerate(tokens):
        result.append(token)
        if token.upper() == "FROM" and i + 1 < len(tokens):
            # Add newline if not already there
            if tokens[i + 1] not in ("\n", "\r\n"):
                result.append("\n")
    return result


@sqltidy_rule(rule_type="tidy", order=50)
def double_indent_where_clause(tokens, ctx):
    """Add double indentation before WHERE clauses."""
    result = []
    for i, token in enumerate(tokens):
        if token.upper() == "WHERE":
            # Add newline and double indent before WHERE
            if result and result[-1] not in ("\n", "\r\n"):
                result.append("\n")
            result.append("    ")  # Double indent
        result.append(token)
    return result


@sqltidy_rule(rule_type="tidy", order=40, supported_dialects={"postgresql", "mysql"})
def postgres_mysql_only_rule(tokens, ctx):
    """Example of a dialect-specific rule (PostgreSQL and MySQL only)."""
    # This rule only runs for PostgreSQL and MySQL
    # Add your custom logic here
    return tokens


@sqltidy_rule(
    rule_type="rewrite",
    order=100,
    config_fields={
        "enable_expand_select_star": ConfigField(
            name="enable_expand_select_star",
            default=False,
            description="Expand SELECT * to explicit column names (requires schema info)?",
            field_type=bool,
        )
    },
)
def expand_select_star(tokens, ctx):
    """
    Replace SELECT * with explicit column names (mock example).

    In a real implementation, you would need schema information.
    This is just a demonstration of a rewrite rule.

    Note: Rewrite rules use 'enable_' prefix for config fields.
    """
    # Rewrite rules use 'enable_' prefix
    if not getattr(ctx.config, "enable_expand_select_star", False):
        return tokens

    result = []
    for i, token in enumerate(tokens):
        if token == "*" and i > 0 and tokens[i - 1].upper() == "SELECT":
            # Mock expansion - in reality you'd query schema
            result.append("col1, col2, col3")
        else:
            result.append(token)
    return result


@sqltidy_rule(rule_type="tidy", order=5)
def standardize_keywords(tokens, ctx):
    """
    Ensure all SQL keywords are uppercase.

    This is a simple example that uppercases common keywords.
    """
    keywords = {
        "select",
        "from",
        "where",
        "join",
        "inner",
        "outer",
        "left",
        "right",
        "on",
        "and",
        "or",
        "in",
        "not",
        "null",
        "as",
        "distinct",
        "order",
        "by",
        "group",
        "having",
        "limit",
        "offset",
        "union",
        "except",
        "intersect",
    }

    result = []
    for token in tokens:
        if token.lower() in keywords:
            result.append(token.upper())
        else:
            result.append(token)
    return result


# You can also register class-based rules
from sqltidy.plugins import register_rule_class
from sqltidy.rules.base import BaseRule


class CustomSpacingRule(BaseRule):
    """Example class-based rule with config field."""

    rule_type = "tidy"
    order = 60

    # Declare config fields (tidy rules don't use 'enable_' prefix)
    config_fields = {
        "custom_spacing": ConfigField(
            name="custom_spacing",
            default=True,
            description="Apply custom spacing rules to remove redundant whitespace?",
            field_type=bool,
        )
    }

    def apply(self, tokens, ctx):
        """Ensure single space between tokens (simplified example)."""
        # Check config option
        if not getattr(ctx.config, "custom_spacing", True):
            return tokens

        result = []
        for i, token in enumerate(tokens):
            if token in (" ", "\t") and result and result[-1] in (" ", "\t", "\n"):
                # Skip redundant whitespace
                continue
            result.append(token)
        return result


# Register the class-based rule
register_rule_class(CustomSpacingRule)


# Register the class-based rule
register_rule_class(CustomSpacingRule)


# You can also use the shorter alias 'rule' instead of 'sqltidy_rule'
from sqltidy.plugins import rule


# Example with dialect-specific defaults
@rule(
    rule_type="tidy",
    order=95,
    config_fields={
        "add_schema_prefix": ConfigField(
            name="add_schema_prefix",
            default=False,
            description="Add schema prefix to table names (e.g., dbo.TableName)?",
            field_type=bool,
            # Dialect-specific defaults
            dialect_defaults={
                "sqlserver": True,  # Enable by default for SQL Server
                "oracle": True,  # Enable by default for Oracle
            },
        )
    },
)
def add_schema_prefix(tokens, ctx):
    """Example rule with dialect-specific defaults."""
    # This would be enabled by default for SQL Server but not others
    if not getattr(ctx.config, "add_schema_prefix", False):
        return tokens

    # Your custom logic here
    return tokens


@rule(
    rule_type="tidy",
    order=90,
    config_fields={
        "remove_double_spaces": ConfigField(
            name="remove_double_spaces",
            default=True,
            description="Remove consecutive spaces in SQL?",
            field_type=bool,
        )
    },
)
def remove_double_spaces(tokens, ctx):
    """Remove consecutive spaces."""
    # Check config option
    if not getattr(ctx.config, "remove_double_spaces", True):
        return tokens

    result = []
    for token in tokens:
        if token == " " and result and result[-1] == " ":
            continue  # Skip double space
        result.append(token)
    return result
