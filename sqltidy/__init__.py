__version__ = "0.6.0"

from .api import ( 
    tidy_sql,
    rewrite_sql,
    tidy_and_rewrite_sql,
)

from .dialects import (
    DIALECTS,
    
)

from .io import read_sql

from .rulebook import SQLTidyConfig

from .utils import (
    get_user_rules_dir, 
    get_user_rulebooks_dir, 
    get_bundled_rulebooks_dir, 
    get_rulebook_path, 
    get_bundled_rulebook_path, 
    get_default_filename,
)

__all__ = [
    # Main formatting functions
    "tidy_sql",
    "rewrite_sql",
    "tidy_and_rewrite_sql",

    # Utils
    "get_user_rules_dir",
    "get_user_rulebooks_dir",
    "get_bundled_rulebooks_dir",
    "get_rulebook_path",
    "get_bundled_rulebook_path",
    "get_default_filename",
    # Configuration
    "SQLTidyConfig",
    "DIALECTS",
    # Version
    "__version__",
    "read_sql",
]
