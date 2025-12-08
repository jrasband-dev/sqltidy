Creating Plugins
=================

Overview
--------

SQLTidy supports extending functionality through custom rule plugins. This allows you to create custom formatting rules that can be registered and applied to your SQL code.

Base Rule Class
---------------

All plugins must inherit from the ``BaseRule`` class:

.. automodule:: sqltidy.rules.base
   :members:
   :undoc-members:
   :show-inheritance:

Creating a Custom Plugin
------------------------

Here's an example of creating a custom rule:

.. code-block:: python

   from sqltidy.rules.base import BaseRule
   
   class UppercaseKeywordsRule(BaseRule):
       """Convert all SQL keywords to uppercase."""
       
       def apply(self, tokens):
           """
           Args:
               tokens: List of tokens from the SQL string
               
           Returns:
               List of formatted tokens
           """
           for token in tokens:
               if token.type == 'keyword':
                   token.value = token.value.upper()
           return tokens

Registering Your Plugin
-----------------------

Once you've created your custom rule, register it at runtime:

.. code-block:: python

   from sqltidy import register_plugin, format_sql
   
   # Create and register the plugin
   my_rule = UppercaseKeywordsRule()
   register_plugin(my_rule)
   
   # Format SQL - your custom rule will be applied
   sql = "select * from users"
   formatted = format_sql(sql)

Clearing Plugins
----------------

To clear all registered plugins:

.. code-block:: python

   from sqltidy import clear_plugins
   
   clear_plugins()

Best Practices
--------------

1. **Inherit from BaseRule**: All custom rules should inherit from ``sqltidy.rules.base.BaseRule``
2. **Implement the apply method**: Your rule must implement the ``apply(tokens)`` method
3. **Don't modify in place**: Return a new list of tokens rather than modifying the input
4. **Document your rule**: Add docstrings to explain what your rule does
5. **Test thoroughly**: Test your rules with various SQL statements

Example: Complete Plugin
------------------------

Here's a more complete example of a custom plugin:

.. code-block:: python

   from sqltidy.rules.base import BaseRule
   
   class NormalizeWhitespaceRule(BaseRule):
       """Normalize whitespace in SQL strings."""
       
       def __init__(self):
           super().__init__()
           self.name = "normalize_whitespace"
       
       def apply(self, tokens):
           """
           Normalize whitespace between tokens.
           
           Args:
               tokens: List of tokens from SQL
               
           Returns:
               List of tokens with normalized whitespace
           """
           result = []
           for i, token in enumerate(tokens):
               result.append(token)
               # Add single space after tokens (except last)
               if i < len(tokens) - 1 and token.type != 'whitespace':
                   result.append(self._create_whitespace_token(' '))
           return result
       
       def _create_whitespace_token(self, value):
           """Helper method to create whitespace tokens."""
           # Implement based on your token structure
           pass

For more information about the base rule structure, see the :doc:`api` documentation.
