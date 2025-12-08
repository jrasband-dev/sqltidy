SQLTidy Documentation
======================

Welcome to the SQLTidy documentation! SQLTidy is a Python library for formatting and tidying SQL scripts.

**SQLTidy** makes it easy to format and clean up your SQL code with customizable rules and plugins.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getting_started
   api
   modules
   plugins

Quick Start
-----------

Installation
~~~~~~~~~~~~

Install SQLTidy using pip:

.. code-block:: bash

   pip install sqltidy

Basic Usage
~~~~~~~~~~~

Format a SQL string:

.. code-block:: python

   from sqltidy import format_sql
   
   sql = "SELECT * FROM users WHERE age > 18"
   formatted = format_sql(sql)
   print(formatted)

Features
--------

- **Easy to Use**: Simple API for formatting SQL
- **Extensible**: Register custom plugins at runtime
- **Configurable**: Customize formatting behavior with configuration objects
- **Fast**: Efficient tokenization and formatting

.. note::

   For more details, see the :doc:`getting_started` guide.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
