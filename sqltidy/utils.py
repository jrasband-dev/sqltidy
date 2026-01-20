from pathlib import Path


def get_user_rules_dir() -> Path:
    """Get the path to user's rule directory."""
    return Path.home() / ".sqltidy" / "rules"


def get_user_rulebooks_dir() -> Path:
    """Get the path to user's rulebook directory."""
    return Path.home() / ".sqltidy" / "rulebooks"

def get_bundled_rulebooks_dir() -> Path:
    """Get the path to bundled rulebook templates."""
    return Path(__file__).parent / "rulebooks"


def get_rulebook_path(dialect: str) -> Path:
    """
    Get the path to a rulebook file, checking user directory first, then bundled.

    Args:
        dialect: SQL dialect name

    Returns:
        Path to the rulebook file (user rulebook if exists, otherwise bundled)
    """
    user_path = get_user_rulebooks_dir() / f"sqltidy_{dialect}.json"
    if user_path.exists():
        return user_path
    return get_bundled_rulebook_path(dialect)


def get_bundled_rulebook_path(dialect: str) -> Path:
    """
    Get the path to a bundled rulebook template for a specific dialect.

    Args:
        dialect: SQL dialect name

    Returns:
        Path to the bundled rulebook file
    """
    return get_bundled_rulebooks_dir() / f"sqltidy_{dialect}.json"


def get_default_filename(dialect: str) -> str:
    """Get default rulebook filename for a dialect."""
    return f"sqltidy_{dialect}.json"
