Building Documentation
======================

This directory contains the Sphinx documentation for SQLTidy.

Prerequisites
-------------

Install the required dependencies:

.. code-block:: bash

   pip install -r ../requirements.txt

Or install Sphinx manually:

.. code-block:: bash

   pip install sphinx sphinx-alabaster-theme

Building the Documentation
---------------------------

**On Linux/macOS:**

.. code-block:: bash

   make html

**On Windows:**

.. code-block:: bash

   .\make.bat html

**Using Sphinx directly (all platforms):**

.. code-block:: bash

   sphinx-build -b html . _build/html

Viewing the Documentation
--------------------------

After building, open the generated HTML documentation:

.. code-block:: bash

   # On Windows
   start _build/html/index.html
   
   # On macOS
   open _build/html/index.html
   
   # On Linux
   xdg-open _build/html/index.html

Documentation Structure
------------------------

- ``conf.py`` - Sphinx configuration file
- ``index.rst`` - Main documentation page
- ``getting_started.rst`` - Getting started guide
- ``api.rst`` - API reference
- ``plugins.rst`` - Plugin development guide
- ``modules.rst`` - Module documentation
- ``_static/`` - Static files (CSS, images, etc.)
- ``_templates/`` - Custom templates
- ``_build/`` - Build output (generated, not in version control)

Writing Documentation
---------------------

Documentation is written in reStructuredText (.rst) format. Key syntax:

**Headers:**

.. code-block:: rst

   Main Section
   ============
   
   Subsection
   ----------
   
   Sub-subsection
   ~~~~~~~~~~~~~~

**Code blocks:**

.. code-block:: rst

   .. code-block:: python
   
      def hello():
          print("Hello, World!")

**Links and references:**

.. code-block:: rst

   `Link text <https://example.com>`_
   :doc:`getting_started`
   :ref:`section-label`

For more information, see the `Sphinx documentation <https://www.sphinx-doc.org/>`_.

Automatic Documentation from Docstrings
----------------------------------------

The documentation automatically includes docstrings from the Python code using Sphinx's autodoc extension. Make sure your Python modules have proper docstrings in Google style format:

.. code-block:: python

   def my_function(arg1, arg2):
       """Brief description.
       
       Longer description here.
       
       Args:
           arg1: Description of arg1
           arg2: Description of arg2
           
       Returns:
           Description of return value
       """
       pass
