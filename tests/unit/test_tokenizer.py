"""
Unit tests for tokenizer functionality.

Tests:
- Basic tokenization
- Token type detection
- Keyword identification
- SQL Server specific features
"""
import pytest
from sqltidy.tokenizer import tokenize, tokenize_with_types, is_keyword, TokenType


class TestBasicTokenization:
    """Test basic tokenization functionality."""
    
    def test_simple_select(self):
        """Test tokenizing a simple SELECT statement."""
        sql = "SELECT id, name FROM users"
        tokens = tokenize(sql)
        
        assert 'SELECT' in [t.upper() for t in tokens]
        assert 'FROM' in [t.upper() for t in tokens]
        assert len(tokens) > 0
    
    def test_whitespace_handling(self):
        """Test that whitespace is properly tokenized."""
        sql = "SELECT  \n  id FROM users"
        tokens = tokenize(sql)
        
        # Should have newlines and spaces as separate tokens
        assert '\n' in tokens or any(t.isspace() for t in tokens)
    
    def test_comments(self):
        """Test comment tokenization."""
        sql = "SELECT id -- this is a comment\nFROM users"
        tokens = tokenize(sql)
        
        assert len(tokens) > 0
    
    def test_keywords_case_insensitive(self):
        """Test that keywords are detected case-insensitively."""
        assert is_keyword('SELECT', 'sqlserver')
        assert is_keyword('select', 'sqlserver')
        assert is_keyword('Select', 'sqlserver')
        assert is_keyword('FROM', 'sqlserver')
        assert is_keyword('from', 'sqlserver')


class TestTypedTokenization:
    """Test tokenization with type information."""
    
    def test_token_types(self):
        """Test that tokens have correct types."""
        sql = "SELECT 123 FROM users"
        typed_tokens = tokenize_with_types(sql, 'sqlserver')
        
        # Should have keyword, number, and identifier tokens
        types = [t.type for t in typed_tokens if t.type != TokenType.WHITESPACE]
        assert TokenType.KEYWORD in types
    
    def test_identifier_detection(self):
        """Test identifier token detection."""
        sql = "SELECT user_id, user_name FROM users"
        typed_tokens = tokenize_with_types(sql, 'sqlserver')
        
        identifiers = [t for t in typed_tokens if t.type == TokenType.IDENTIFIER]
        assert len(identifiers) > 0


class TestKeywordDetection:
    """Test keyword detection across dialects."""
    
    def test_sqlserver_keywords(self):
        """Test SQL Server specific keywords."""
        assert is_keyword('SELECT', 'sqlserver')
        assert is_keyword('WITH', 'sqlserver')
        assert is_keyword('NOLOCK', 'sqlserver')
        assert not is_keyword('user_id', 'sqlserver')
        assert not is_keyword('123', 'sqlserver')
    
    def test_postgresql_keywords(self):
        """Test PostgreSQL specific keywords."""
        assert is_keyword('SELECT', 'postgresql')
        assert is_keyword('RETURNING', 'postgresql')
        assert is_keyword('ILIKE', 'postgresql')
    
    def test_mysql_keywords(self):
        """Test MySQL specific keywords."""
        assert is_keyword('SELECT', 'mysql')
        assert is_keyword('LIMIT', 'mysql')
        assert is_keyword('REGEXP', 'mysql')
    
    def test_oracle_keywords(self):
        """Test Oracle specific keywords."""
        assert is_keyword('SELECT', 'oracle')
        assert is_keyword('CONNECT', 'oracle')
        assert is_keyword('DUAL', 'oracle')
    
    def test_sqlite_keywords(self):
        """Test SQLite specific keywords."""
        assert is_keyword('SELECT', 'sqlite')
        assert is_keyword('AUTOINCREMENT', 'sqlite')


class TestComplexQueries:
    """Test tokenization of complex SQL queries."""
    
    def test_join_query(self):
        """Test tokenizing queries with joins."""
        sql = """
        SELECT u.id, u.name, o.order_date
        FROM users u
        INNER JOIN orders o ON u.id = o.user_id
        WHERE u.active = 1
        """
        tokens = tokenize(sql)
        
        upper_tokens = [t.upper() for t in tokens]
        assert 'SELECT' in upper_tokens
        assert 'INNER' in upper_tokens or 'JOIN' in upper_tokens
        assert 'WHERE' in upper_tokens
    
    def test_cte_query(self):
        """Test tokenizing queries with CTEs."""
        sql = """
        WITH sales_cte AS (
            SELECT customer_id, SUM(total) as total_sales
            FROM orders
            GROUP BY customer_id
        )
        SELECT * FROM sales_cte WHERE total_sales > 1000
        """
        tokens = tokenize(sql)
        
        upper_tokens = [t.upper() for t in tokens]
        assert 'WITH' in upper_tokens
        assert 'AS' in upper_tokens
    
    def test_subquery(self):
        """Test tokenizing queries with subqueries."""
        sql = """
        SELECT id, name
        FROM users
        WHERE id IN (SELECT user_id FROM orders WHERE total > 100)
        """
        tokens = tokenize(sql)
        
        assert len(tokens) > 0
        assert any(t == '(' for t in tokens)
        assert any(t == ')' for t in tokens)
