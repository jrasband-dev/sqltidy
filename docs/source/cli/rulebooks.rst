``sqltidy rulebooks`` - Manage Configuration
=============================================

Manage dialect-specific rulebooks that control formatting and rewriting behavior.

Synopsis
--------

.. code-block:: bash

   sqltidy rulebooks {create,list,edit,reset,sync} [OPTIONS]

Description
-----------

Rulebooks are JSON configuration files stored in ``~/.sqltidy/rulebooks/`` that define
formatting and transformation rules for each SQL dialect. Each rulebook contains:

- **Tidy rules:** Formatting preferences (uppercase keywords, indentation, etc.)
- **Rewrite rules:** Structural transformations (subquery→CTE, alias styles, etc.)

Subcommands
-----------

``create``
~~~~~~~~~~

Create a new rulebook for a dialect.

**Synopsis:**

.. code-block:: bash

   sqltidy rulebooks create [OPTIONS]

**Options:**

``-d, --dialect {sqlserver,postgresql,mysql,oracle,sqlite}``
   Dialect for the rulebook. If omitted, prompts interactively.

``-t, --template PATH``
   Use an existing rulebook as a template.

``--no-plugins``
   Exclude user plugin rules from configuration. By default, custom rules
   from ``~/.sqltidy/rules/`` are included.

**Examples:**

.. code-block:: bash

   # Create PostgreSQL rulebook (interactive)
   sqltidy rulebooks create
   
   # Create specific dialect
   sqltidy rulebooks create -d postgresql
   
   # Create from template
   sqltidy rulebooks create -d mysql -t sqltidy_postgresql.json
   
   # Create without plugins
   sqltidy rulebooks create -d oracle --no-plugins

``list``
~~~~~~~~

List all rulebooks in the user directory.

**Synopsis:**

.. code-block:: bash

   sqltidy rulebooks list [OPTIONS]

**Options:**

``-d, --directory PATH``
   Directory to search for rulebooks.
   
   **Default:** ``~/.sqltidy/rulebooks/``

**Examples:**

.. code-block:: bash

   # List user rulebooks
   sqltidy rulebooks list
   
   # List rulebooks in custom directory
   sqltidy rulebooks list -d "C:\Configs"

**Output Example:**

.. code-block:: text

   User Rulebook Directory
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   C:\Users\user\.sqltidy\rulebooks
   
   📚 Rulebooks (3 found)
   ├── 📄 sqltidy_postgresql.json
   │   ├── Dialect: postgresql
   │   ├── Rules enabled: 12 (8 tidy, 4 rewrite)
   │   └── Size: 3.2 KB
   ├── 📄 sqltidy_sqlserver.json
   │   ├── Dialect: sqlserver
   │   ├── Rules enabled: 10 (7 tidy, 3 rewrite)
   │   └── Size: 2.8 KB
   └── 📄 sqltidy_mysql.json
       ├── Dialect: mysql
       ├── Rules enabled: 11 (8 tidy, 3 rewrite)
       └── Size: 3.0 KB

``edit``
~~~~~~~~

Edit an existing rulebook in your default text editor.

**Synopsis:**

.. code-block:: bash

   sqltidy rulebooks edit [RULEBOOK]

**Arguments:**

``RULEBOOK``
   Dialect name (e.g., ``postgresql``) or filename. If omitted, shows
   interactive selection menu.

**Examples:**

.. code-block:: bash

   # Edit specific dialect (interactive choice if not found)
   sqltidy rulebooks edit postgresql
   
   # Edit by filename
   sqltidy rulebooks edit sqltidy_mysql.json
   
   # Interactive selection
   sqltidy rulebooks edit

**Notes:**

- Opens the file in your system's default JSON/text editor
- Only edits files in ``~/.sqltidy/rulebooks/``
- Use ``create`` to make new rulebooks first

``reset``
~~~~~~~~~

Reset a rulebook to auto-generated defaults.

**Synopsis:**

.. code-block:: bash

   sqltidy rulebooks reset [RULEBOOK]

**Arguments:**

``RULEBOOK``
   Dialect name, filename, or ``all`` to reset all rulebooks.

**Examples:**

.. code-block:: bash

   # Reset specific dialect
   sqltidy rulebooks reset postgresql
   
   # Reset all rulebooks
   sqltidy rulebooks reset all

**Warning:**

This permanently removes your customizations and regenerates the rulebook
from rule metadata.

``sync``
~~~~~~~~

Sync an existing rulebook with newly registered rules.

**Synopsis:**

.. code-block:: bash

   sqltidy rulebooks sync [OPTIONS] [RULEBOOK]

**Arguments:**

``RULEBOOK``
   Dialect name, filename, or ``all`` to sync all rulebooks.

**Options:**

``--no-plugins``
   Exclude plugin rules from sync.

**Examples:**

.. code-block:: bash

   # Sync after adding custom rules
   sqltidy rulebooks sync postgresql
   
   # Sync all rulebooks
   sqltidy rulebooks sync all
   
   # Sync without plugins
   sqltidy rulebooks sync mysql --no-plugins

**Use Case:**

After adding custom plugin rules to ``~/.sqltidy/rules/``, run sync to add
their configuration fields to existing rulebooks while preserving your
current settings.

Rulebook Structure
------------------

Rulebooks are JSON files with this structure:

.. code-block:: json

   {
     "dialect": "postgresql",
     "tidy": {
       "uppercase_keywords": false,
       "compact": true,
       "leading_commas": false,
       "indent_select_columns": true,
       "newline_after_select": true,
       "newline_on_join": true,
       "quote_identifiers": false
     },
     "rewrite": {
       "enable_subquery_to_cte": false,
       "enable_alias_style_abc": false,
       "enable_alias_style_t_numeric": false
     }
   }

Dialect Defaults
----------------

Each dialect has different default formatting preferences:

**SQL Server (T-SQL)**

- Uppercase keywords: ``true``
- Quote identifiers: ``[brackets]``

**PostgreSQL**

- Uppercase keywords: ``false``
- Quote identifiers: ``"double quotes"`` (when needed)

**MySQL**

- Uppercase keywords: varies
- Quote identifiers: ``backticks`` (when needed)

**Oracle (PL/SQL)**

- Uppercase keywords: ``true``
- Quote identifiers: ``"double quotes"``

**SQLite**

- Uppercase keywords: ``false``
- Quote identifiers: minimal

Locations
---------

**User Rulebooks**
   ``~/.sqltidy/rulebooks/sqltidy_{dialect}.json``
   
   Customizations stored here take precedence.

**Bundled Rulebooks**
   ``{package}/sqltidy/rulebooks/sqltidy_{dialect}.json``
   
   Package defaults used when no user rulebook exists.

**Auto-Generated**
   When no file exists, generated from rule metadata on-demand.

API Reference
-------------

.. currentmodule:: sqltidy.cli.dialog

.. autosummary::
   :toctree: ../_autosummary
   :nosignatures:

   create_rulebook
   list_rulebooks
   edit_rulebook
   reset_rulebook
   update_rulebook
   load_rulebook_file

See Also
--------

- :doc:`tidy` - Apply rulebook formatting
- :doc:`rewrite` - Apply rulebook transformations
- :doc:`rules` - Manage custom rule plugins
