``sqltidy dialects`` - Explore SQL Dialects
============================================

Explore supported SQL dialects and their keywords, data types, and functions.

Synopsis
--------

.. code-block:: bash

   sqltidy dialects {list,keywords,datatypes,functions} [OPTIONS]

Description
-----------

The ``dialects`` command helps you understand dialect-specific SQL features.
Use it to:

- See which dialects are supported
- View keywords for a specific dialect
- List data types available in a dialect
- Browse built-in functions

Subcommands
-----------

``list``
~~~~~~~~

List all supported SQL dialects.

**Synopsis:**

.. code-block:: bash

   sqltidy dialects list [OPTIONS]

**Options:**

``--format {table,json}``
   Output format.
   
   **Default:** ``table``

**Examples:**

.. code-block:: bash

   # Table format
   sqltidy dialects list
   
   # JSON format
   sqltidy dialects list --format json

**Output Example (table):**

.. code-block:: text

   Supported SQL Dialects
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   
   Dialect       Description
   ─────────────────────────────────────────────
   sqlserver     Microsoft SQL Server (T-SQL)
   postgresql    PostgreSQL
   mysql         MySQL / MariaDB
   oracle        Oracle Database (PL/SQL)
   sqlite        SQLite

**Output Example (json):**

.. code-block:: json

   [
     {
       "name": "sqlserver",
       "description": "Microsoft SQL Server (T-SQL)"
     },
     {
       "name": "postgresql",
       "description": "PostgreSQL"
     },
     {
       "name": "mysql",
       "description": "MySQL / MariaDB"
     },
     {
       "name": "oracle",
       "description": "Oracle Database (PL/SQL)"
     },
     {
       "name": "sqlite",
       "description": "SQLite"
     }
   ]

``keywords``
~~~~~~~~~~~~

Show SQL keywords for a specific dialect.

**Synopsis:**

.. code-block:: bash

   sqltidy dialects keywords DIALECT [OPTIONS]

**Arguments:**

``DIALECT``
   Dialect name: ``sqlserver``, ``postgresql``, ``mysql``, ``oracle``, or ``sqlite``.

**Options:**

``--format {table,json}``
   Output format.
   
   **Default:** ``table``

**Examples:**

.. code-block:: bash

   # View PostgreSQL keywords
   sqltidy dialects keywords postgresql
   
   # JSON format
   sqltidy dialects keywords sqlserver --format json
   
   # Pipe to search
   sqltidy dialects keywords mysql | grep -i "table"

**Output Example:**

.. code-block:: text

   SQL Keywords for POSTGRESQL
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   
   Total keywords: 472
   
   SELECT     FROM       WHERE      GROUP      ORDER
   BY         AS         JOIN       LEFT       RIGHT
   INNER      OUTER      CROSS      ON         USING
   AND        OR         NOT        IN         EXISTS
   BETWEEN    LIKE       ILIKE      CASE       WHEN
   THEN       ELSE       END        IS         NULL
   ...

``datatypes``
~~~~~~~~~~~~~

Show data types for a specific dialect.

**Synopsis:**

.. code-block:: bash

   sqltidy dialects datatypes DIALECT [OPTIONS]

**Arguments:**

``DIALECT``
   Dialect name.

**Options:**

``--format {table,json}``
   Output format.
   
   **Default:** ``table``

**Examples:**

.. code-block:: bash

   # View SQL Server data types
   sqltidy dialects datatypes sqlserver
   
   # Compare dialects
   sqltidy dialects datatypes postgresql > pg_types.txt
   sqltidy dialects datatypes mysql > mysql_types.txt
   diff pg_types.txt mysql_types.txt

**Output Example:**

.. code-block:: text

   Data Types for SQLSERVER
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   
   Total data types: 34
   
   Numeric Types:
     INT, BIGINT, SMALLINT, TINYINT, DECIMAL,
     NUMERIC, FLOAT, REAL, MONEY, SMALLMONEY
   
   String Types:
     VARCHAR, NVARCHAR, CHAR, NCHAR, TEXT,
     NTEXT
   
   Date/Time Types:
     DATETIME, DATETIME2, DATE, TIME,
     SMALLDATETIME, DATETIMEOFFSET
   
   Binary Types:
     VARBINARY, BINARY, IMAGE
   
   Other Types:
     BIT, UNIQUEIDENTIFIER, XML, GEOGRAPHY,
     GEOMETRY, HIERARCHYID, SQL_VARIANT

``functions``
~~~~~~~~~~~~~

Show built-in functions for a specific dialect.

**Synopsis:**

.. code-block:: bash

   sqltidy dialects functions DIALECT [OPTIONS]

**Arguments:**

``DIALECT``
   Dialect name.

**Options:**

``--format {table,json}``
   Output format.
   
   **Default:** ``table``

**Examples:**

.. code-block:: bash

   # View Oracle functions
   sqltidy dialects functions oracle
   
   # JSON output
   sqltidy dialects functions postgresql --format json
   
   # Search for specific functions
   sqltidy dialects functions mysql | grep -i "date"

**Output Example:**

