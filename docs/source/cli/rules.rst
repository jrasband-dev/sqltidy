``sqltidy rules`` - Manage Custom Rules
========================================

Manage custom formatting and rewrite rule plugins.

Synopsis
--------

.. code-block:: bash

   sqltidy rules {add,list,remove} [OPTIONS]

Description
-----------

Custom rule plugins extend SQLTidy's formatting and transformation capabilities.
Rules are Python files stored in ``~/.sqltidy/rules/`` and automatically loaded
when SQLTidy runs.

Subcommands
-----------

``add``
~~~~~~~

Add a custom rule file to the user rules directory.

**Synopsis:**

.. code-block:: bash

   sqltidy rules add RULE_FILE

**Arguments:**

``RULE_FILE``
   Path to the Python file containing custom rule(s).

**Examples:**

.. code-block:: bash

   # Add a rule file
   sqltidy rules add my_custom_rule.py
   
   # Add from another directory
   sqltidy rules add "C:\Dev\sql_rules\special_formatter.py"

**Behavior:**

- Copies the file to ``~/.sqltidy/rules/``
- Validates the file is valid Python (basic check)
- File is automatically loaded on next SQLTidy run

``list``
~~~~~~~~

List all installed custom rules.

**Synopsis:**

.. code-block:: bash

   sqltidy rules list

**Examples:**

.. code-block:: bash

   sqltidy rules list

**Output Example:**

.. code-block:: text

   Custom Rule Files
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Location: C:\Users\user\.sqltidy\rules
   
   📜 Rules (2 files)
   ├── remove_semicolons.py
   │   └── 1.2 KB
   └── uppercase_table_names.py
       └── 2.4 KB

``remove``
~~~~~~~~~~

Remove a custom rule file.

**Synopsis:**

.. code-block:: bash

   sqltidy rules remove RULE_NAME

**Arguments:**

``RULE_NAME``
   Name of the rule file to remove (e.g., ``my_rule.py``).

**Examples:**

.. code-block:: bash

   sqltidy rules remove my_custom_rule.py

**Behavior:**

- Deletes the file from ``~/.sqltidy/rules/``
- Rule will no longer be loaded on next run
- Does not affect bundled rules

Creating Custom Rules
---------------------

Rules are Python functions decorated with ``@sqltidy_rule``:

**Example: Remove Trailing Semicolons**

.. code-block:: python

   # File: ~/.sqltidy/rules/remove_semicolons.py
   from sqltidy.plugins import sqltidy_rule
   
   @sqltidy_rule(
       rule_type="tidy",
       order=100,
       name="RemoveSemicolonsRule"
   )
   def remove_semicolons(tokens, ctx):
       """Remove trailing semicolons from SQL statements."""
       if tokens and tokens[-1].value == ';':
           return tokens[:-1]
       return tokens

**Example: Uppercase Table Names**

.. code-block:: python

   # File: ~/.sqltidy/rules/uppercase_tables.py
   from sqltidy.plugins import sqltidy_rule
   from sqltidy.rules.base import ConfigField
   
   @sqltidy_rule(
       rule_type="tidy",
       order=50,
       config_fields={
           "uppercase_table_names": ConfigField(
               name="uppercase_table_names",
               field_type=bool,
               default=True,
               description="Convert table names to UPPERCASE"
           )
       }
   )
   def uppercase_table_names(tokens, ctx):
       """Convert table names to uppercase."""
       if not ctx.config.get_tidy("uppercase_table_names", True):
           return tokens
       
       result = []
       for i, token in enumerate(tokens):
           if token.type == 'identifier' and is_table_name(token, tokens, i):
               token.value = token.value.upper()
           result.append(token)
       return result
   
   def is_table_name(token, tokens, index):
       """Check if token is a table name."""
       # Look for FROM, JOIN keywords before this token
       if index > 0:
           prev = tokens[index - 1]
           if prev.type == 'keyword' and prev.value.upper() in ('FROM', 'JOIN'):
               return True
       return False

Rule Decorator Parameters
-------------------------

``rule_type``
   Type of rule: ``"tidy"`` for formatting, ``"rewrite"`` for transformations.
   
   **Required**

``order``
   Execution order (lower runs first). Use 0-100 for tidy, 100+ for rewrite.
   
   **Default:** 50

``supported_dialects``
   Set of dialect names this rule applies to. If None, applies to all.
   
   **Default:** None (all dialects)
   
   **Example:**
   
   .. code-block:: python
   
      supported_dialects={'sqlserver', 'postgresql'}

``name``
   Custom class name for the rule. Auto-generated from function name if omitted.
   
   **Example:**
   
   .. code-block:: python
   
      name="SpecialFormattingRule"

``config_fields``
   Dictionary of ConfigField objects for rulebook integration.
   
   **Example:**
   
   .. code-block:: python
   
      config_fields={
          "my_option": ConfigField(
              name="my_option",
              field_type=bool,
              default=True,
              description="Enable my custom option"
          )
      }

Rule Function Signature
-----------------------

All rule functions must accept these parameters:

.. code-block:: python

   def my_rule(tokens, ctx):
       """
       Args:
           tokens: List of Token objects representing the SQL
           ctx: FormatterContext with config, dialect, indent info
       
       Returns:
           List of Token objects (modified or original)
       """
       return tokens

Token Object
~~~~~~~~~~~~

Each token has:

- ``value``: String content (e.g., ``"SELECT"``)
- ``type``: Token type (e.g., ``"keyword"``, ``"identifier"``, ``"whitespace"``)
- ``position``: Character position in original SQL

FormatterContext
~~~~~~~~~~~~~~~~

- ``ctx.config``: SQLTidyConfig with rulebook settings
- ``ctx.dialect``: Dialect object (keywords, data types, etc.)
- ``ctx.indent_string``: Current indentation string
- ``ctx.indent_level``: Current indentation depth

Testing Rules
-------------

After adding a rule:

1. Verify it loads:

   .. code-block:: bash
   
      sqltidy rules list

2. Test on sample SQL:

   .. code-block:: bash
   
      echo "select * from users;" | sqltidy tidy

3. Sync rulebooks to add config fields:

   .. code-block:: bash
   
      sqltidy rulebooks sync all

4. Edit rulebook to configure:

   .. code-block:: bash
   
      sqltidy rulebooks edit sqlserver

Best Practices
--------------

1. **Return new token list:** Don't modify tokens in place
2. **Check config:** Respect user's rulebook settings
3. **Handle edge cases:** Empty token lists, malformed SQL
4. **Document thoroughly:** Add clear docstrings
5. **Test extensively:** Try various SQL patterns
6. **Use appropriate order:** Ensure rules run in logical sequence

Locations
---------

**User Rules Directory**
   ``~/.sqltidy/rules/``
   
   Custom rule files stored here are automatically loaded.

**Rule File Naming**
   - Use ``.py`` extension
   - Avoid starting with ``_`` (private files skipped)
   - Use descriptive names: ``remove_comments.py``, ``add_schema_prefix.py``

API Reference
-------------

.. currentmodule:: sqltidy.cli.dialog

.. autosummary::
   :toctree: ../_autosummary
   :nosignatures:

   add_rule
   list_rules
   remove_rule

.. currentmodule:: sqltidy.plugins

.. autosummary::
   :toctree: ../_autosummary
   :nosignatures:

   sqltidy_rule
   register_rule_class
   load_rule_file
   load_rules_from_directory

See Also
--------

- :doc:`rulebooks` - Configure rule behavior
- :doc:`../plugins` - Detailed plugin development guide
- API: :doc:`../rules` - Rule base classes and helpers
