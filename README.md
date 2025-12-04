# SQL Server Formatter

A lightweight SQL Server–focused SQL formatting library with plugin support.

## Quick Start
```python
from sqlserver_formatter import format_sql
print(format_sql("select id from users"))
```

## Plugins
```python
from sqlserver_formatter import register_plugin
import plugins_example.compact_plugin as compact
register_plugin(compact)
```
