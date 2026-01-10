"""
SQL dialect support for SQLTidy.

This module provides a dialect system that allows SQLTidy to support
multiple SQL database systems (SQL Server, PostgreSQL, MySQL, Oracle, SQLite).
"""

from .base import SQLDialect
from .registry import get_dialect, register_dialect, list_dialects, DIALECTS

__all__ = [
    "SQLDialect",
    "get_dialect",
    "register_dialect",
    "list_dialects",
    "DIALECTS",
]
