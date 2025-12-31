Modules Overview
================

This section provides a complete overview of all SQLTidy modules and subpackages.

.. toctree::
   :maxdepth: 3

Main Package
------------

The main SQLTidy package provides the public API for formatting SQL code.

.. autosummary::
   :toctree: _autosummary
   :recursive:

   sqltidy

Core Modules
------------

.. autosummary::
   :toctree: _autosummary

   sqltidy.api
   sqltidy.config
   sqltidy.core
   sqltidy.tokenizer
   sqltidy.generator
   sqltidy.plugins
   sqltidy.cli

Dialects Package
----------------

SQL dialect support for multiple database systems.

.. autosummary::
   :toctree: _autosummary
   :recursive:

   sqltidy.dialects

Rules Package
-------------

Rule-based formatting and rewriting system.

.. autosummary::
   :toctree: _autosummary
   :recursive:

   sqltidy.rules

For detailed API documentation, see :doc:`api`.

For dialect-specific information, see :doc:`dialects`.

For rules documentation, see :doc:`rules`.
