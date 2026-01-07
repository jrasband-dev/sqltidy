"""
Unit tests for CASE WHEN formatting rule.
"""
import pytest
from sqltidy.rules.tidy.case_when_formatting import CaseWhenFormattingRule
from sqltidy.rules.base import FormatterContext
from sqltidy.rulebook import SQLTidyConfig
from sqltidy.tokenizer import tokenize


class TestCaseWhenFormattingRule:
    """Test CaseWhenFormattingRule."""
    
    def test_rule_disabled_by_default(self):
        """Test that the rule is disabled by default."""
        rule = CaseWhenFormattingRule()
        config = SQLTidyConfig(dialect='sqlserver')
        ctx = FormatterContext(config)
        
        sql = "SELECT CASE WHEN status='A' THEN 'Active' ELSE 'Inactive' END"
        tokens = tokenize(sql)
        result = rule.apply(tokens, ctx)
        
        # Should return unchanged when disabled
        assert ''.join(result) == sql
    
    def test_simple_case_formatting(self):
        """Test formatting a simple CASE expression."""
        rule = CaseWhenFormattingRule()
        config = SQLTidyConfig(
            dialect='sqlserver',
            tidy={
                'indent_case_when': True,
                'case_indent_spaces': 4,
                'newline_after_case': False,
                'newline_before_end': True
            }
        )
        ctx = FormatterContext(config)
        
        sql = "SELECT CASE WHEN status='A' THEN 'Active' ELSE 'Inactive' END"
        tokens = tokenize(sql)
        result = rule.apply(tokens, ctx)
        result_sql = ''.join(result)
        
        # Should have newlines and indentation
        assert '\n' in result_sql
        assert '    WHEN' in result_sql
        assert '    ELSE' in result_sql
    
    def test_multiple_when_clauses(self):
        """Test formatting CASE with multiple WHEN clauses."""
        rule = CaseWhenFormattingRule()
        config = SQLTidyConfig(
            dialect='sqlserver',
            tidy={
                'indent_case_when': True,
                'case_indent_spaces': 4,
                'newline_after_case': False,
                'newline_before_end': True
            }
        )
        ctx = FormatterContext(config)
        
        sql = "SELECT CASE WHEN x=1 THEN 'One' WHEN x=2 THEN 'Two' WHEN x=3 THEN 'Three' ELSE 'Other' END"
        tokens = tokenize(sql)
        result = rule.apply(tokens, ctx)
        result_sql = ''.join(result)
        
        # Count WHEN occurrences with proper indentation
        assert result_sql.count('    WHEN') == 3
        assert '    ELSE' in result_sql
        assert result_sql.count('\n') >= 4  # At least 4 newlines (3 WHENs + 1 ELSE)
    
    def test_newline_after_case(self):
        """Test newline_after_case option."""
        rule = CaseWhenFormattingRule()
        config = SQLTidyConfig(
            dialect='sqlserver',
            tidy={
                'indent_case_when': True,
                'case_indent_spaces': 4,
                'newline_after_case': True,
                'newline_before_end': True
            }
        )
        ctx = FormatterContext(config)
        
        sql = "SELECT CASE WHEN status='A' THEN 'Active' ELSE 'Inactive' END"
        tokens = tokenize(sql)
        result = rule.apply(tokens, ctx)
        result_sql = ''.join(result)
        
        # CASE should be followed by newline, not space
        assert 'CASE\n' in result_sql
    
    def test_no_newline_before_end(self):
        """Test newline_before_end=False option."""
        rule = CaseWhenFormattingRule()
        config = SQLTidyConfig(
            dialect='sqlserver',
            tidy={
                'indent_case_when': True,
                'case_indent_spaces': 4,
                'newline_after_case': False,
                'newline_before_end': False
            }
        )
        ctx = FormatterContext(config)
        
        sql = "SELECT CASE WHEN status='A' THEN 'Active' ELSE 'Inactive' END"
        tokens = tokenize(sql)
        result = rule.apply(tokens, ctx)
        result_sql = ''.join(result)
        
        # END should be preceded by space, not newline
        assert "'Inactive' END" in result_sql
    
    def test_custom_indent_spaces(self):
        """Test custom indentation spacing."""
        rule = CaseWhenFormattingRule()
        config = SQLTidyConfig(
            dialect='sqlserver',
            tidy={
                'indent_case_when': True,
                'case_indent_spaces': 2,  # 2 spaces instead of 4
                'newline_after_case': False,
                'newline_before_end': True
            }
        )
        ctx = FormatterContext(config)
        
        sql = "SELECT CASE WHEN status='A' THEN 'Active' ELSE 'Inactive' END"
        tokens = tokenize(sql)
        result = rule.apply(tokens, ctx)
        result_sql = ''.join(result)
        
        # Should use 2-space indentation
        assert '  WHEN' in result_sql
        assert '  ELSE' in result_sql
        # Should NOT have 4-space indentation
        assert '    WHEN' not in result_sql
    
    def test_nested_case_expressions(self):
        """Test that nested CASE expressions are handled."""
        rule = CaseWhenFormattingRule()
        config = SQLTidyConfig(
            dialect='sqlserver',
            tidy={
                'indent_case_when': True,
                'case_indent_spaces': 4,
                'newline_after_case': False,
                'newline_before_end': True
            }
        )
        ctx = FormatterContext(config)
        
        # Nested CASE
        sql = "SELECT CASE WHEN x=1 THEN CASE WHEN y=1 THEN 'A' ELSE 'B' END ELSE 'C' END"
        tokens = tokenize(sql)
        result = rule.apply(tokens, ctx)
        result_sql = ''.join(result)
        
        # Both CASE expressions should be formatted
        # Count number of CASE keywords
        assert result_sql.count('CASE') == 2
        assert result_sql.count('END') == 2
    
    def test_case_without_else(self):
        """Test CASE expression without ELSE clause."""
        rule = CaseWhenFormattingRule()
        config = SQLTidyConfig(
            dialect='sqlserver',
            tidy={
                'indent_case_when': True,
                'case_indent_spaces': 4,
                'newline_after_case': False,
                'newline_before_end': True
            }
        )
        ctx = FormatterContext(config)
        
        sql = "SELECT CASE WHEN status='A' THEN 'Active' END"
        tokens = tokenize(sql)
        result = rule.apply(tokens, ctx)
        result_sql = ''.join(result)
        
        # Should format properly without ELSE
        assert '    WHEN' in result_sql
        assert 'ELSE' not in result_sql
        assert '\nEND' in result_sql
    
    def test_complex_when_conditions(self):
        """Test CASE with complex WHEN conditions."""
        rule = CaseWhenFormattingRule()
        config = SQLTidyConfig(
            dialect='sqlserver',
            tidy={
                'indent_case_when': True,
                'case_indent_spaces': 4,
                'newline_after_case': False,
                'newline_before_end': True
            }
        )
        ctx = FormatterContext(config)
        
        sql = "SELECT CASE WHEN (x > 10 AND y < 20) OR z = 5 THEN 'Valid' ELSE 'Invalid' END"
        tokens = tokenize(sql)
        result = rule.apply(tokens, ctx)
        result_sql = ''.join(result)
        
        # Complex condition should be preserved
        assert '(x > 10 AND y < 20) OR z = 5' in result_sql or \
               '(x>10 AND y<20) OR z=5' in result_sql  # Tokenizer might remove some spaces
    
    def test_multiple_case_in_query(self):
        """Test multiple CASE expressions in the same query."""
        rule = CaseWhenFormattingRule()
        config = SQLTidyConfig(
            dialect='sqlserver',
            tidy={
                'indent_case_when': True,
                'case_indent_spaces': 4,
                'newline_after_case': False,
                'newline_before_end': True
            }
        )
        ctx = FormatterContext(config)
        
        sql = "SELECT CASE WHEN x=1 THEN 'A' ELSE 'B' END, CASE WHEN y=1 THEN 'C' ELSE 'D' END"
        tokens = tokenize(sql)
        result = rule.apply(tokens, ctx)
        result_sql = ''.join(result)
        
        # Both CASE expressions should be formatted
        assert result_sql.count('CASE') == 2
        assert result_sql.count('    WHEN') == 2
        assert result_sql.count('    ELSE') == 2
    
    def test_dialect_independence(self):
        """Test that rule works across different dialects."""
        rule = CaseWhenFormattingRule()
        
        sql = "SELECT CASE WHEN status='A' THEN 'Active' ELSE 'Inactive' END"
        
        for dialect in ['sqlserver', 'postgresql', 'mysql', 'oracle', 'sqlite']:
            config = SQLTidyConfig(
                dialect=dialect,
                tidy={
                    'indent_case_when': True,
                    'case_indent_spaces': 4
                }
            )
            ctx = FormatterContext(config)
            tokens = tokenize(sql)
            result = rule.apply(tokens, ctx)
            result_sql = ''.join(result)
            
            # Should format consistently across dialects
            assert '    WHEN' in result_sql
            assert '    ELSE' in result_sql
    
    def test_case_in_where_clause(self):
        """Test CASE expression in WHERE clause."""
        rule = CaseWhenFormattingRule()
        config = SQLTidyConfig(
            dialect='sqlserver',
            tidy={
                'indent_case_when': True,
                'case_indent_spaces': 4,
                'newline_after_case': False,
                'newline_before_end': True
            }
        )
        ctx = FormatterContext(config)
        
        sql = "SELECT * FROM users WHERE status = CASE WHEN active=1 THEN 'Y' ELSE 'N' END"
        tokens = tokenize(sql)
        result = rule.apply(tokens, ctx)
        result_sql = ''.join(result)
        
        # CASE in WHERE should still be formatted
        assert '    WHEN' in result_sql
        assert '    ELSE' in result_sql
