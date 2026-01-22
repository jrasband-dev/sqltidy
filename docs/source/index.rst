SQLTidy Documentation
======================

Welcome to SQLTidy! A powerful Python tool for formatting and tidying SQL scripts across multiple database dialects.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getting_started
   overview
   cli/index
   api
   dialects
   rules
   modules
   plugins

Quick Start
-----------

**Installation**

.. code-block:: bash

   pip install sqltidy

**Command Line**

Format SQL files from your terminal:

.. code-block:: bash

   sqltidy tidy myfile.sql
   sqltidy tidy "SQL Files" -r --pattern "*.sql"

See the :doc:`cli/index` for complete command reference.

**Python API**

Use SQLTidy programmatically in your code:

.. code-block:: python

   from sqltidy import tidy_sql
   
   sql = "SELECT * FROM users WHERE age > 18"
   formatted = tidy_sql(sql)
   print(formatted)

See the :doc:`api` for detailed API documentation.

Key Features
------------

- **Multi-Dialect Support**: SQL Server, PostgreSQL, MySQL, Oracle, SQLite
- **Flexible Formatting**: Tidy (format) and Rewrite (transform) rules
- **Extensible**: Create custom rules and plugins
- **CLI & API**: Use from command line or Python code

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
