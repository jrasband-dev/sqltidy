"""
Pytest configuration and shared fixtures.
"""
import pytest
from sqltidy.config import TidyConfig


@pytest.fixture
def simple_sql():
    """Simple SQL query for basic testing."""
    return "select id, name from users where active = 1"


@pytest.fixture
def complex_sql():
    """Complex SQL query with joins and aggregations."""
    return """
    SELECT 
        u.id,
        u.name,
        COUNT(*) AS order_count,
        SUM(o.total) AS total_spent
    FROM users u
    INNER JOIN orders o ON u.id = o.user_id
    WHERE u.active = 1
    GROUP BY u.id, u.name
    HAVING COUNT(*) > 5
    ORDER BY total_spent DESC
    """


@pytest.fixture
def default_config():
    """Default TidyConfig for testing."""
    return TidyConfig()


@pytest.fixture
def sqlserver_config():
    """SQL Server dialect configuration."""
    return TidyConfig(dialect='sqlserver', uppercase_keywords=True)


@pytest.fixture
def postgresql_config():
    """PostgreSQL dialect configuration."""
    return TidyConfig(dialect='postgresql', uppercase_keywords=False)


@pytest.fixture
def mysql_config():
    """MySQL dialect configuration."""
    return TidyConfig(dialect='mysql', uppercase_keywords=False)


@pytest.fixture
def oracle_config():
    """Oracle dialect configuration."""
    return TidyConfig(dialect='oracle', uppercase_keywords=True)


@pytest.fixture
def sqlite_config():
    """SQLite dialect configuration."""
    return TidyConfig(dialect='sqlite', uppercase_keywords=False)


@pytest.fixture(params=['sqlserver', 'postgresql', 'mysql', 'oracle', 'sqlite'])
def all_dialects(request):
    """Parameterized fixture for testing all dialects."""
    return request.param


@pytest.fixture
def dialect_config(all_dialects):
    """Create config for each dialect."""
    return TidyConfig(dialect=all_dialects)
