``sqltidy tidy`` - Format SQL Files
====================================

The ``tidy`` command applies formatting rules to SQL files without changing their logical structure.

Synopsis
--------

.. code-block:: bash

   sqltidy tidy [OPTIONS] [INPUT]

Description
-----------

The ``tidy`` command formats SQL code according to dialect-specific rulebooks. It applies
formatting rules like:

- Uppercase/lowercase keywords
- Consistent indentation
- Newlines after SELECT, JOIN clauses
- Leading or trailing commas
- Compact whitespace removal

By default, formatted files are written to a ``Cleaned/`` subfolder relative to the input.

Arguments
---------

``INPUT``
   Path to a SQL file or folder to format. If omitted, reads from stdin.

Options
-------

``-d, --dialect {sqlserver,postgresql,mysql,oracle,sqlite}``
   SQL dialect to use for formatting. Each dialect has different keyword sets,
   data types, and formatting conventions.
   
   **Default:** ``sqlserver``
   
   **Example:**
   
   .. code-block:: bash
   
      sqltidy tidy queries.sql -d postgresql

``-o, --output PATH``
   Output file or folder path. When processing a folder, preserves the directory
   structure under the output path.
   
   **Example:**
   
   .. code-block:: bash
   
      sqltidy tidy input.sql -o formatted.sql
      sqltidy tidy "SQL Files" -o "Formatted SQL" -r

``-r, --recursive``
   Process folders recursively, including all subdirectories.
   
   **Example:**
   
   .. code-block:: bash
   
      sqltidy tidy "SQL Files" -r

``--pattern PATTERN``
   Glob pattern for selecting files when processing folders.
   
   **Default:** ``*.sql``
   
   **Example:**
   
   .. code-block:: bash
   
      sqltidy tidy scripts/ -r --pattern "*.tsql"

``--no-in-place``
   Don't write files to disk. Output is printed to stdout unless ``--output`` is specified.
   Useful for previewing changes or piping to other tools.
   
   **Example:**
   
   .. code-block:: bash
   
      sqltidy tidy query.sql --no-in-place | less

Examples
--------

Format a single file
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Format to Cleaned/ subfolder
   sqltidy tidy example.sql
   
   # Format to specific output file
   sqltidy tidy example.sql -o formatted.sql
   
   # Preview without saving
   sqltidy tidy example.sql --no-in-place

Format a folder
~~~~~~~~~~~~~~~

.. code-block:: bash

   # Non-recursive (only *.sql files in top folder)
   sqltidy tidy "SQL Files"
   
   # Recursive (all *.sql in folder tree)
   sqltidy tidy "SQL Files" -r
   
   # Custom output location
   sqltidy tidy "SQL Files" -r -o "Formatted"
   
   # Custom file pattern
   sqltidy tidy scripts/ -r --pattern "*.tsql"

Format from stdin
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Pipe SQL from another command
   cat query.sql | sqltidy tidy
   
   # Format clipboard content (Windows)
   Get-Clipboard | sqltidy tidy

Use different dialects
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   sqltidy tidy postgres_query.sql -d postgresql
   sqltidy tidy mysql_script.sql -d mysql
   sqltidy tidy oracle_proc.sql -d oracle

Behavior Details
----------------

Default Output Location
~~~~~~~~~~~~~~~~~~~~~~~

When no ``--output`` is specified:

- **Single file:** Creates ``Cleaned/`` subfolder next to the input file
- **Folder:** Creates ``Cleaned/`` subfolder inside the input folder
- **Stdin:** Prints to stdout

Rulebook Selection
~~~~~~~~~~~~~~~~~~

The command looks for a rulebook in this order:

1. User rulebook: ``~/.sqltidy/rulebooks/sqltidy_{dialect}.json``
2. Bundled rulebook: Package-included default for the dialect
3. Auto-generated: Created from rule metadata if no file exists

Progress Display
~~~~~~~~~~~~~~~~

When processing folders, a progress bar shows:

- Current file being processed
- Success/failure count
- Applied formatting rules

API Reference
-------------

.. currentmodule:: sqltidy.cli.core

.. autosummary::
   :toctree: ../_autosummary
   :nosignatures:

   handle_tidy_command

See Also
--------

- :doc:`rewrite` - Transform SQL structure
- :doc:`rulebooks` - Customize formatting rules
- :doc:`dialects` - View dialect-specific keywords
