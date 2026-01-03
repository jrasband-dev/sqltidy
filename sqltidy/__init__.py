__version__ = "0.4.0"

from .api import (
    tidy_sql,
    rewrite_sql,
    tidy_and_rewrite_sql,
    register_plugin,
    clear_plugins,
    load_plugin,
    load_user_plugins,
)
from .config import SQLTidyConfig, SUPPORTED_DIALECTS


__all__ = [
    # Main formatting functions
    "tidy_sql",
    "rewrite_sql",
    "tidy_and_rewrite_sql",
    # Plugin management
    "register_plugin",
    "clear_plugins",
    "load_plugin",
    "load_user_plugins",
    # Configuration
    "SQLTidyConfig",
    "SUPPORTED_DIALECTS",
    # Version
    "__version__",
]
