"""
Dialect registry for managing and accessing SQL dialects.
"""

from typing import Dict, List
from .base import SQLDialect
from .sqlserver import SQLServerDialect
from .postgresql import PostgreSQLDialect
from .mysql import MySQLDialect
from .oracle import OracleDialect
from .sqlite import SQLiteDialect


# Global registry of available dialects
DIALECTS: Dict[str, SQLDialect] = {}


def _initialize_dialects():
    """Initialize the built-in dialects."""
    global DIALECTS

    # Register built-in dialects
    sqlserver = SQLServerDialect()
    postgresql = PostgreSQLDialect()
    mysql = MySQLDialect()
    oracle = OracleDialect()
    sqlite = SQLiteDialect()

    DIALECTS[sqlserver.name] = sqlserver
    DIALECTS[postgresql.name] = postgresql
    DIALECTS[mysql.name] = mysql
    DIALECTS[oracle.name] = oracle
    DIALECTS[sqlite.name] = sqlite


# Initialize on module load
_initialize_dialects()


def get_dialect(name: str = "sqlserver") -> SQLDialect:
    """
    Get a dialect by name.

    Args:
        name: The dialect name (case-insensitive). Defaults to 'sqlserver'.

    Returns:
        The requested SQLDialect instance.

    Raises:
        ValueError: If the dialect is not found.

    Examples:
        >>> dialect = get_dialect('sqlserver')
        >>> dialect = get_dialect('postgresql')
    """
    name_lower = name.lower()

    if name_lower not in DIALECTS:
        available = ", ".join(sorted(DIALECTS.keys()))
        raise ValueError(f"Dialect '{name}' not found. Available dialects: {available}")

    return DIALECTS[name_lower]


def register_dialect(dialect: SQLDialect) -> None:
    """
    Register a custom dialect.

    This allows users to add support for additional SQL dialects
    beyond the built-in ones.

    Args:
        dialect: An instance of SQLDialect to register.

    Raises:
        ValueError: If a dialect with the same name is already registered.

    Examples:
        >>> class CustomDialect(SQLDialect):
        ...     @property
        ...     def name(self):
        ...         return 'custom'
        ...     # ... implement other methods
        >>> register_dialect(CustomDialect())
    """
    if dialect.name.lower() in DIALECTS:
        raise ValueError(
            f"Dialect '{dialect.name}' is already registered. "
            f"Use a different name or unregister the existing dialect first."
        )

    DIALECTS[dialect.name.lower()] = dialect


def unregister_dialect(name: str) -> None:
    """
    Unregister a dialect.

    Args:
        name: The name of the dialect to unregister.

    Raises:
        ValueError: If the dialect is not found.
    """
    name_lower = name.lower()

    if name_lower not in DIALECTS:
        raise ValueError(f"Dialect '{name}' is not registered.")

    del DIALECTS[name_lower]


def list_dialects() -> List[str]:
    """
    List all registered dialect names.

    Returns:
        A sorted list of dialect names.

    Examples:
        >>> list_dialects()
        ['mysql', 'oracle', 'postgresql', 'sqlserver', 'sqlite']
    """
    return sorted(DIALECTS.keys())


def is_dialect_available(name: str) -> bool:
    """
    Check if a dialect is available.

    Args:
        name: The dialect name to check.

    Returns:
        True if the dialect is registered, False otherwise.

    Examples:
        >>> is_dialect_available('sqlserver')
        True
        >>> is_dialect_available('unknown')
        False
    """
    return name.lower() in DIALECTS
