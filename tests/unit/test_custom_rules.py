"""
Tests for custom rule helpers.

Tests the helper functions that make it easy to create custom rules.
"""

import pytest
from sqltidy.rules.helpers import (
    create_simple_rule,
    create_token_replacement_rule,
    create_pattern_rule,
    create_keyword_wrapper_rule,
    create_filter_rule,
    create_transform_rule,
    remove_trailing_semicolons,
    add_newline_before_keyword,
    replace_token,
    uppercase_keywords,
)
from sqltidy.rules.base import FormatterContext
from sqltidy.config import TidyConfig
from sqltidy.tokenizer import tokenize


class TestCreateSimpleRule:
    """Test create_simple_rule helper."""
    
    def test_creates_rule_class(self):
        """Test that a rule class is created."""
        def my_apply(tokens, ctx):
            return [t.upper() for t in tokens]
        
        RuleClass = create_simple_rule("MyRule", my_apply)
        rule = RuleClass()
        
        assert rule.rule_type == "tidy"
        assert rule.order == 50
    
    def test_custom_parameters(self):
        """Test creating rule with custom parameters."""
        def my_apply(tokens, ctx):
            return tokens
        
        RuleClass = create_simple_rule(
            "MyRule",
            my_apply,
            rule_type="rewrite",
            order=10,
            supported_dialects={'postgresql'}
        )
        
        rule = RuleClass()
        assert rule.rule_type == "rewrite"
        assert rule.order == 10
        assert rule.supported_dialects == {'postgresql'}
    
    def test_apply_function_works(self):
        """Test that the apply function is called correctly."""
        def my_apply(tokens, ctx):
            return [t.upper() for t in tokens]
        
        RuleClass = create_simple_rule("MyRule", my_apply)
        rule = RuleClass()
        
        config = TidyConfig()
        ctx = FormatterContext(config)
        tokens = ['select', 'id', 'from', 'users']
        
        result = rule.apply(tokens, ctx)
        assert result == ['SELECT', 'ID', 'FROM', 'USERS']


class TestTokenReplacementRule:
    """Test create_token_replacement_rule helper."""
    
    def test_replaces_tokens(self):
        """Test basic token replacement."""
        rule = create_token_replacement_rule({
            'user': 'app_user',
            'order': 'sales_order'
        })
        
        config = TidyConfig()
        ctx = FormatterContext(config)
        tokens = ['select', 'id', 'from', 'user']
        
        result = rule.apply(tokens, ctx)
        assert result == ['select', 'id', 'from', 'app_user']
    
    def test_case_insensitive_by_default(self):
        """Test that replacement is case-insensitive by default."""
        rule = create_token_replacement_rule({'user': 'app_user'})
        
        config = TidyConfig()
        ctx = FormatterContext(config)
        
        # Test uppercase
        result = rule.apply(['USER'], ctx)
        assert result == ['APP_USER']
        
        # Test lowercase
        result = rule.apply(['user'], ctx)
        assert result == ['app_user']


class TestPatternRule:
    """Test create_pattern_rule helper."""
    
    def test_replaces_pattern(self):
        """Test pattern replacement."""
        rule = create_pattern_rule(
            pattern=['INNER', 'JOIN'],
            replacement=['JOIN']
        )
        
        config = TidyConfig()
        ctx = FormatterContext(config)
        tokens = ['SELECT', '*', 'FROM', 'a', 'INNER', 'JOIN', 'b']
        
        result = rule.apply(tokens, ctx)
        assert result == ['SELECT', '*', 'FROM', 'a', 'JOIN', 'b']
    
    def test_multiple_replacements(self):
        """Test multiple pattern occurrences."""
        rule = create_pattern_rule(
            pattern=['IS', 'NOT', 'NULL'],
            replacement=['IS', 'NOT_NULL']
        )
        
        config = TidyConfig()
        ctx = FormatterContext(config)
        tokens = ['WHERE', 'a', 'IS', 'NOT', 'NULL', 'AND', 'b', 'IS', 'NOT', 'NULL']
        
        result = rule.apply(tokens, ctx)
        assert 'NOT_NULL' in result


