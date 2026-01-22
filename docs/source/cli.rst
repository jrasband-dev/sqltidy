CLI Reference
=============

The `sqltidy` command-line interface formats, rewrites, and analyzes SQL files.
This page documents all commands, options, and typical usage patterns.

Quick Start
-----------

Install and run `sqltidy` from your shell:

.. code-block:: bash

   # Show version
   sqltidy version

   # Tidy a single file
   sqltidy tidy SQL\ Files/example.sql

   # Tidy a folder recursively into a Cleaned/ subfolder
   sqltidy tidy "SQL Files" -r --pattern "*.sql"

   # Rewrite a file (optionally apply tidy after)
   sqltidy rewrite SQL\ Files/complex_join.sql --tidy

   # Parse and inspect tokens for a file
   sqltidy parse SQL\ Files/example.sql --format table

   # List supported dialects
   sqltidy dialects list --format table

   # Manage dialect rulebooks interactively
   sqltidy rulebooks create -d postgresql
   sqltidy rulebooks list

Command Overview
----------------

Top-level entry point provided by console script:

.. currentmodule:: sqltidy.cli.core

.. autosummary::
   :toctree: _autosummary
   :nosignatures:

   main

Primary Commands
----------------

Tidy
~~~~~
Format SQL files and folders using tidy rules.

.. code-block:: bash

   # Tidy a file, write to Cleaned/<filename>
   sqltidy tidy path/to/file.sql

   # Tidy a folder non-recursively
   sqltidy tidy path/to/folder --pattern "*.sql"

   # Tidy recursively, output to a custom folder
   sqltidy tidy path/to/folder -r -o path/to/output

Options:
- ``-d``, ``--dialect``: one of ``sqlserver``, ``postgresql``, ``mysql``, ``oracle``, ``sqlite`` (default: ``sqlserver``)
- ``-r``, ``--recursive``: process folders recursively
- ``--pattern``: glob pattern for file selection (default: ``*.sql``)
- ``-o``, ``--output``: output file or folder
- ``--no-in-place``: do not write files; print to stdout or require ``--output``

Handlers:

.. autosummary::
   :toctree: _autosummary
   :nosignatures:

   handle_tidy_command

Rewrite
~~~~~~~
Rewrite SQL queries (e.g., transforms like subquery→CTE), optionally followed by tidy.

.. code-block:: bash

   # Rewrite a single file
   sqltidy rewrite path/to/file.sql

   # Rewrite a folder recursively and tidy afterward
   sqltidy rewrite path/to/folder -r --tidy

Options:
- ``-d``, ``--dialect``: SQL dialect (default: ``sqlserver``)
- ``-r``, ``--recursive``: process folders recursively
- ``--pattern``: glob pattern for file selection (default: ``*.sql``)
- ``-o``, ``--output``: output file or folder
- ``--no-in-place``: do not write files; print to stdout or require ``--output``
- ``--summary``: show summary of processed files
- ``--tidy``: apply tidy rules after rewriting

Handlers:

.. autosummary::
   :toctree: _autosummary
   :nosignatures:

   handle_rewrite_command

Rulebooks
~~~~~~~~~
Create, list, edit, reset, and sync dialect rulebooks under the user directory ``~/.sqltidy/rulebooks/``.

.. code-block:: bash

   # Create a new rulebook for a dialect
   sqltidy rulebooks create -d postgresql

   # List user rulebooks
   sqltidy rulebooks list

   # Edit an existing rulebook (opens in default editor)
   sqltidy rulebooks edit postgresql

   # Reset a rulebook to defaults
   sqltidy rulebooks reset postgresql

   # Sync a rulebook with newly registered rules
   sqltidy rulebooks sync postgresql

Dialog helpers:

.. currentmodule:: sqltidy.cli.dialog

.. autosummary::
   :toctree: _autosummary
   :nosignatures:

   create_rulebook
   list_rulebooks
   edit_rulebook
   reset_rulebook
   update_rulebook
   load_rulebook_file

Rules Management
~~~~~~~~~~~~~~~~
Manage custom rule plugin files in ``~/.sqltidy/rules/``.

.. code-block:: bash

   # Add a rule file
   sqltidy rules add path/to/my_rule.py

   # List installed rules
   sqltidy rules list

   # Remove a rule file by name
   sqltidy rules remove my_rule.py

Dialog helpers:

.. autosummary::
   :toctree: _autosummary
   :nosignatures:

   add_rule
   list_rules
   remove_rule

Parse
~~~~~
Tokenize and optionally analyze semantic groups.

.. code-block:: bash

   sqltidy parse path/to/file.sql --dialect postgresql --format table

Options:
- ``--format``: ``table`` or ``json`` (default: ``table``)
- ``--tokens-only``: show raw tokens only
- ``--show-tree``: show hierarchical token tree

Patterns
~~~~~~~~
Inspect available SQL patterns or those detected in a file.

.. code-block:: bash

   # List patterns (global or for a given dialect)
   sqltidy patterns list postgresql --format table

   # Show patterns detected in a file
   sqltidy patterns show path/to/file.sql --dialect sqlserver

Handlers:

.. currentmodule:: sqltidy.cli.core

.. autosummary::
   :toctree: _autosummary
   :nosignatures:

   handle_pattern_command

Dialects
~~~~~~~~
Explore supported dialects and their keywords, datatypes, and functions.

.. code-block:: bash

   sqltidy dialects list --format json
   sqltidy dialects keywords postgresql --format table
   sqltidy dialects datatypes mysql
   sqltidy dialects functions sqlserver

Handlers:

.. autosummary::
   :toctree: _autosummary
   :nosignatures:

   handle_dialects_command

Notes
-----
- Default output location is a ``Cleaned/`` subfolder for folder operations unless ``--no-in-place`` or ``-o`` is used.
- Dialect-specific behavior is driven by the selected rulebook; when none exists, a default configuration is auto-generated.
