"""
Unit tests for formatting rules.

Tests:
- Individual rule behavior
- Rule applicability
- Dialect-specific rules
"""
import pytest
from sqltidy.rules.base import BaseRule, FormatterContext
from sqltidy.rules.tidy.uppercase_keywords import UppercaseKeywordsRule
from sqltidy.rules.tidy.compact_whitespace import CompactWhitespaceRule
from sqltidy.rules.tidy.quote_identifiers import QuoteIdentifiersRule
from sqltidy.rules.tidy.sqlserver_top_formatting import SQLServerTopFormattingRule
from sqltidy.rules.tidy.oracle_connect_by import OracleConnectByFormattingRule
from sqltidy.config import SQLTidyConfig
from sqltidy.tokenizer import tokenize


class TestBaseRule:
    """Test BaseRule functionality."""
    
    def test_is_applicable_no_restriction(self):
        """Test that rules with no dialect restriction apply to all dialects."""
        rule = BaseRule()
        
        for dialect in ['sqlserver', 'postgresql', 'mysql', 'oracle', 'sqlite']:
            config = SQLTidyConfig(dialect=dialect)
            ctx = FormatterContext(config)
            assert rule.is_applicable(ctx) is True
    
    def test_is_applicable_with_restriction(self):
        """Test that rules with dialect restrictions only apply to specified dialects."""
        rule = BaseRule()
        rule.supported_dialects = {'sqlserver', 'oracle'}
        
        # Should apply to SQL Server and Oracle
        ctx_sqlserver = FormatterContext(SQLTidyConfig(dialect='sqlserver'))
        assert rule.is_applicable(ctx_sqlserver) is True
        
        ctx_oracle = FormatterContext(SQLTidyConfig(dialect='oracle'))
        assert rule.is_applicable(ctx_oracle) is True
        
        # Should NOT apply to PostgreSQL, MySQL, SQLite
        ctx_postgresql = FormatterContext(SQLTidyConfig(dialect='postgresql'))
        assert rule.is_applicable(ctx_postgresql) is False
        
        ctx_mysql = FormatterContext(SQLTidyConfig(dialect='mysql'))
        assert rule.is_applicable(ctx_mysql) is False


class TestUppercaseKeywordsRule:
    """Test UppercaseKeywordsRule."""
    
    def test_dialect_defaults(self):
        """Test that dialect defaults are correct."""
        rule = UppercaseKeywordsRule()
        
        # SQL Server and Oracle default to uppercase
        assert rule.DIALECT_DEFAULTS['sqlserver'] is True
        assert rule.DIALECT_DEFAULTS['oracle'] is True
        
        # PostgreSQL, MySQL, SQLite default to lowercase
        assert rule.DIALECT_DEFAULTS['postgresql'] is False
        assert rule.DIALECT_DEFAULTS['mysql'] is False
        assert rule.DIALECT_DEFAULTS['sqlite'] is False
    
    def test_uppercase_sqlserver(self):
        """Test uppercasing keywords for SQL Server."""
        rule = UppercaseKeywordsRule()
        config = SQLTidyConfig(dialect='sqlserver', uppercase_keywords=None)
        ctx = FormatterContext(config)
        
        tokens = ['select', ' ', 'id', ' ', 'from', ' ', 'users']
        result = rule.apply(tokens, ctx)
        
        assert result[0] == 'SELECT'
        assert result[4] == 'FROM'
        assert result[2] == 'id'  # Not a keyword
    
    def test_lowercase_postgresql(self):
        """Test lowercasing keywords for PostgreSQL."""
        rule = UppercaseKeywordsRule()
        config = SQLTidyConfig(dialect='postgresql', uppercase_keywords=None)
        ctx = FormatterContext(config)
        
        tokens = ['SELECT', ' ', 'ID', ' ', 'FROM', ' ', 'USERS']
        result = rule.apply(tokens, ctx)
        
        assert result[0] == 'select'
        assert result[4] == 'from'
    
    def test_explicit_override(self):
        """Test explicit uppercase_keywords override."""
        rule = UppercaseKeywordsRule()
        
        # Force uppercase on PostgreSQL (normally lowercase)
        config = SQLTidyConfig(dialect='postgresql', uppercase_keywords=True)
        ctx = FormatterContext(config)
        tokens = ['select', ' ', 'from']
        result = rule.apply(tokens, ctx)
        assert result[0] == 'SELECT'
        
        # Force lowercase on SQL Server (normally uppercase)
        config = SQLTidyConfig(dialect='sqlserver', uppercase_keywords=False)
        ctx = FormatterContext(config)
        tokens = ['SELECT', ' ', 'FROM']
        result = rule.apply(tokens, ctx)
        assert result[0] == 'select'


