CLI Reference
=============

The ``sqltidy`` command-line interface formats, rewrites, and analyzes SQL files.

.. toctree::
   :maxdepth: 2
   :caption: Commands:

   tidy
   rewrite
   rulebooks
   rules
   dialects

Installation
------------

Install SQLTidy to get the ``sqltidy`` command:

.. code-block:: bash

   pip install sqltidy

Quick Start
-----------

.. code-block:: bash

   # Show version
   sqltidy version

   # Format a SQL file
   sqltidy tidy example.sql

   # Format a folder recursively
   sqltidy tidy "SQL Files" -r

   # Rewrite and format
   sqltidy rewrite complex_query.sql --tidy

   # Create a dialect rulebook
   sqltidy rulebooks create -d postgresql

   # List supported dialects
   sqltidy dialects list

Command Overview
----------------

Main Commands
~~~~~~~~~~~~~

:doc:`tidy`
   Format SQL files using tidy rules without changing structure.
   
   .. code-block:: bash
   
      sqltidy tidy file.sql
      sqltidy tidy folder/ -r

:doc:`rewrite`
   Transform SQL structure (e.g., subquery→CTE, alias styles).
   
   .. code-block:: bash
   
      sqltidy rewrite file.sql
      sqltidy rewrite file.sql --tidy

:doc:`rulebooks`
   Manage dialect-specific configuration rulebooks.
   
   .. code-block:: bash
   
      sqltidy rulebooks create -d postgresql
      sqltidy rulebooks list
      sqltidy rulebooks edit mysql

:doc:`rules`
   Manage custom formatting/rewrite rule plugins.
   
   .. code-block:: bash
   
      sqltidy rules add my_rule.py
      sqltidy rules list
      sqltidy rules remove old_rule.py

:doc:`dialects`
   Explore SQL dialects and their features.
   
   .. code-block:: bash
   
      sqltidy dialects list
      sqltidy dialects keywords postgresql
      sqltidy dialects datatypes sqlserver
      sqltidy dialects functions mysql

Additional Commands
~~~~~~~~~~~~~~~~~~~

``parse``
   Tokenize and analyze SQL structure.
   
   .. code-block:: bash
   
      sqltidy parse file.sql --dialect postgresql

``patterns``
   Inspect SQL patterns and constructs.
   
   .. code-block:: bash
   
      sqltidy patterns list postgresql
      sqltidy patterns show file.sql

``version``
   Display SQLTidy version.
   
   .. code-block:: bash
   
      sqltidy version

Common Options
--------------

These options appear across multiple commands:

``-d, --dialect {sqlserver,postgresql,mysql,oracle,sqlite}``
   SQL dialect for parsing and formatting.
   
   **Default:** ``sqlserver``

``-o, --output PATH``
   Output file or folder path.

``-r, --recursive``
   Process folders recursively.

``--pattern PATTERN``
   Glob pattern for file selection (default: ``*.sql``).

``--no-in-place``
   Don't modify files; output to stdout.

``--format {table,json}``
   Output format for display commands.

Common Workflows
----------------

Format an entire project
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Recursively format all SQL files
   sqltidy tidy "SQL Files" -r -d postgresql

Migrate to CTE style
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # First, edit rulebook to enable subquery→CTE
   sqltidy rulebooks edit postgresql
   # Set "enable_subquery_to_cte": true
   
   # Then rewrite with formatting
   sqltidy rewrite "Legacy SQL" -r --tidy

Set up dialect preferences
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Create rulebook
   sqltidy rulebooks create -d mysql
   
   # Edit preferences
   sqltidy rulebooks edit mysql
   
   # Use it
   sqltidy tidy queries/ -d mysql -r

Add custom formatting
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Create rule file: remove_comments.py
   # (see 'sqltidy rules' docs for examples)
   
   # Add to SQLTidy
   sqltidy rules add remove_comments.py
   
   # Sync rulebooks
   sqltidy rulebooks sync all
   
   # Configure in rulebook
   sqltidy rulebooks edit sqlserver

Compare dialects
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Compare keywords
   sqltidy dialects keywords sqlserver > sqlserver.txt
   sqltidy dialects keywords postgresql > postgresql.txt
   diff sqlserver.txt postgresql.txt
   
   # View functions
   sqltidy dialects functions oracle | grep -i date

Default Behavior
----------------

Output Location
~~~~~~~~~~~~~~~

When ``--output`` is not specified:

- **Single file:** Creates ``Cleaned/`` subfolder next to input
- **Folder:** Creates ``Cleaned/`` subfolder inside input folder
- **Stdin:** Prints to stdout

File Discovery
~~~~~~~~~~~~~~

When processing folders:

- Searches for ``*.sql`` files by default
- Use ``--pattern`` to change (e.g., ``*.tsql``, ``*.pgsql``)
- Respects ``--recursive`` flag for subdirectories

Configuration
~~~~~~~~~~~~~

Rulebook lookup order:

1. User rulebook: ``~/.sqltidy/rulebooks/sqltidy_{dialect}.json``
2. Bundled rulebook: Package default
3. Auto-generated: From rule metadata

File Locations
--------------

User Data
~~~~~~~~~

``~/.sqltidy/``
   User configuration directory

``~/.sqltidy/rulebooks/``
   Custom dialect rulebooks

``~/.sqltidy/rules/``
   Custom rule plugins

Package Data
~~~~~~~~~~~~

``{package}/sqltidy/rulebooks/``
   Bundled dialect defaults

API Entry Point
---------------

.. currentmodule:: sqltidy.cli.core

.. autosummary::
   :toctree: _autosummary
   :nosignatures:

   main

See Also
--------

- :doc:`../getting_started` - Tutorial and examples
- :doc:`../api` - Python API reference
- :doc:`../dialects` - Dialect system documentation
- :doc:`../rules` - Rule development guide
