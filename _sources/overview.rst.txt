Package Overview
================

SQLTidy is a Python library for formatting and tidying SQL scripts with support for multiple SQL dialects.

Architecture
------------

SQLTidy is organized into several key components:

Main API Layer
~~~~~~~~~~~~~~

- **sqltidy.api**: Public API functions (``format_sql``, ``register_plugin``, ``clear_plugins``)
- **sqltidy.config**: Configuration classes for customizing behavior
- **sqltidy.cli**: Command-line interface

Core Components
~~~~~~~~~~~~~~~

- **sqltidy.core**: ``SQLFormatter`` - main formatting engine that orchestrates the process
- **sqltidy.tokenizer**: ``Tokenizer`` - parses SQL into tokens
- **sqltidy.generator**: Interactive configuration generator

Plugin System
~~~~~~~~~~~~~

- **sqltidy.plugins**: Runtime plugin registration system
- **sqltidy.rules.base**: Base classes for all rules
- **sqltidy.rules.loader**: Dynamic rule loading

Dialects
~~~~~~~~

- **sqltidy.dialects**: SQL dialect support
  
  - ``sqlserver`` - Microsoft SQL Server (T-SQL)
  - ``postgresql`` - PostgreSQL
  - ``mysql`` - MySQL
  - ``oracle`` - Oracle Database (PL/SQL)
  - ``sqlite`` - SQLite

Rules
~~~~~

- **sqltidy.rules.tidy**: Formatting rules that don't change structure
  
  - ``uppercase_keywords``
  - ``newline_after_select``
  - ``compact_whitespace``
  - ``indent_select_columns``
  - ``leading_commas``
  - ``quote_identifiers``
  - ``oracle_connect_by``
  - ``sqlserver_top_formatting``

- **sqltidy.rules.rewrite**: Structural transformation rules
  
  - ``subquery_to_cte``
  - ``alias_style_abc``
  - ``alias_style_t_numeric``

Processing Flow
---------------

1. **Input**: SQL string provided by user
2. **Configuration**: Load config (defaults or custom ``SQLTidyConfig``)
3. **Dialect Detection**: Determine SQL dialect (or use configured dialect)
4. **Tokenization**: Parse SQL into tokens using ``Tokenizer``
5. **Rule Application**: Apply enabled rules in order:
   
   - Built-in tidy rules
   - Built-in rewrite rules
   - Runtime-registered plugins
   - Custom rules passed to ``format_sql()``

6. **Output**: Formatted SQL string

Quick Reference
---------------

Import the main API:

.. code-block:: python

   from sqltidy import format_sql, register_plugin, clear_plugins
   from sqltidy.config import SQLTidyConfig, SQLTidyConfig

Format SQL with defaults:

.. code-block:: python

   sql = "select * from users where age > 18"
   formatted = format_sql(sql)

Format with custom configuration:

.. code-block:: python

   config = SQLTidyConfig(
       uppercase_keywords=True,
       leading_commas=True,
       dialect='postgresql',
       rewrite=SQLTidyConfig(
           enable_subquery_to_cte=True
       )
   )
   formatted = format_sql(sql, config=config)

Register a custom rule:

.. code-block:: python

   from sqltidy.rules.base import BaseRule
   
   class MyRule(BaseRule):
       def apply(self, tokens):
           # Custom logic
           return tokens
   
   register_plugin(MyRule())
   formatted = format_sql(sql)

Module Index
------------

For detailed documentation of each module, see:

- :doc:`api` - Complete API reference
- :doc:`dialects` - SQL dialect system
- :doc:`rules` - Formatting and rewrite rules
- :doc:`modules` - All modules and subpackages
- :doc:`plugins` - Creating custom plugins

Configuration Reference
-----------------------

Main Configuration Classes
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autosummary::

   sqltidy.config.SQLTidyConfig
   sqltidy.config.SQLTidyConfig

See :doc:`api` for full configuration documentation.

Extension Points
----------------

SQLTidy provides several extension points:

1. **Custom Rules**: Create rules by inheriting from ``BaseRule``
2. **Runtime Plugins**: Register rules dynamically with ``register_plugin()``
3. **Custom Dialects**: Register new SQL dialects
4. **Configuration**: Override defaults via ``SQLTidyConfig``

For examples, see:

- :doc:`../CUSTOM_RULES`
- :doc:`../CUSTOM_RULES_QUICKSTART`
- :doc:`../PLUGINS`
