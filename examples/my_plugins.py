"""
Example SQLTidy plugins using decorator-based registration.

This file demonstrates how to create custom formatting rules using the
@sqltidy_rule decorator, similar to Polars' plugin system.

Usage:
    # From command line:
    sqltidy tidy input.sql --plugin my_plugins.py
    
    # Load from directory:
    sqltidy tidy input.sql --plugin-dir ~/.sqltidy/plugins
    
    # From Python:
    from sqltidy.plugins import load_plugin_file
    from sqltidy.api import format_sql
    
    load_plugin_file('my_plugins.py')
    result = format_sql(sql)
"""

from sqltidy.plugins import sqltidy_rule


@sqltidy_rule(rule_type="tidy", order=100)
def remove_trailing_semicolons(tokens, ctx):
    """Remove trailing semicolons from SQL."""
    if tokens and tokens[-1] == ';':
        return tokens[:-1]
    return tokens


@sqltidy_rule(rule_type="tidy", order=10)
def add_newline_after_from(tokens, ctx):
    """Add a newline after FROM keyword."""
    result = []
    for i, token in enumerate(tokens):
        result.append(token)
        if token.upper() == 'FROM' and i + 1 < len(tokens):
            # Add newline if not already there
            if tokens[i + 1] not in ('\n', '\r\n'):
                result.append('\n')
    return result


@sqltidy_rule(rule_type="tidy", order=50)
def double_indent_where_clause(tokens, ctx):
    """Add double indentation before WHERE clauses."""
    result = []
    for i, token in enumerate(tokens):
        if token.upper() == 'WHERE':
            # Add newline and double indent before WHERE
            if result and result[-1] not in ('\n', '\r\n'):
                result.append('\n')
            result.append('    ')  # Double indent
        result.append(token)
    return result


@sqltidy_rule(rule_type="tidy", order=40, supported_dialects={'postgresql', 'mysql'})
def postgres_mysql_only_rule(tokens, ctx):
    """Example of a dialect-specific rule (PostgreSQL and MySQL only)."""
    # This rule only runs for PostgreSQL and MySQL
    # Add your custom logic here
    return tokens


@sqltidy_rule(rule_type="rewrite", order=100)
def expand_select_star(tokens, ctx):
    """
    Replace SELECT * with explicit column names (mock example).
    
    In a real implementation, you would need schema information.
    This is just a demonstration of a rewrite rule.
    """
    result = []
    for i, token in enumerate(tokens):
        if token == '*' and i > 0 and tokens[i-1].upper() == 'SELECT':
            # Mock expansion - in reality you'd query schema
            result.append('col1, col2, col3')
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
        'select', 'from', 'where', 'join', 'inner', 'outer', 'left', 'right',
        'on', 'and', 'or', 'in', 'not', 'null', 'as', 'distinct', 'order',
        'by', 'group', 'having', 'limit', 'offset', 'union', 'except', 'intersect'
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
    """Example class-based rule."""
    
    rule_type = "tidy"
    order = 60
    
    def apply(self, tokens, ctx):
        """Ensure single space between tokens (simplified example)."""
        result = []
        for i, token in enumerate(tokens):
            if token in (' ', '\t') and result and result[-1] in (' ', '\t', '\n'):
                # Skip redundant whitespace
                continue
            result.append(token)
        return result


# Register the class-based rule
register_rule_class(CustomSpacingRule)


# You can also use the shorter alias 'rule' instead of 'sqltidy_rule'
from sqltidy.plugins import rule


@rule(rule_type="tidy", order=90)
def remove_double_spaces(tokens, ctx):
    """Remove consecutive spaces."""
    result = []
    for token in tokens:
        if token == ' ' and result and result[-1] == ' ':
            continue  # Skip double space
        result.append(token)
    return result
