Rules System
============

SQLTidy uses a rule-based system to format and rewrite SQL code.
Rules are organized into two main categories: **Tidy Rules** and **Rewrite Rules**.

Rule Architecture
-----------------

Base Rule Classes
~~~~~~~~~~~~~~~~~

All rules inherit from base classes that define the rule interface.

.. automodule:: sqltidy.rules.base
   :members:
   :undoc-members:
   :show-inheritance:

Rule Loader
~~~~~~~~~~~

The rule loader system dynamically loads and manages rules.

.. automodule:: sqltidy.rules.loader
   :members:
   :undoc-members:
   :show-inheritance:

Rule Helpers
~~~~~~~~~~~~

Helper functions for implementing custom rules.

.. automodule:: sqltidy.rules.helpers
   :members:
   :undoc-members:
   :show-inheritance:

Built-in Rules
~~~~~~~~~~~~~~

The core rules module containing built-in formatting rules.

.. automodule:: sqltidy.rules.rules
   :members:
   :undoc-members:
   :show-inheritance:

Tidy Rules
----------

Tidy rules format SQL code without changing its structure or meaning.

Uppercase Keywords
~~~~~~~~~~~~~~~~~~

.. automodule:: sqltidy.rules.tidy.uppercase_keywords
   :members:
   :undoc-members:
   :show-inheritance:

Newline After SELECT
~~~~~~~~~~~~~~~~~~~~

.. automodule:: sqltidy.rules.tidy.newline_after_select
   :members:
   :undoc-members:
   :show-inheritance:

Compact Whitespace
~~~~~~~~~~~~~~~~~~

.. automodule:: sqltidy.rules.tidy.compact_whitespace
   :members:
   :undoc-members:
   :show-inheritance:

Indent SELECT Columns
~~~~~~~~~~~~~~~~~~~~~

.. automodule:: sqltidy.rules.tidy.indent_select_columns
   :members:
   :undoc-members:
   :show-inheritance:

Leading Commas
~~~~~~~~~~~~~~

.. automodule:: sqltidy.rules.tidy.leading_commas
   :members:
   :undoc-members:
   :show-inheritance:

Quote Identifiers
~~~~~~~~~~~~~~~~~

.. automodule:: sqltidy.rules.tidy.quote_identifiers
   :members:
   :undoc-members:
   :show-inheritance:

Oracle CONNECT BY
~~~~~~~~~~~~~~~~~

.. automodule:: sqltidy.rules.tidy.oracle_connect_by
   :members:
   :undoc-members:
   :show-inheritance:

SQL Server TOP Formatting
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: sqltidy.rules.tidy.sqlserver_top_formatting
   :members:
   :undoc-members:
   :show-inheritance:

Rewrite Rules
-------------

Rewrite rules transform SQL structure while preserving semantics.

Subquery to CTE
~~~~~~~~~~~~~~~

Convert subqueries to Common Table Expressions (CTEs).

.. automodule:: sqltidy.rules.rewrite.subquery_to_cte
   :members:
   :undoc-members:
   :show-inheritance:

Alias Style ABC
~~~~~~~~~~~~~~~

Apply alphabetic table aliases (A, B, C, ...).

.. automodule:: sqltidy.rules.rewrite.alias_style_abc
   :members:
   :undoc-members:
   :show-inheritance:

Alias Style T-Numeric
~~~~~~~~~~~~~~~~~~~~~

Apply T-numeric table aliases (T1, T2, T3, ...).

.. automodule:: sqltidy.rules.rewrite.alias_style_t_numeric
   :members:
   :undoc-members:
   :show-inheritance:

Creating Custom Rules
---------------------

You can create custom rules by inheriting from ``BaseRule``:

.. code-block:: python

   from sqltidy.rules.base import BaseRule
   from sqltidy.tokenizer import Token
   from typing import List
   
   class MyCustomRule(BaseRule):
       """Custom rule that modifies tokens."""
       
       def apply(self, tokens: List[Token]) -> List[Token]:
           # Implement your rule logic here
           return tokens
   
   # Register the rule
   from sqltidy import register_plugin
   register_plugin(MyCustomRule())

For more details, see:

- :doc:`../CUSTOM_RULES`
- :doc:`../CUSTOM_RULES_QUICKSTART`

Configuration
-------------

Rules can be enabled or disabled via configuration:

.. code-block:: python

   from sqltidy import format_sql
   from sqltidy.rulebook import SQLTidyConfig
   
   config = SQLTidyConfig(
       uppercase_keywords=True,
       leading_commas=True,
       rewrite=SQLTidyConfig(
           enable_subquery_to_cte=True
       )
   )
   
   formatted = format_sql(sql, config=config)
