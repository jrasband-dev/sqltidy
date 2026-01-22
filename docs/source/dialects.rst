Dialect System
==============

SQLTidy supports multiple SQL database systems through its dialect system.
Each dialect defines database-specific keywords, functions, and parsing rules.

Supported Dialects
------------------

SQLTidy includes built-in support for:

- **SQL Server** (T-SQL)
- **PostgreSQL**
- **MySQL**
- **Oracle** (PL/SQL)
- **SQLite**

Dialect Registry
----------------

The dialect registry manages all available SQL dialects.

.. currentmodule:: sqltidy.dialects.registry

.. autosummary::
   :toctree: _autosummary
   :nosignatures:

   get_dialect
   register_dialect
   unregister_dialect
   list_dialects
   is_dialect_available

Base Dialect
------------

The base dialect class that all specific dialects inherit from.

.. currentmodule:: sqltidy.dialects.base

.. autosummary::
   :toctree: _autosummary

   SQLDialect

SQL Server Dialect
------------------

Microsoft SQL Server (T-SQL) specific dialect.

.. currentmodule:: sqltidy.dialects.sqlserver

.. autosummary::
   :toctree: _autosummary

   SQLServerDialect

PostgreSQL Dialect
------------------

PostgreSQL specific dialect.

.. currentmodule:: sqltidy.dialects.postgresql

.. autosummary::
   :toctree: _autosummary

   PostgreSQLDialect

MySQL Dialect
-------------

MySQL specific dialect.

.. currentmodule:: sqltidy.dialects.mysql

.. autosummary::
   :toctree: _autosummary

   MySQLDialect

Oracle Dialect
--------------

Oracle Database (PL/SQL) specific dialect.

.. currentmodule:: sqltidy.dialects.oracle

.. autosummary::
   :toctree: _autosummary

   OracleDialect

SQLite Dialect
--------------

SQLite specific dialect.

.. currentmodule:: sqltidy.dialects.sqlite

.. autosummary::
   :toctree: _autosummary

   SQLiteDialect

Usage Example
-------------

Specify a dialect when formatting SQL:

.. code-block:: python

   from sqltidy import format_sql
   from sqltidy.rulebook import SQLTidyConfig
   
   config = SQLTidyConfig(dialect='postgresql')
   sql = "SELECT * FROM users WHERE id = 1"
   formatted = format_sql(sql, config=config)

Or use the dialect registry directly:

.. code-block:: python

   from sqltidy.dialects import get_dialect, list_dialects
   
   # Get available dialects
   print(list_dialects())
   
   # Get a specific dialect
   pg_dialect = get_dialect('postgresql')
   print(pg_dialect.keywords)