.. code-block:: text

   Built-in Functions for POSTGRESQL
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   
   Total functions: 238
   
   String Functions:
     CONCAT, SUBSTRING, UPPER, LOWER, TRIM,
     LTRIM, RTRIM, LENGTH, POSITION, REPLACE
   
   Numeric Functions:
     ABS, CEIL, FLOOR, ROUND, TRUNC, MOD,
     POWER, SQRT, EXP, LN, LOG
   
   Date/Time Functions:
     NOW, CURRENT_DATE, CURRENT_TIME,
     CURRENT_TIMESTAMP, DATE_TRUNC, EXTRACT,
     AGE, DATE_PART
   
   Aggregate Functions:
     COUNT, SUM, AVG, MIN, MAX, ARRAY_AGG,
     STRING_AGG, JSON_AGG
   
   Window Functions:
     ROW_NUMBER, RANK, DENSE_RANK, NTILE,
     LAG, LEAD, FIRST_VALUE, LAST_VALUE

Dialect Differences
-------------------

SQL Server (T-SQL)
~~~~~~~~~~~~~~~~~~

**Key Features:**

- ``TOP`` clause for limiting results
- ``[]`` brackets for quoting identifiers
- Rich date functions: ``GETDATE()``, ``DATEADD()``, ``DATEDIFF()``
- ``ISNULL()`` for null handling
- Window functions with ``OVER`` clause

**Examples:**

.. code-block:: sql

   -- Top N rows
   SELECT TOP 10 * FROM users
   
   -- Quoted identifiers
   SELECT [User Name] FROM [My Table]
   
   -- Date functions
   SELECT GETDATE(), DATEADD(day, 7, OrderDate)

PostgreSQL
~~~~~~~~~~

**Key Features:**

- ``LIMIT`` and ``OFFSET`` for pagination
- ``""`` double quotes for quoting (when needed)
- Advanced JSON/JSONB support
- Array types and functions
- ``ILIKE`` for case-insensitive matching
- Rich text search capabilities

**Examples:**

.. code-block:: sql

   -- Limit/offset
   SELECT * FROM users LIMIT 10 OFFSET 20
   
   -- Case-insensitive search
   SELECT * FROM users WHERE name ILIKE '%john%'
   
   -- JSON operations
   SELECT data->>'name' FROM json_table
   
   -- Arrays
   SELECT ARRAY[1, 2, 3]

MySQL
~~~~~

**Key Features:**

- Backticks for quoting identifiers
- ``LIMIT`` with optional ``OFFSET``
- Auto-increment with ``AUTO_INCREMENT``
- String concatenation with ``CONCAT()``
- ``IFNULL()`` and ``COALESCE()``

**Examples:**

.. code-block:: sql

   -- Backtick identifiers
   SELECT `user-name` FROM `my table`
   
   -- Auto-increment
   CREATE TABLE users (id INT AUTO_INCREMENT PRIMARY KEY)
   
   -- String functions
   SELECT CONCAT(first_name, ' ', last_name) AS full_name

Oracle (PL/SQL)
~~~~~~~~~~~~~~~

**Key Features:**

- ``ROWNUM`` for row limiting
- ``DUAL`` dummy table
- Rich date arithmetic
- ``NVL()`` for null handling
- Hierarchical queries with ``CONNECT BY``

**Examples:**

.. code-block:: sql

   -- Row limiting
   SELECT * FROM users WHERE ROWNUM <= 10
   
   -- Dual table
   SELECT SYSDATE FROM DUAL
   
   -- Hierarchical query
   SELECT * FROM employees
   CONNECT BY PRIOR employee_id = manager_id
   START WITH manager_id IS NULL

SQLite
~~~~~~

**Key Features:**

- Minimal data types (dynamic typing)
- ``LIMIT`` with optional ``OFFSET``
- Limited built-in functions
- ``AUTOINCREMENT`` for primary keys
- Lightweight and embedded

**Examples:**

.. code-block:: sql

   -- Limit
   SELECT * FROM users LIMIT 10 OFFSET 5
   
   -- Auto-increment
   CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT)
   
   -- Date functions (limited)
   SELECT datetime('now'), date('now')

Use Cases
---------

Migration Planning
~~~~~~~~~~~~~~~~~~

Compare keywords and functions between dialects:

.. code-block:: bash

   # Compare keywords
   sqltidy dialects keywords sqlserver > sqlserver_keywords.txt
   sqltidy dialects keywords postgresql > postgresql_keywords.txt
   diff sqlserver_keywords.txt postgresql_keywords.txt

Learning
~~~~~~~~

Explore unfamiliar dialects:

.. code-block:: bash

   # Learn Oracle functions
   sqltidy dialects functions oracle | less
   
   # Search for specific capability
   sqltidy dialects functions postgresql | grep -i "json"

Validation
~~~~~~~~~~

Check if a keyword/function exists in a dialect:

.. code-block:: bash

   # Does PostgreSQL have ISNULL?
   sqltidy dialects functions postgresql | grep -i "isnull"
   
   # What about IFNULL?
   sqltidy dialects functions mysql | grep -i "ifnull"

API Reference
-------------

.. currentmodule:: sqltidy.cli.core

.. autosummary::
   :toctree: ../_autosummary
   :nosignatures:

   handle_dialects_command

.. currentmodule:: sqltidy.dialects.registry

.. autosummary::
   :toctree: ../_autosummary
   :nosignatures:

   get_dialect
   list_dialects
   is_dialect_available

See Also
--------

- :doc:`../dialects` - Dialect system architecture
- :doc:`tidy` - Format with dialect-specific rules
- :doc:`rulebooks` - Dialect-specific configuration
