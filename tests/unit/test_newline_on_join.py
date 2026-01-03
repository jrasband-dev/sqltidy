"""Tests for the newline_on_join rule."""
import pytest
from sqltidy import format_sql
from sqltidy.config import SQLTidyConfig


class TestNewlineOnJoinRule:
    """Test the newline_on_join formatting rule."""
    
    @pytest.fixture
    def config(self):
        """Config with newline_on_join enabled."""
        return SQLTidyConfig(
            dialect='sqlserver',
            uppercase_keywords=True,
            newline_on_join=True,
            newline_after_select=False,
            compact=True,
            leading_commas=False,
            indent_select_columns=False
        )
    
    def test_basic_left_join(self, config):
        """Test basic LEFT JOIN formatting."""
        sql = "SELECT * FROM MyTable LEFT JOIN Table2 ON MyTable.Id = Table2.ID"
        result = format_sql(sql, config)
        assert "LEFT JOIN Table2\nON" in result
    
    def test_inner_join(self, config):
        """Test INNER JOIN formatting."""
        sql = "SELECT * FROM T1 INNER JOIN T2 ON T1.Id = T2.Id"
        result = format_sql(sql, config)
        assert "INNER JOIN T2\nON" in result
    
    def test_right_join(self, config):
        """Test RIGHT JOIN formatting."""
        sql = "SELECT * FROM T1 RIGHT JOIN T2 ON T1.x = T2.x"
        result = format_sql(sql, config)
        assert "RIGHT JOIN T2\nON" in result
    
    def test_full_outer_join(self, config):
        """Test FULL OUTER JOIN formatting."""
        sql = "SELECT * FROM T1 FULL OUTER JOIN T2 ON T1.Id = T2.Id"
        result = format_sql(sql, config)
        assert "FULL OUTER JOIN T2\nON" in result
    
    def test_multiple_joins(self, config):
        """Test multiple JOINs in one query."""
        sql = "SELECT * FROM T1 INNER JOIN T2 ON T1.Id = T2.Id LEFT JOIN T3 ON T2.Code = T3.Code"
        result = format_sql(sql, config)
        assert "INNER JOIN T2\nON" in result
        assert "LEFT JOIN T3\nON" in result
    
    def test_join_with_alias(self, config):
        """Test JOIN with table aliases."""
        sql = "SELECT * FROM Orders o INNER JOIN Customers c ON o.CustomerId = c.Id"
        result = format_sql(sql, config)
        assert "INNER JOIN Customers c\nON" in result
    
    def test_join_with_as_alias(self, config):
        """Test JOIN with AS alias."""
        sql = "SELECT * FROM Orders AS o INNER JOIN Customers AS c ON o.CustomerId = c.Id"
        result = format_sql(sql, config)
        # Result may or may not have AS depending on other rules
        assert "INNER JOIN Customers" in result
        assert "\nON o.CustomerId = c.Id" in result
    
    def test_schema_qualified_tables(self, config):
        """Test JOIN with schema-qualified table names."""
        sql = "SELECT * FROM dbo.Orders JOIN dbo.Customers ON Orders.CustId = Customers.Id"
        result = format_sql(sql, config)
        assert "JOIN dbo.Customers\nON" in result
    
    def test_preserves_existing_newline(self, config):
        """Test that existing newlines before ON are preserved."""
        sql = """SELECT * FROM T1 LEFT JOIN T2
ON T1.Id = T2.Id"""
        result = format_sql(sql, config)
        assert "LEFT JOIN T2\nON" in result
    
    def test_cross_join_without_on(self, config):
        """Test CROSS JOIN (which has no ON clause) is not affected."""
        sql = "SELECT * FROM T1 CROSS JOIN T2 WHERE T1.x = 1"
        result = format_sql(sql, config)
        # Should not crash and should preserve CROSS JOIN
        assert "CROSS JOIN" in result
    
    def test_disabled_rule(self):
        """Test that rule doesn't apply when disabled."""
        config = SQLTidyConfig(
            dialect='sqlserver',
            uppercase_keywords=True,
            newline_on_join=False,  # Disabled
            newline_after_select=False,
            compact=True
        )
        sql = "SELECT * FROM T1 LEFT JOIN T2 ON T1.Id = T2.Id"
        result = format_sql(sql, config)
        # ON should remain on same line as LEFT JOIN when rule is disabled
        assert "LEFT JOIN T2 ON" in result.upper()
    
    def test_case_insensitive(self, config):
        """Test that rule works with mixed case keywords."""
        sql = "select * from t1 Left Join t2 on t1.id = t2.id"
        result = format_sql(sql, config)
        # Should handle mixed case and format correctly
        assert "\nON" in result.upper()
