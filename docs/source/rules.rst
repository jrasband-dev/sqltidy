Rules System
============

SQLTidy uses a rule-based system to format and rewrite SQL code.

Rule Architecture
-----------------

Base Rule Classes
~~~~~~~~~~~~~~~~~

All rules inherit from base classes that define the rule interface.

.. currentmodule:: sqltidy.rules.base

.. autosummary::
   :toctree: _autosummary

   ConfigField
   FormatterContext
   BaseRule

Rule Loader
~~~~~~~~~~~

The rule loader system dynamically loads and manages rules.

.. currentmodule:: sqltidy.rules.loader

.. autosummary::
   :toctree: _autosummary
   :nosignatures:

   load_rules

General Formatting Rules
------------------------

These rules format SQL code without changing its structure or meaning.

.. currentmodule:: sqltidy.rules.general

.. autosummary::
   :toctree: _autosummary

   UppercaseKeywordsRule
   CompactWhitespaceRule
   NewlineJoinPatternRule
   OnNewlinesRule
   QuoteIdentifiersRule
   SelectNewlineRule
   ColumnsNewlineRule
   WhereNewlinesRule
   IndentSelectColumnsRule
   CaseWhenNewlineIndentRule
   LeadingCommasRule
   AliasStyleABCRule
   AliasStyleTNumericRule
   SubqueryToCTERule

Database-Specific Rules
------------------------

SQL Server Rules
~~~~~~~~~~~~~~~~

Rules specific to Microsoft SQL Server (T-SQL).

.. currentmodule:: sqltidy.rules.sqlserver

.. autosummary::
   :toctree: _autosummary

   SQLServerTopFormattingRule

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
