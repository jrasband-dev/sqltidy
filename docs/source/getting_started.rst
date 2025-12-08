Getting Started
===============

Installation
------------

Install SQLTidy using pip:

.. code-block:: bash

   pip install sqltidy

Tidy
----

API Usage
~~~~~~~~~

The simplest way to use SQLTidy is to import the ``format_sql`` function:

.. code-block:: python

   from sqltidy import format_sql
   
   sql = "SELECT id, name FROM users WHERE age > 18"
   formatted = format_sql(sql)
   print(formatted)


You can customize formatting behavior using a ``TidyConfig`` object:

.. code-block:: python

   from sqltidy import format_sql
   from sqltidy.config import TidyConfig
   
   config = TidyConfig()
   sql = "SELECT * FROM users"
   formatted = format_sql(sql, config=config)

Command-Line Interface
----------------------

SQLTidy provides a command-line tool for formatting SQL files:

.. code-block:: bash

   sqltidy tidy input.sql -o output.sql

To see all available options:

.. code-block:: bash

   sqltidy --help


Rewrite
~~~~~~~

You can also use SQLTidy to rewrite SQL files in place:

.. code-block:: bash

   sqltidy rewrite input.sql -o output.sql




Extending with Plugins
----------------------

You can register custom formatting rules at runtime:

.. code-block:: python

   from sqltidy import format_sql, register_plugin
   from sqltidy.rules.base import BaseRule
   
   class MyCustomRule(BaseRule):
       def apply(self, tokens):
           # Your custom formatting logic here
           return tokens
   
   register_plugin(MyCustomRule())
   
   sql = "SELECT * FROM users"
   formatted = format_sql(sql)

For more information about creating custom rules, see the :doc:`plugins` documentation.

Configuration
-------------

Configuration options can be set using the ``TidyConfig`` class:

.. code-block:: python

   from sqltidy.config import TidyConfig
   
   config = TidyConfig(
       # Add your configuration options here
   )

See the :doc:`api` documentation for all available configuration options.
