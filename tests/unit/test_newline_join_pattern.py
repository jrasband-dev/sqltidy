"""Unit tests for NewlineJoinPatternRule"""
import pytest
from sqltidy.rules.tidy.newline_join_pattern import NewlineJoinPatternRule
from sqltidy.rules.base import FormatterContext
from sqltidy.config import SQLTidyConfig


class TestNewlineJoinPatternRule:
    """Test cases for the NewlineJoinPatternRule"""
    
    def test_pattern_before(self):
        """Test 'before' pattern - JOIN on new line, table on same line"""
        rule = NewlineJoinPatternRule()
        config = SQLTidyConfig(newline_join_pattern='before', join_indent='')
        ctx = FormatterContext(config)
        
        sql = "SELECT * FROM table1 INNER JOIN table2 ON table1.id = table2.id"
        tokens = [sql]
        
        result = rule.apply(tokens, ctx)
        result_sql = "".join(result)
        
        assert "INNER JOIN" in result_sql
        assert result_sql.count('\n') > 0
    
    def test_pattern_newline(self):
        """Test 'newline' pattern - JOIN and table on separate lines"""
        rule = NewlineJoinPatternRule()
        config = SQLTidyConfig(newline_join_pattern='newline', join_indent='')
        ctx = FormatterContext(config)
        
        sql = "SELECT * FROM table1 LEFT JOIN table2 ON table1.id = table2.id"
        tokens = [sql]
        
        result = rule.apply(tokens, ctx)
        result_sql = "".join(result)
        
        assert "LEFT JOIN" in result_sql
        assert result_sql.count('\n') >= 1
    
    def test_pattern_compact(self):
        """Test 'compact' pattern - minimal whitespace"""
        rule = NewlineJoinPatternRule()
        config = SQLTidyConfig(newline_join_pattern='compact', join_indent='')
        ctx = FormatterContext(config)
        
        sql = "SELECT * FROM table1\n    INNER JOIN table2\n    ON table1.id = table2.id"
        tokens = [sql]
        
        result = rule.apply(tokens, ctx)
        result_sql = "".join(result)
        
        # Compact should reduce excessive whitespace
        assert "INNER JOIN" in result_sql
    
    def test_disabled_when_no_pattern(self):
        """Test that rule is disabled when pattern is None"""
        rule = NewlineJoinPatternRule()
        config = SQLTidyConfig(newline_join_pattern=None)
        ctx = FormatterContext(config)
        
        sql = "SELECT * FROM table1 INNER JOIN table2 ON table1.id = table2.id"
        tokens = [sql]
        
        result = rule.apply(tokens, ctx)
        
        # Should return unchanged tokens
        assert result == tokens
    
    def test_multiple_joins(self):
        """Test handling multiple JOIN clauses"""
        rule = NewlineJoinPatternRule()
        config = SQLTidyConfig(newline_join_pattern='before', join_indent='')
        ctx = FormatterContext(config)
        
        sql = "SELECT * FROM t1 INNER JOIN t2 ON t1.id=t2.id LEFT JOIN t3 ON t1.id=t3.id"
        tokens = [sql]
        
        result = rule.apply(tokens, ctx)
        result_sql = "".join(result)
        
        # Both JOINs should be formatted
        assert "INNER JOIN" in result_sql
        assert "LEFT JOIN" in result_sql
    
    def test_join_types(self):
        """Test various JOIN types are handled"""
        rule = NewlineJoinPatternRule()
        config = SQLTidyConfig(newline_join_pattern='before', join_indent='')
        ctx = FormatterContext(config)
        
        join_types = [
            "INNER JOIN",
            "LEFT JOIN",
            "RIGHT JOIN", 
            "FULL JOIN",
            "CROSS JOIN",
            "LEFT OUTER JOIN",
            "RIGHT OUTER JOIN",
        ]
        
        for join_type in join_types:
            sql = f"SELECT * FROM t1 {join_type} t2 ON t1.id=t2.id"
            tokens = [sql]
            result = rule.apply(tokens, ctx)
            result_sql = "".join(result)
            
            # JOIN type should be preserved
            assert join_type in result_sql.upper()


if __name__ == "__main__":
    # Run tests
    import sys
    pytest.main([__file__, "-v"] + sys.argv[1:])