class TestKeywordWrapperRule:
    """Test create_keyword_wrapper_rule helper."""
    
    def test_adds_prefix(self):
        """Test adding prefix before keyword."""
        rule = create_keyword_wrapper_rule(
            keyword='WHERE',
            prefix='\n'
        )
        
        config = TidyConfig()
        ctx = FormatterContext(config)
        tokens = ['SELECT', '*', 'FROM', 'users', 'WHERE', 'active', '=', '1']
        
        result = rule.apply(tokens, ctx)
        assert '\n' in result
        assert result.index('\n') < result.index('WHERE')
    
    def test_adds_suffix(self):
        """Test adding suffix after keyword."""
        rule = create_keyword_wrapper_rule(
            keyword='SELECT',
            suffix='\n'
        )
        
        config = TidyConfig()
        ctx = FormatterContext(config)
        tokens = ['SELECT', 'id', 'FROM', 'users']
        
        result = rule.apply(tokens, ctx)
        select_idx = result.index('SELECT')
        assert result[select_idx + 1] == '\n'


class TestFilterRule:
    """Test create_filter_rule helper."""
    
    def test_filters_tokens(self):
        """Test filtering tokens."""
        rule = create_filter_rule(lambda t: t != ';')
        
        config = TidyConfig()
        ctx = FormatterContext(config)
        tokens = ['SELECT', '*', 'FROM', 'users', ';']
        
        result = rule.apply(tokens, ctx)
        assert ';' not in result
        assert len(result) == 4


class TestTransformRule:
    """Test create_transform_rule helper."""
    
    def test_transforms_tokens(self):
        """Test transforming tokens."""
        rule = create_transform_rule(lambda t: t.upper())
        
        config = TidyConfig()
        ctx = FormatterContext(config)
        tokens = ['select', ' ', 'id', ' ', 'from', ' ', 'users']
        
        result = rule.apply(tokens, ctx)
        # Whitespace should be preserved
        assert result == ['SELECT', ' ', 'ID', ' ', 'FROM', ' ', 'USERS']


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_remove_trailing_semicolons(self):
        """Test remove_trailing_semicolons helper."""
        rule = remove_trailing_semicolons()
        
        config = TidyConfig()
        ctx = FormatterContext(config)
        tokens = ['SELECT', '*', 'FROM', 'users']
        
        result = rule.apply(tokens, ctx)
        assert result == tokens  # No change if no semicolon
    
    def test_add_newline_before_keyword(self):
        """Test add_newline_before_keyword helper."""
        rule = add_newline_before_keyword('WHERE')
        
        config = TidyConfig()
        ctx = FormatterContext(config)
        tokens = ['SELECT', '*', 'FROM', 'users', 'WHERE', 'id', '=', '1']
        
        result = rule.apply(tokens, ctx)
        assert '\n' in result
    
    def test_replace_token(self):
        """Test replace_token helper."""
        rule = replace_token('user', 'app_user')
        
        config = TidyConfig()
        ctx = FormatterContext(config)
        tokens = ['SELECT', '*', 'FROM', 'user']
        
        result = rule.apply(tokens, ctx)
        assert 'app_user' in result
    
    def test_uppercase_keywords(self):
        """Test uppercase_keywords helper."""
        rule = uppercase_keywords('select', 'from', 'where')
        
        config = TidyConfig()
        ctx = FormatterContext(config)
        tokens = ['select', 'id', 'from', 'users', 'where', 'active', '=', '1']
        
        result = rule.apply(tokens, ctx)
        assert result[0] == 'SELECT'
        assert result[2] == 'FROM'
        assert result[4] == 'WHERE'
        assert result[1] == 'id'  # Not a keyword, unchanged


class TestIntegrationWithFormatter:
    """Test using custom rules with SQLFormatter."""
    
    def test_custom_rule_in_formatter(self):
        """Test adding custom rule to formatter."""
        from sqltidy.core import SQLFormatter
        
        # Create custom rule
        rule = create_token_replacement_rule({'user': 'app_user'})
        
        # Add to formatter
        formatter = SQLFormatter(TidyConfig(
            uppercase_keywords=False,
            newline_after_select=False,
            compact=True
        ))
        formatter.rules.append(rule)
        
        # Format SQL
        sql = "select id from user"
        result = formatter.format(sql)
        
        assert 'app_user' in result
    
    def test_multiple_custom_rules(self):
        """Test adding multiple custom rules."""
        from sqltidy.core import SQLFormatter
        
        # Create custom rules
        rule1 = add_newline_before_keyword('WHERE')
        rule2 = uppercase_keywords('select', 'from', 'where')
        
        # Add to formatter
        formatter = SQLFormatter(TidyConfig(
            newline_after_select=False,
            compact=True
        ))
        formatter.rules.extend([rule1, rule2])
        
        # Format SQL
        sql = "select id from users where active = 1"
        result = formatter.format(sql)
        
        assert 'SELECT' in result
        assert 'FROM' in result
        assert 'WHERE' in result
        assert '\n' in result
