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

.. automodule:: sqltidy.dialects.registry
   :members:
   :undoc-members:
   :show-inheritance:

Base Dialect
------------

The base dialect class that all specific dialects inherit from.

.. automodule:: sqltidy.dialects.base
   :members:
   :undoc-members:
   :show-inheritance:

SQL Server Dialect
------------------

Microsoft SQL Server (T-SQL) specific dialect.

.. automodule:: sqltidy.dialects.sqlserver
   :members:
   :undoc-members:
   :show-inheritance:

PostgreSQL Dialect
------------------

PostgreSQL specific dialect.

.. automodule:: sqltidy.dialects.postgresql
   :members:
   :undoc-members:
   :show-inheritance:

MySQL Dialect
-------------

MySQL specific dialect.

.. automodule:: sqltidy.dialects.mysql
   :members:
   :undoc-members:
   :show-inheritance:

Oracle Dialect
--------------

Oracle Database (PL/SQL) specific dialect.

.. automodule:: sqltidy.dialects.oracle
   :members:
   :undoc-members:
   :show-inheritance:

SQLite Dialect
--------------

SQLite specific dialect.

.. automodule:: sqltidy.dialects.sqlite
   :members:
   :undoc-members:
   :show-inheritance:

Usage Example
-------------

Specify a dialect when formatting SQL:

.. code-block:: python

   from sqltidy import format_sql
   from sqltidy.config import TidyConfig
   
   config = TidyConfig(dialect='postgresql')
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
