"""
Configuration schema utilities for sqltidy.

This module provides utilities to build configuration schemas by introspecting
registered rules. This enables automatic generation of configuration files and
ensures that custom/plugin rules can extend the configuration system.
"""

from typing import Dict, Any
from pathlib import Path
import json
from .rules.base import (
    ConfigField,
    build_config_schema_from_rules,
    generate_config_defaults,
    get_config_descriptions,
)
from .rules.loader import load_rules
from .plugins import get_registered_rules


def build_full_config_schema(include_plugins: bool = True) -> Dict[str, ConfigField]:
    """
    Build complete configuration schema from all available rules.

    This introspects all loaded rules (both built-in and plugins) to build
    a comprehensive configuration schema. Each config field includes metadata
    like default values, descriptions, and dialect-specific overrides.

    Args:
        include_plugins: Whether to include plugin rules in the schema

    Returns:
        Dict mapping config field names to ConfigField metadata

    Example:
        >>> schema = build_full_config_schema()
        >>> print(schema['uppercase_keywords'].description)
        'Convert SQL keywords to UPPERCASE (True) or lowercase (False)'
    """
    # Load built-in rules
    rules = load_rules()

    # Add plugin rules
    if include_plugins:
        plugin_rules = get_registered_rules()
        rules.extend([cls() for cls in plugin_rules])

    return build_config_schema_from_rules(rules)


def generate_dialect_config(
    dialect: str, include_plugins: bool = True
) -> Dict[str, Any]:
    """
    Generate a complete configuration for a specific dialect.

    This creates a config dict with all fields set to appropriate defaults
    based on the dialect. Rules can specify dialect-specific defaults.

    **Auto-loads user plugins:** Automatically loads custom rules from
    ~/.sqltidy/rules/ when include_plugins=True (default).

    Args:
        dialect: SQL dialect name (e.g., 'postgresql', 'sqlserver')
        include_plugins: Whether to include plugin rules (default: True)

    Returns:
        Dict of configuration values ready to be saved as JSON or used directly

    Example:
        >>> config = generate_dialect_config('postgresql')
        >>> print(config['uppercase_keywords'])  # False for PostgreSQL
        False
        >>> config = generate_dialect_config('sqlserver')
        >>> print(config['uppercase_keywords'])  # True for SQL Server
        True
    """
    from .plugins import auto_load_user_rules, get_registered_rules

    rules = load_rules()

    if include_plugins:
        # Auto-load user rules from ~/.sqltidy/rules/
        auto_load_user_rules()

        # Get all registered plugins (includes auto-loaded ones)
        plugin_rules = get_registered_rules()
        rules.extend([cls() for cls in plugin_rules])

    return generate_config_defaults(rules, dialect)


def save_dialect_config_to_json(
    dialect: str, filepath: str, include_plugins: bool = True
):
    """
    Generate and save a dialect configuration to JSON file.

    This is useful for creating or updating bundled configuration files.

    Args:
        dialect: SQL dialect name
        filepath: Output JSON file path
        include_plugins: Whether to include plugin rules

    Example:
        >>> save_dialect_config_to_json('postgresql', 'sqltidy_postgresql.json')
    """
    config = generate_dialect_config(dialect, include_plugins)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def regenerate_all_bundled_configs():
    """
    Regenerate all bundled configuration files from rule metadata.

    Note: With Option 2 implementation, bundled configs are OPTIONAL.
    The system auto-generates configs from rules when no JSON file exists.

    This function is provided for:
    - Development/testing purposes
    - Creating template configs for distribution
    - Backwards compatibility with older systems

    In production, configs are auto-generated on-demand, so running this
    function is not required for the system to work.

    Example:
        >>> regenerate_all_bundled_configs()
        ✓ Generated sqltidy_postgresql.json
        ✓ Generated sqltidy_sqlserver.json
        ...
    """
    from .rulebook import SUPPORTED_DIALECTS

    rulebooks_dir = Path(__file__).parent / "rulebooks"
    rulebooks_dir.mkdir(exist_ok=True)

    for dialect in SUPPORTED_DIALECTS:
        output_file = rulebooks_dir / f"sqltidy_{dialect}.json"
        save_dialect_config_to_json(dialect, str(output_file), include_plugins=False)
        print(f"✓ Generated {output_file.name}")


def get_all_config_descriptions(include_plugins: bool = True) -> Dict[str, str]:
    """
    Get descriptions for all configuration fields.

    This is useful for building interactive configuration tools or
    documentation.

    Args:
        include_plugins: Whether to include plugin rules

    Returns:
        Dict mapping config field names to human-readable descriptions

    Example:
        >>> descriptions = get_all_config_descriptions()
        >>> print(descriptions['leading_commas'])
        'Use leading commas in column lists (e.g., col1\\n  , col2\\n  , col3)?'
    """
    rules = load_rules()

    if include_plugins:
        plugin_rules = get_registered_rules()
        rules.extend([cls() for cls in plugin_rules])

    return get_config_descriptions(rules)


def print_config_schema_summary(include_plugins: bool = True):
    """
    Print a summary of the configuration schema to console.

    Useful for debugging and understanding what config options are available.

    Args:
        include_plugins: Whether to include plugin rules
    """
    schema = build_full_config_schema(include_plugins)

    print("SQLTidy Configuration Schema")
    print("=" * 70)
    print(f"Total config fields: {len(schema)}")
    print()

    for field_name, field_meta in sorted(schema.items()):
        print(f"Field: {field_name}")
        print(f"  Type: {field_meta.field_type.__name__}")
        print(f"  Default: {field_meta.default}")
        print(f"  Description: {field_meta.description}")

        if field_meta.dialect_defaults:
            print("  Dialect Defaults:")
            for dialect, value in sorted(field_meta.dialect_defaults.items()):
                print(f"    {dialect}: {value}")
        print()


if __name__ == "__main__":
    # Allow running as script to regenerate configs
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "summary":
            print_config_schema_summary()
        elif sys.argv[1] == "regenerate":
            print("Regenerating bundled configuration files...")
            regenerate_all_bundled_configs()
            print("\nDone!")
        else:
            print("Usage:")
            print(
                "  python -m sqltidy.config_schema summary      # Print config schema"
            )
            print(
                "  python -m sqltidy.config_schema regenerate   # Regenerate JSON files"
            )
    else:
        print("Regenerating bundled configuration files...")
        regenerate_all_bundled_configs()
        print("\nDone!")
