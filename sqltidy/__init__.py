__version__ = "0.5.0"

from .api import (
    tidy_sql,
    rewrite_sql,
    tidy_and_rewrite_sql,
)
from .rulebook import SQLTidyConfig, SUPPORTED_DIALECTS


__all__ = [
    # Main formatting functions
    "tidy_sql",
    "rewrite_sql",
    "tidy_and_rewrite_sql",
    # Configuration
    "SQLTidyConfig",
    "SUPPORTED_DIALECTS",
    # Version
    "__version__",
]
