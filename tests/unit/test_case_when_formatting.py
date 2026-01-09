"""Unit tests for CASE WHEN formatting rule (consolidated)."""

import pytest
from sqltidy.rules.general import CaseWhenNewlineIndentRule
from sqltidy.rules.base import FormatterContext
from sqltidy.rulebook import SQLTidyConfig
from sqltidy.tokenizer import Token, TokenGroup, tokenize_with_types


def to_text(tokens):
    parts = []
    for tok in tokens:
        if isinstance(tok, Token):
            parts.append(tok.value)
        elif isinstance(tok, TokenGroup):
            parts.append(tok.get_text())
        else:
            parts.append(str(tok))
    return ''.join(parts)


class TestCaseWhenNewlineIndentRule:
    """Test CaseWhenNewlineIndentRule."""

    def test_rule_disabled_by_default(self):
        rule = CaseWhenNewlineIndentRule()
        config = SQLTidyConfig(dialect='sqlserver')
        ctx = FormatterContext(config)

        sql = "SELECT CASE WHEN status='A' THEN 'Active' ELSE 'Inactive' END"
        tokens = tokenize_with_types(sql, dialect='sqlserver')
        result = rule.apply(tokens, ctx)

        assert to_text(result) == sql

    def test_simple_case_formatting(self):
        rule = CaseWhenNewlineIndentRule()
        config = SQLTidyConfig(dialect='sqlserver', tidy={'case_when_newline_indent': True})
        ctx = FormatterContext(config)

        sql = "SELECT CASE WHEN status='A' THEN 'Active' ELSE 'Inactive' END"
        tokens = tokenize_with_types(sql, dialect='sqlserver')
        result_sql = to_text(rule.apply(tokens, ctx))

        assert '\n' in result_sql
        assert '    WHEN' in result_sql
        assert '    ELSE' in result_sql

    def test_multiple_when_clauses(self):
        rule = CaseWhenNewlineIndentRule()
        config = SQLTidyConfig(dialect='sqlserver', tidy={'case_when_newline_indent': True})
        ctx = FormatterContext(config)

        sql = "SELECT CASE WHEN x=1 THEN 'One' WHEN x=2 THEN 'Two' WHEN x=3 THEN 'Three' ELSE 'Other' END"
        tokens = tokenize_with_types(sql, dialect='sqlserver')
        result_sql = to_text(rule.apply(tokens, ctx))

        assert result_sql.count('    WHEN') == 3
        assert '    ELSE' in result_sql

    def test_nested_case_expressions(self):
        rule = CaseWhenNewlineIndentRule()
        config = SQLTidyConfig(dialect='sqlserver', tidy={'case_when_newline_indent': True})
        ctx = FormatterContext(config)

        sql = "SELECT CASE WHEN x=1 THEN CASE WHEN y=1 THEN 'A' ELSE 'B' END ELSE 'C' END"
        tokens = tokenize_with_types(sql, dialect='sqlserver')
        result_sql = to_text(rule.apply(tokens, ctx))

        assert result_sql.count('CASE') == 2
        assert result_sql.count('END') == 2

    def test_case_in_where_clause(self):
        rule = CaseWhenNewlineIndentRule()
        config = SQLTidyConfig(dialect='sqlserver', tidy={'case_when_newline_indent': True})
        ctx = FormatterContext(config)

        sql = "SELECT * FROM users WHERE status = CASE WHEN active=1 THEN 'Y' ELSE 'N' END"
        tokens = tokenize_with_types(sql, dialect='sqlserver')
        result_sql = to_text(rule.apply(tokens, ctx))

        assert '    WHEN' in result_sql
        assert '    ELSE' in result_sql
