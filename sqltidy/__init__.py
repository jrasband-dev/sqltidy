__version__ = "0.5.0"

from .api import (
    tidy_sql,
    rewrite_sql,
    tidy_and_rewrite_sql,
)
from .rulebook import SQLTidyConfig, SUPPORTED_DIALECTS


# Alias for backwards compatibility - just reference the same function
format_sql = tidy_and_rewrite_sql


__all__ = [
    # Main formatting functions
    "tidy_sql",
    "rewrite_sql",
    "tidy_and_rewrite_sql",
    "format_sql",  # Backwards compatibility
    # Configuration
    "SQLTidyConfig",
    "SUPPORTED_DIALECTS",
    # Version
    "__version__",
]