class TestCompactWhitespaceRule:
    """Test CompactWhitespaceRule."""
    
    def test_removes_duplicate_spaces(self):
        """Test that duplicate spaces are removed."""
        rule = CompactWhitespaceRule()
        config = SQLTidyConfig()
        ctx = FormatterContext(config)
        
        tokens = ['SELECT', ' ', ' ', ' ', 'id']
        result = rule.apply(tokens, ctx)
        
        # Should have only one space
        assert result.count(' ') == 1
        assert result == ['SELECT', ' ', 'id']
    
    def test_preserves_single_spaces(self):
        """Test that single spaces are preserved."""
        rule = CompactWhitespaceRule()
        config = SQLTidyConfig()
        ctx = FormatterContext(config)
        
        tokens = ['SELECT', ' ', 'id', ' ', 'FROM', ' ', 'users']
        result = rule.apply(tokens, ctx)
        
        assert result == tokens  # Should be unchanged


class TestQuoteIdentifiersRule:
    """Test QuoteIdentifiersRule."""
    
    def test_quote_chars_by_dialect(self):
        """Test that quote characters are correct for each dialect."""
        rule = QuoteIdentifiersRule()
        
        assert rule.QUOTE_CHARS['sqlserver'] == ('[', ']')
        assert rule.QUOTE_CHARS['mysql'] == ('`', '`')
        assert rule.QUOTE_CHARS['oracle'] == ('"', '"')
        assert rule.QUOTE_CHARS['postgresql'] == ('"', '"')
        assert rule.QUOTE_CHARS['sqlite'] == ('"', '"')
    
    def test_sqlserver_brackets(self):
        """Test SQL Server uses brackets."""
        rule = QuoteIdentifiersRule()
        config = SQLTidyConfig(dialect='sqlserver', quote_identifiers=True)
        ctx = FormatterContext(config)
        
        tokens = ['SELECT', ' ', 'id', ' ', 'FROM', ' ', 'users']
        result = rule.apply(tokens, ctx)
        
        # Check for brackets around identifiers
        assert '[id]' in ''.join(result) or ('[' in result and ']' in result)
    
    def test_mysql_backticks(self):
        """Test MySQL uses backticks."""
        rule = QuoteIdentifiersRule()
        config = SQLTidyConfig(dialect='mysql', quote_identifiers=True)
        ctx = FormatterContext(config)
        
        tokens = ['select', ' ', 'id', ' ', 'from', ' ', 'users']
        result = rule.apply(tokens, ctx)
        
        # Check for backticks
        assert '`id`' in ''.join(result) or ('`' in result)


class TestDialectSpecificRules:
    """Test dialect-specific rules."""
    
    def test_sqlserver_top_formatting_applies_to_sqlserver(self):
        """Test SQLServerTopFormattingRule applies to SQL Server."""
        rule = SQLServerTopFormattingRule()
        
        ctx_sqlserver = FormatterContext(SQLTidyConfig(dialect='sqlserver'))
        assert rule.is_applicable(ctx_sqlserver) is True
        
        ctx_postgresql = FormatterContext(SQLTidyConfig(dialect='postgresql'))
        assert rule.is_applicable(ctx_postgresql) is False
    
    def test_oracle_connect_by_applies_to_oracle(self):
        """Test OracleConnectByFormattingRule applies to Oracle."""
        rule = OracleConnectByFormattingRule()
        
        ctx_oracle = FormatterContext(SQLTidyConfig(dialect='oracle'))
        assert rule.is_applicable(ctx_oracle) is True
        
        ctx_mysql = FormatterContext(SQLTidyConfig(dialect='mysql'))
        assert rule.is_applicable(ctx_mysql) is False
    
    def test_sqlserver_top_formatting(self):
        """Test SQL Server TOP formatting."""
        rule = SQLServerTopFormattingRule()
        config = SQLTidyConfig(dialect='sqlserver')
        ctx = FormatterContext(config)
        
        tokens = ['SELECT', ' ', 'TOP', ' ', '10', ' ', 'id', ' ', 'FROM', ' ', 'users']
        result = rule.apply(tokens, ctx)
        
        # Should add newline before TOP
        assert '\n' in result
