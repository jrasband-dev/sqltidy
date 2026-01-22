``sqltidy rewrite`` - Transform SQL Structure
==============================================

The ``rewrite`` command applies structural transformations to SQL queries while preserving their semantics.

Synopsis
--------

.. code-block:: bash

   sqltidy rewrite [OPTIONS] [INPUT]

Description
-----------

The ``rewrite`` command transforms SQL query structure according to enabled rewrite rules. Common transformations include:

- Converting subqueries to Common Table Expressions (CTEs)
- Applying consistent table alias styles (alphabetic: A, B, C or T-numeric: T1, T2, T3)
- Refactoring complex nested queries

Rewrite rules are controlled by the dialect rulebook's ``rewrite`` section.

Arguments
---------

``INPUT``
   Path to a SQL file or folder to rewrite. If omitted, reads from stdin.

Options
-------

``-d, --dialect {sqlserver,postgresql,mysql,oracle,sqlite}``
   SQL dialect to use for parsing and rewriting.
   
   **Default:** ``sqlserver``
   
   **Example:**
   
   .. code-block:: bash
   
      sqltidy rewrite complex_query.sql -d postgresql

``-o, --output PATH``
   Output file or folder path.
   
   **Example:**
   
   .. code-block:: bash
   
      sqltidy rewrite input.sql -o refactored.sql

``-r, --recursive``
   Process folders recursively.
   
   **Example:**
   
   .. code-block:: bash
   
      sqltidy rewrite "Legacy Queries" -r

``--pattern PATTERN``
   Glob pattern for file selection.
   
   **Default:** ``*.sql``

``--no-in-place``
   Don't write files; output to stdout unless ``--output`` is specified.

``--tidy``
   Apply tidy formatting rules after rewriting. This ensures the rewritten
   SQL is also properly formatted.
   
   **Example:**
   
   .. code-block:: bash
   
      sqltidy rewrite legacy.sql --tidy

``--summary``
   Display a detailed summary of rewrite operations performed.
   
   **Example:**
   
   .. code-block:: bash
   
      sqltidy rewrite queries/ -r --summary

Examples
--------

Basic rewriting
~~~~~~~~~~~~~~~

.. code-block:: bash

   # Rewrite a single file
   sqltidy rewrite complex_query.sql
   
   # Rewrite and format
   sqltidy rewrite complex_query.sql --tidy
   
   # Preview changes
   sqltidy rewrite complex_query.sql --no-in-place

Folder operations
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Rewrite all SQL files in a folder
   sqltidy rewrite "Legacy Queries" -r
   
   # Rewrite and tidy with custom output
   sqltidy rewrite "Old SQL" -r --tidy -o "Refactored"

Pipeline usage
~~~~~~~~~~~~~~

.. code-block:: bash

   # From stdin
   cat legacy_query.sql | sqltidy rewrite --tidy
   
   # Chain with other tools
   sqltidy rewrite query.sql --no-in-place | grep "WITH"

Rewrite Rules
-------------

The following transformations are available (controlled via rulebook):

Subquery to CTE
~~~~~~~~~~~~~~~

**Config field:** ``enable_subquery_to_cte``

Converts inline subqueries to CTEs (WITH clauses) for better readability.

**Before:**

.. code-block:: sql

   SELECT * FROM (
     SELECT id, name FROM users WHERE active = 1
   ) AS active_users

**After:**

.. code-block:: sql

   WITH active_users AS (
     SELECT id, name FROM users WHERE active = 1
   )
   SELECT * FROM active_users

Alias Style: Alphabetic (ABC)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Config field:** ``enable_alias_style_abc``

Renames table aliases to alphabetic style: A, B, C, ...

**Before:**

.. code-block:: sql

   SELECT u.name, o.total
   FROM users u
   JOIN orders o ON u.id = o.user_id

**After:**

.. code-block:: sql

   SELECT A.name, B.total
   FROM users A
   JOIN orders B ON A.id = B.user_id

Alias Style: T-Numeric
~~~~~~~~~~~~~~~~~~~~~~~

**Config field:** ``enable_alias_style_t_numeric``

Renames table aliases to T-numeric style: T1, T2, T3, ...

**Before:**

.. code-block:: sql

   SELECT u.name, o.total
   FROM users u
   JOIN orders o ON u.id = o.user_id

**After:**

.. code-block:: sql

   SELECT T1.name, T2.total
   FROM users T1
   JOIN orders T2 ON T1.id = T2.user_id

Configuring Rewrites
--------------------

Edit your dialect rulebook to enable/disable rewrite rules:

.. code-block:: bash

   sqltidy rulebooks edit postgresql

In the JSON file, modify the ``rewrite`` section:

.. code-block:: json

   {
     "dialect": "postgresql",
     "tidy": { ... },
     "rewrite": {
       "enable_subquery_to_cte": true,
       "enable_alias_style_abc": false,
       "enable_alias_style_t_numeric": false
     }
   }

API Reference
-------------

.. currentmodule:: sqltidy.cli.core

.. autosummary::
   :toctree: ../_autosummary
   :nosignatures:

   handle_rewrite_command

See Also
--------

- :doc:`tidy` - Format SQL without structural changes
- :doc:`rulebooks` - Configure rewrite rules
- API: :doc:`../rules` - Custom rewrite rule development
