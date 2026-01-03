__version__ = "0.4.0"

from .api import (
    tidy_sql,
    rewrite_sql,
    tidy_and_rewrite_sql,
    register_rule,
    clear_rules,
    load_rule,
    load_user_rules,
)
from .config import SQLTidyConfig, SUPPORTED_DIALECTS


__all__ = [
    # Main formatting functions
    "tidy_sql",
    "rewrite_sql",
    "tidy_and_rewrite_sql",
    # rule management
    "register_rule",
    "clear_rules",
    "load_rule",
    "load_user_rules",
    # Configuration
    "SQLTidyConfig",
    "SUPPORTED_DIALECTS",
    # Version
    "__version__",
]
