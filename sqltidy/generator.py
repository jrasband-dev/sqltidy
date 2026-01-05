"""
Interactive configuration generator for sqltidy.
Generates dialect-specific config files.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from .rulebook import SQLTidyConfig, SUPPORTED_DIALECTS

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.tree import Tree
    from rich import box
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False
    console = None


def get_user_rulebooks_dir() -> Path:
    """Get the path to user's rulebook directory."""
    return Path.home() / ".sqltidy" / "rulebooks"


def get_bundled_rulebooks_dir() -> Path:
    """Get the path to bundled rulebook templates."""
    return Path(__file__).parent / "rulebooks"


def initialize_user_rulebooks() -> None:
    """
    Initialize user rulebook directory.
    
    If bundled rulebooks exist, copies them to user directory.
    If no bundled rulebooks exist, generates them from rule metadata.
    """
    user_dir = get_user_rulebooks_dir()
    bundled_dir = get_bundled_rulebooks_dir()
    
    # Create user rulebook directory if it doesn't exist
    user_dir.mkdir(parents=True, exist_ok=True)
    
    # Try to copy bundled rulebooks if they exist
    if bundled_dir.exists():
        bundled_rulebooks = list(bundled_dir.glob("sqltidy_*.json"))
        if bundled_rulebooks:
            # Bundled files exist - copy them
            for bundled_rulebook in bundled_rulebooks:
                user_rulebook = user_dir / bundled_rulebook.name
                if not user_rulebook.exists():
                    shutil.copy2(bundled_rulebook, user_rulebook)
            return
    
    # No bundled files - generate from rules
    from .config_schema import save_dialect_config_to_json
    for dialect in SUPPORTED_DIALECTS:
        user_rulebook = user_dir / f"sqltidy_{dialect}.json"
        if not user_rulebook.exists():
            save_dialect_config_to_json(dialect, str(user_rulebook), include_plugins=False)


def get_rulebook_path(dialect: str) -> Path:
    """
    Get the path to a rulebook file, checking user directory first, then bundled.
    
    Args:
        dialect: SQL dialect name
        
    Returns:
        Path to the rulebook file (user rulebook if exists, otherwise bundled)
        Note: May return a path that doesn't exist if bundled files are not present.
              Callers should check existence or use _load_config_for_dialect() instead.
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


# Field descriptions for interactive prompts
FIELD_DESCRIPTIONS = {
    # Tidy/Formatting rules
    "uppercase_keywords": "Convert SQL keywords to uppercase? (e.g., SELECT, FROM, WHERE)",
    "newline_after_select": "Add newline after SELECT keyword?",
    "compact": "Use compact formatting (reduce unnecessary whitespace)?",
    "leading_commas": "Use leading commas in column lists? (e.g., col1\\n  , col2\\n  , col3)",
    "indent_select_columns": "Indent SELECT columns on separate lines?",
    "quote_identifiers": "Quote all identifiers (table/column names)?",
    
    # Rewrite/Transformation rules
    "enable_subquery_to_cte": "Convert subqueries to Common Table Expressions (CTEs)?",
    "enable_alias_style_abc": "Apply uppercase A, B, C ... table aliases?",
    "enable_alias_style_t_numeric": "Apply uppercase T1, T2, T3 ... table aliases?",
}


def prompt_yes_no(question: str, default: Optional[bool] = True) -> Optional[bool]:
    """
    Prompt user for a yes/no question.
    
    Args:
        question: The question to ask
        default: The default value if user just presses enter (can be None)
    
    Returns:
        bool or None: The user's choice
    """
    if default is None:
        default_str = "[y/n]"
    else:
        default_str = "[Y/n]" if default else "[y/N]"
    
    while True:
        response = input(f"{question} {default_str}: ").strip().lower()
        if not response:
            return default
        if response in ("y", "yes"):
            return True
        if response in ("n", "no"):
            return False
        print("Please enter 'y' or 'n'")


def select_dialect() -> str:
    """
    Prompt user to select a SQL dialect.
    
    Returns:
        str: Selected dialect name
    """
    print("\nSelect SQL dialect:\n")
    for i, dialect in enumerate(SUPPORTED_DIALECTS, 1):
        print(f"{i}. {dialect}")
    
    while True:
        choice = input(f"\nEnter your choice (1-{len(SUPPORTED_DIALECTS)}): ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(SUPPORTED_DIALECTS):
                return SUPPORTED_DIALECTS[idx]
        except ValueError:
            pass
        print(f"Please enter a number between 1 and {len(SUPPORTED_DIALECTS)}")


def generate_rulebook_interactive(dialect: str, existing_config: Optional[SQLTidyConfig] = None) -> SQLTidyConfig:
    """
    Interactively generate or update a SQLTidyConfig.
    
    Args:
        dialect: SQL dialect for the configuration
        existing_config: Existing config to update (if None, creates new from defaults)
    
    Returns:
        SQLTidyConfig: The generated or updated configuration
    """
    print("\n" + "=" * 70)
    print(f"CONFIGURATION GENERATOR - {dialect.upper()}")
    print("=" * 70)
    
    if existing_config:
        print("Updating existing configuration. Press Enter to keep current value.\n")
        config = existing_config
    else:
        print("Creating new configuration with dialect defaults.\n")
        config = SQLTidyConfig.get_dialect_defaults(dialect)
    
    # Get current values as dict
    config_dict = config.to_dict()
    
    # Prompt for each field (except dialect)
    print("=" * 70)
    print("FORMATTING RULES (TIDY)")
    print("=" * 70 + "\n")
    
    tidy_fields = ['uppercase_keywords', 'newline_after_select', 'compact', 
                   'leading_commas', 'indent_select_columns', 'quote_identifiers']
    
    for field_name in tidy_fields:
        if field_name not in config_dict:
            continue
        
        current_value = config_dict[field_name]
        question = FIELD_DESCRIPTIONS.get(
            field_name,
            f"Enable {field_name.replace('_', ' ')}?"
        )
        
        new_value = prompt_yes_no(question, default=current_value)
        config_dict[field_name] = new_value
    
    print("\n" + "=" * 70)
    print("TRANSFORMATION RULES (REWRITE)")
    print("=" * 70 + "\n")
    
    rewrite_fields = ['enable_subquery_to_cte', 'enable_alias_style_abc', 
                      'enable_alias_style_t_numeric']
    
    for field_name in rewrite_fields:
        if field_name not in config_dict:
            continue
        
        current_value = config_dict[field_name]
        question = FIELD_DESCRIPTIONS.get(
            field_name,
            f"Enable {field_name.replace('_', ' ')}?"
        )
        
        new_value = prompt_yes_no(question, default=current_value)
        config_dict[field_name] = new_value
    
    # Update dialect to ensure it's set correctly
    config_dict['dialect'] = dialect
    
    return SQLTidyConfig.from_dict(config_dict)


def get_default_filename(dialect: str) -> str:
    """Get default rulebook filename for a dialect."""
    return f"sqltidy_{dialect}.json"


def create_rulebook(dialect: Optional[str] = None, template_file: Optional[str] = None, include_plugins: bool = False) -> None:
    """
    Create a new rulebook file in the user's rulebook directory.
    
    With Option 2, this function now:
    1. Generates config from rule metadata (includes all registered rules)
    2. Saves to ~/.sqltidy/rulebooks/ by default
    3. Optionally includes plugin rules if --include-plugins flag is used
    
    Args:
        dialect: SQL dialect (if None, will prompt)
        template_file: Optional template rulebook file to copy from
        include_plugins: If True, include loaded plugin rules in the config
    """
    try:
        # Select dialect if not provided
        if dialect is None:
            dialect = select_dialect()
        elif dialect not in SUPPORTED_DIALECTS:
            print(f"Error: Unsupported dialect '{dialect}'. Must be one of: {', '.join(SUPPORTED_DIALECTS)}")
            return
        
        # Load template if provided
        base_config = None
        if template_file:
            try:
                print(f"\nLoading template from: {template_file}")
                base_config = SQLTidyConfig.from_file(template_file)
                base_config.dialect = dialect  # Override dialect
            except Exception as e:
                print(f"Warning: Could not load template file: {e}")
                print("Proceeding with auto-generation from rules...\n")
        
        # If no template, generate from rules (Option 2!)
        if base_config is None:
            from .config_schema import generate_dialect_config
            print(f"\nAuto-generating config from rule metadata...")
            if include_plugins:
                print("Including plugin rules in configuration...")
            config_dict = generate_dialect_config(dialect, include_plugins=include_plugins)
            base_config = SQLTidyConfig.from_dict(config_dict)
            print("✓ Config generated from rules")
        
        # Generate rulebook interactively (allows user to customize)
        config = generate_rulebook_interactive(dialect, base_config)
        
        # Get output location - default to user's rulebook directory
        user_dir = get_user_rulebooks_dir()
        user_dir.mkdir(parents=True, exist_ok=True)
        
        default_path = user_dir / f"sqltidy_{dialect}.json"
        print(f"\nDefault location: {default_path}")
        
        filename = input(f"Output filename (or path) [{default_path}]: ").strip()
        if not filename:
            filename = str(default_path)
        
        # Expand to absolute path
        output_path = Path(filename).expanduser().absolute()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save rulebook
        config.save(str(output_path))
        
        print("\n" + "=" * 70)
        print("✓ Rulebook saved successfully!")
        print(f"File: {output_path}")
        if include_plugins:
            print("Note: Plugin rules included in configuration")
        print("=" * 70)
        print("\nUsage:")
        print(f"  sqltidy tidy <input_file> -d {dialect}")
        print(f"  sqltidy tidy <input_file> -cfg {output_path}")
        print()
        
    except KeyboardInterrupt:
        print("\n\nRulebook creation cancelled.")
    except Exception as e:
        print(f"\nError: {e}")
        raise


def update_rulebook(rulebook_file: str) -> None:
    """
    Update an existing rulebook file interactively.
    
    Args:
        rulebook_file: Path to existing rulebook file
    """
    try:
        # Load existing rulebook
        print(f"Loading rulebook from: {rulebook_file}")
        existing_config = SQLTidyConfig.from_file(rulebook_file)
        dialect = existing_config.dialect
        
        # Update interactively
        updated_config = generate_rulebook_interactive(dialect, existing_config)
        
        # Save back to same file
        updated_config.save(rulebook_file)
        
        print("\n" + "=" * 70)
        print("✓ Rulebook updated successfully!")
        print(f"File: {Path(rulebook_file).absolute()}")
        print("=" * 70)
        
    except FileNotFoundError:
        print(f"\nError: Rulebook file not found: {rulebook_file}")
    except KeyboardInterrupt:
        print("\n\nRulebook update cancelled.")
    except Exception as e:
        print(f"\nError: {e}")
        raise


def list_rulebooks(directory: str = ".") -> None:
    """
    List rulebook files in user rulebook directory.
    
    Args:
        directory: Directory to search (default: current directory)
    """
    user_dir = get_user_rulebooks_dir()
    
    print(f"\nUser rulebook directory: {user_dir}\n")
    
    # Check if directory exists
    if not user_dir.exists():
        print("Directory does not exist yet.")
        print(f"\nTip: Create a rulebook with 'sqltidy rulebooks create -d <dialect>'")
        return
    
    # List all files in the user rulebook directory
    all_files = list(user_dir.glob("*"))
    
    if not all_files:
        print("Directory is empty.")
        print(f"\nTip: Create a rulebook with 'sqltidy rulebooks create -d <dialect>'")
        return
    
    # Separate rulebook files from other files
    rulebook_files = [f for f in all_files if f.name.startswith("sqltidy_") and f.name.endswith(".json")]
    other_files = [f for f in all_files if f not in rulebook_files]
    
    if rulebook_files:
        print("Rulebook files:\n")
        for rulebook_file in sorted(rulebook_files):
            try:
                cfg = SQLTidyConfig.from_file(str(rulebook_file))
                print(f"  • {rulebook_file.name} (dialect: {cfg.dialect})")
            except Exception as e:
                print(f"  • {rulebook_file.name} (invalid/unreadable: {e})")
    
    if other_files:
        print("\nOther files:\n")
        for file in sorted(other_files):
            file_type = "directory" if file.is_dir() else "file"
            print(f"  • {file.name} ({file_type})")


def edit_rulebook(rulebook_name: Optional[str] = None) -> None:
    """
    Edit an existing rulebook file in the user's rulebook directory.
    Opens the file in the system's default editor.
    
    Note: This only edits existing files. Use 'sqltidy rulebooks create' to create new rulebooks.
    
    Args:
        rulebook_name: Name of the rulebook file or dialect (e.g., 'postgresql' or 'sqltidy_postgresql.json')
    """
    user_dir = get_user_rulebooks_dir()
    
    # Check if user directory exists
    if not user_dir.exists():
        print("\nNo user rulebooks found.")
        print(f"\nTip: Create a rulebook with 'sqltidy rulebooks create -d <dialect>'")
        return
    
    # Get all existing user rulebooks
    existing_user_rulebooks = list(user_dir.glob("sqltidy_*.json"))
    
    if not existing_user_rulebooks:
        print("\nNo user rulebooks found.")
        print(f"\nUser rulebook directory: {user_dir}")
        print(f"\nTip: Create a rulebook with 'sqltidy rulebooks create -d <dialect>'")
        return
    
    # Build list of existing rulebooks
    available_options = {}
    
    for rulebook_file in existing_user_rulebooks:
        try:
            cfg = SQLTidyConfig.from_file(str(rulebook_file))
            dialect = cfg.dialect
            available_options[dialect] = rulebook_file
        except Exception:
            # Use filename as fallback
            name = rulebook_file.stem.replace('sqltidy_', '')
            available_options[name] = rulebook_file
    
    # If no rulebook specified, let user choose
    if rulebook_name is None:
        print("\nExisting user rulebooks:\n")
        sorted_options = sorted(available_options.items())
        for i, (name, filepath) in enumerate(sorted_options, 1):
            print(f"{i}. {name}")
        
        while True:
            choice = input(f"\nSelect rulebook to edit (1-{len(sorted_options)}): ").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(sorted_options):
                    selected_name, selected_file = sorted_options[idx]
                    break
            except ValueError:
                pass
            print(f"Please enter a number between 1 and {len(sorted_options)}")
    else:
        # Try to find the rulebook by name or dialect
        selected_file = None
        
        # Try as dialect name
        if rulebook_name in available_options:
            selected_file = available_options[rulebook_name]
        # Try as filename
        elif rulebook_name.startswith("sqltidy_") and rulebook_name.endswith(".json"):
            potential_file = user_dir / rulebook_name
            if potential_file.exists():
                selected_file = potential_file
        # Try adding prefix/suffix
        else:
            potential_file = user_dir / f"sqltidy_{rulebook_name}.json"
            if potential_file.exists():
                selected_file = potential_file
        
        if selected_file is None:
            print(f"\nRulebook '{rulebook_name}' not found in user directory.")
            print(f"\nExisting rulebooks: {', '.join(sorted(available_options.keys()))}")
            print(f"\nTip: Create with 'sqltidy rulebooks create -d {rulebook_name}'")
            return
    
    print(f"\n✓ Opening user rulebook: {selected_file}")
    
    # Open in default editor
    try:
        if os.name == 'nt':  # Windows
            os.startfile(selected_file)
        elif os.name == 'posix':  # macOS and Linux
            opener = "open" if os.uname().sysname == "Darwin" else "xdg-open"
            subprocess.run([opener, str(selected_file)])
        
        print(f"\nTip: This file overrides auto-generated defaults.")
        print(f"To revert to auto-generated config, delete: {selected_file}")
    except Exception as e:
        print(f"\nCouldn't open editor automatically: {e}")
        print(f"Please manually edit: {selected_file}")


def reset_rulebook(rulebook_name: Optional[str] = None) -> None:
    """
    Reset a user rulebook to bundled default by removing the user's customization.
    
    Args:
        rulebook_name: Name of the rulebook file or dialect to reset, or 'all' to reset all
    """
    user_dir = get_user_rulebooks_dir()
    
    if not user_dir.exists():
        print("\nNo user rulebooks to reset.")
        return
    
    user_rulebooks = list(user_dir.glob("sqltidy_*.json"))
    
    if not user_rulebooks:
        print("\nNo user rulebooks to reset.")
        return
    
    # Handle 'all' option to reset all rulebooks
    if rulebook_name == 'all':
        print(f"\nFound {len(user_rulebooks)} customized rulebook(s):\n")
        for rulebook_file in sorted(user_rulebooks):
            try:
                cfg = SQLTidyConfig.from_file(str(rulebook_file))
                print(f"  • {cfg.dialect}")
            except Exception:
                print(f"  • {rulebook_file.name}")
        
        confirm = input(f"\nReset all {len(user_rulebooks)} rulebook(s) to bundled defaults? [y/N]: ").strip().lower()
        if confirm in ('y', 'yes'):
            count = 0
            for rulebook_file in user_rulebooks:
                rulebook_file.unlink()
                count += 1
            print(f"\n✓ Reset {count} rulebook(s) to bundled defaults.")
        else:
            print("\nReset cancelled.")
        return
    
    # If no rulebook specified, let user choose
    if rulebook_name is None:
        print("\nCustomized rulebooks:\n")
        for i, rulebook_file in enumerate(sorted(user_rulebooks), 1):
            try:
                cfg = SQLTidyConfig.from_file(str(rulebook_file))
                print(f"{i}. {cfg.dialect}")
            except Exception:
                print(f"{i}. {rulebook_file.name}")
        
        while True:
            choice = input(f"\nSelect rulebook to reset (1-{len(user_rulebooks)}): ").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(user_rulebooks):
                    rulebook_file = sorted(user_rulebooks)[idx]
                    break
            except ValueError:
                pass
            print(f"Please enter a number between 1 and {len(user_rulebooks)}")
    else:
        # Try to find the rulebook by name or dialect
        if rulebook_name in SUPPORTED_DIALECTS:
            rulebook_file = user_dir / f"sqltidy_{rulebook_name}.json"
        elif rulebook_name.startswith("sqltidy_") and rulebook_name.endswith(".json"):
            rulebook_file = user_dir / rulebook_name
        else:
            rulebook_file = user_dir / f"sqltidy_{rulebook_name}.json"
        
        if not rulebook_file.exists():
            print(f"\nNo user customization found for '{rulebook_name}'.")
            return
    
    # Confirm deletion
    confirm = input(f"\nReset {rulebook_file.name} to bundled default? [y/N]: ").strip().lower()
    if confirm in ('y', 'yes'):
        rulebook_file.unlink()
        print(f"\n✓ Reset {rulebook_file.name} to bundled default.")
    else:
        print("\nReset cancelled.")


def update_rulebook(rulebook_name: Optional[str] = None, include_plugins: bool = False) -> None:
    """
    Update an existing rulebook file with new rules that have been added since creation.
    Preserves user's existing settings and only adds new fields from newly registered rules.
    
    Args:
        rulebook_name: Name of the rulebook file or dialect to update, or 'all' to update all
        include_plugins: Whether to include plugin rules in the update
    """
    from .config_schema import generate_dialect_config
    
    user_dir = get_user_rulebooks_dir()
    
    if not user_dir.exists():
        print("\nNo user rulebooks to update.")
        print("Tip: Use 'sqltidy rulebooks create' to create a new rulebook.")
        return
    
    user_rulebooks = list(user_dir.glob("sqltidy_*.json"))
    
    if not user_rulebooks:
        print("\nNo user rulebooks to update.")
        print("Tip: Use 'sqltidy rulebooks create' to create a new rulebook.")
        return
    
    # Handle 'all' option to update all rulebooks
    if rulebook_name == 'all':
        print(f"\nFound {len(user_rulebooks)} user rulebook(s) to update:\n")
        for rulebook_file in sorted(user_rulebooks):
            try:
                cfg = SQLTidyConfig.from_file(str(rulebook_file))
                print(f"  • {cfg.dialect}")
            except Exception:
                print(f"  • {rulebook_file.name}")
        
        confirm = input(f"\nUpdate all {len(user_rulebooks)} rulebook(s) with new rules? [y/N]: ").strip().lower()
        if confirm not in ('y', 'yes'):
            print("\nUpdate cancelled.")
            return
        
        updated_count = 0
        for rulebook_file in sorted(user_rulebooks):
            try:
                # Load existing config
                existing_config = load_rulebook_file(str(rulebook_file))
                dialect = existing_config.get('dialect', 'postgresql')
                
                # Generate fresh config from current rules
                fresh_config = generate_dialect_config(dialect, include_plugins=include_plugins)
                
                # Merge: keep existing values, add new fields
                merged_config = fresh_config.copy()
                merged_config.update(existing_config)
                
                # Check if any new fields were added
                new_fields = set(fresh_config.keys()) - set(existing_config.keys())
                
                if new_fields:
                    # Save updated config
                    with open(rulebook_file, 'w', encoding='utf-8') as f:
                        json.dump(merged_config, f, indent=2)
                    print(f"  ✓ Updated {dialect}: Added {len(new_fields)} new field(s)")
                    for field in sorted(new_fields):
                        print(f"    + {field}")
                    updated_count += 1
                else:
                    print(f"  • {dialect}: Already up-to-date")
            except Exception as e:
                print(f"  ✗ Error updating {rulebook_file.name}: {e}")
        
        if updated_count > 0:
            print(f"\n✓ Updated {updated_count} rulebook(s).")
        else:
            print(f"\nAll rulebooks are already up-to-date!")
        return
    
    # Handle single rulebook update
    if rulebook_name is None:
        print("\nAvailable rulebooks to update:\n")
        for i, rulebook_file in enumerate(sorted(user_rulebooks), 1):
            try:
                cfg = SQLTidyConfig.from_file(str(rulebook_file))
                print(f"{i}. {cfg.dialect}")
            except Exception:
                print(f"{i}. {rulebook_file.name}")
        
        while True:
            choice = input(f"\nSelect rulebook to update (1-{len(user_rulebooks)}): ").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(user_rulebooks):
                    rulebook_file = sorted(user_rulebooks)[idx]
                    break
            except ValueError:
                pass
            print(f"Please enter a number between 1 and {len(user_rulebooks)}")
    else:
        # Try to find the rulebook by name or dialect
        if rulebook_name in SUPPORTED_DIALECTS:
            rulebook_file = user_dir / f"sqltidy_{rulebook_name}.json"
        elif rulebook_name.startswith("sqltidy_") and rulebook_name.endswith(".json"):
            rulebook_file = user_dir / rulebook_name
        else:
            rulebook_file = user_dir / f"sqltidy_{rulebook_name}.json"
        
        if not rulebook_file.exists():
            print(f"\nNo user customization found for '{rulebook_name}'.")
            print(f"Tip: Use 'sqltidy rulebooks create -d {rulebook_name}' to create one.")
            return
    
    # Load existing config
    try:
        existing_config = load_rulebook_file(str(rulebook_file))
        dialect = existing_config.get('dialect', 'postgresql')
    except Exception as e:
        print(f"\nError loading {rulebook_file.name}: {e}")
        return
    
    # Generate fresh config from current rules
    try:
        fresh_config = generate_dialect_config(dialect, include_plugins=include_plugins)
    except Exception as e:
        print(f"\nError generating config for {dialect}: {e}")
        return
    
    # Merge: keep existing values, add new fields
    merged_config = fresh_config.copy()
    merged_config.update(existing_config)
    
    # Check if any new fields were added
    new_fields = set(fresh_config.keys()) - set(existing_config.keys())
    
    if not new_fields:
        print(f"\n✓ {dialect} rulebook is already up-to-date!")
        return
    
    print(f"\nFound {len(new_fields)} new field(s) to add to {dialect} rulebook:")
    for field in sorted(new_fields):
        default_value = fresh_config[field]
        print(f"  + {field} = {default_value}")
    
    confirm = input(f"\nUpdate {rulebook_file.name} with new fields? [Y/n]: ").strip().lower()
    if confirm in ('', 'y', 'yes'):
        # Save updated config
        with open(rulebook_file, 'w', encoding='utf-8') as f:
            json.dump(merged_config, f, indent=2)
        print(f"\n✓ Updated {rulebook_file.name} with {len(new_fields)} new field(s).")
    else:
        print("\nUpdate cancelled.")


def load_rulebook_file(filepath: str) -> Dict[str, Any]:
    """
    Load rulebook from a JSON file.
    
    Args:
        filepath: Path to the rulebook file
    
    Returns:
        dict: Rulebook data
    """
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


# rule Management

def get_user_rules_dir() -> Path:
    """Get the path to user's rule directory."""
    return Path.home() / ".sqltidy" / "rules"


def add_rule(rule_file: str) -> None:
    """
    Add a rule file to the user's rule directory.
    
    Args:
        rule_file: Path to the rule Python file to add
    """
    source_path = Path(rule_file)
    
    if not source_path.exists():
        print(f"Error: rule file not found: {rule_file}")
        return
    
    if not source_path.suffix == '.py':
        print(f"Error: rule file must be a Python file (.py): {rule_file}")
        return
    
    # Validate the rule file by attempting to load it
    try:
        from .plugins import load_rule_file
        rules = load_rule_file(str(source_path))
        if not rules:
            print(f"Warning: No rules found in {rule_file}")
            print("Make sure your file uses @sqltidy_rule decorator or defines BaseRule classes.")
            confirm = input("Add anyway? [y/N]: ").strip().lower()
            if confirm not in ('y', 'yes'):
                print("rule not added.")
                return
    except Exception as e:
        print(f"Error validating rule: {e}")
        confirm = input("Add anyway? [y/N]: ").strip().lower()
        if confirm not in ('y', 'yes'):
            print("rule not added.")
            return
    
    # Create user rules directory if it doesn't exist
    rules_dir = get_user_rules_dir()
    rules_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy rule file to user directory
    dest_path = rules_dir / source_path.name
    
    if dest_path.exists():
        confirm = input(f"rule '{source_path.name}' already exists. Overwrite? [y/N]: ").strip().lower()
        if confirm not in ('y', 'yes'):
            print("rule not added.")
            return
    
    shutil.copy2(source_path, dest_path)
    print(f"\n✓ Added rule: {source_path.name}")
    print(f"  Location: {dest_path}")


def list_rules() -> None:
    """List all built-in and plugin rules."""
    from .rules.loader import load_rules
    
    # Load all built-in rules
    built_in_rules = load_rules()
    
    # Group by rule type
    tidy_rules = [r for r in built_in_rules if getattr(r, 'rule_type', None) == 'tidy']
    rewrite_rules = [r for r in built_in_rules if getattr(r, 'rule_type', None) == 'rewrite']
    other_rules = [r for r in built_in_rules if getattr(r, 'rule_type', None) not in ['tidy', 'rewrite']]
    
    if HAS_RICH:
        # Rich formatted output
        console.print()
        
        # Built-in Tidy Rules
        if tidy_rules:
            tidy_table = Table(title="Built-in Tidy Rules (Formatting)", box=box.ROUNDED, border_style="cyan")
            tidy_table.add_column("Rule Name", style="cyan bold", no_wrap=True)
            tidy_table.add_column("Order", justify="center", style="yellow")
            tidy_table.add_column("Dialects", style="green")
            
            for rule in sorted(tidy_rules, key=lambda r: getattr(r, 'order', 100)):
                rule_name = rule.__class__.__name__
                order = str(getattr(rule, 'order', '?'))
                dialects = getattr(rule, 'supported_dialects', None)
                dialect_info = ', '.join(sorted(dialects)) if dialects else 'all dialects'
                tidy_table.add_row(rule_name, order, dialect_info)
            
            console.print(tidy_table)
            console.print()
        
        # Built-in Rewrite Rules
        if rewrite_rules:
            rewrite_table = Table(title="Built-in Rewrite Rules (Transformations)", box=box.ROUNDED, border_style="magenta")
            rewrite_table.add_column("Rule Name", style="magenta bold", no_wrap=True)
            rewrite_table.add_column("Order", justify="center", style="yellow")
            rewrite_table.add_column("Dialects", style="green")
            
            for rule in sorted(rewrite_rules, key=lambda r: getattr(r, 'order', 100)):
                rule_name = rule.__class__.__name__
                order = str(getattr(rule, 'order', '?'))
                dialects = getattr(rule, 'supported_dialects', None)
                dialect_info = ', '.join(sorted(dialects)) if dialects else 'all dialects'
                rewrite_table.add_row(rule_name, order, dialect_info)
            
            console.print(rewrite_table)
            console.print()
        
        # Other Rules
        if other_rules:
            other_table = Table(title="Other Built-in Rules", box=box.ROUNDED, border_style="blue")
            other_table.add_column("Rule Name", style="blue bold", no_wrap=True)
            other_table.add_column("Order", justify="center", style="yellow")
            
            for rule in sorted(other_rules, key=lambda r: getattr(r, 'order', 100)):
                rule_name = rule.__class__.__name__
                order = str(getattr(rule, 'order', '?'))
                other_table.add_row(rule_name, order)
            
            console.print(other_table)
            console.print()
        
        # Plugin Rules
        rules_dir = get_user_rules_dir()
        
        if not rules_dir.exists() or not list(rules_dir.glob("*.py")):
            console.print(Panel(
                f"[yellow]No plugin rules installed.[/yellow]\n"
                f"[dim]Plugin directory: {rules_dir}[/dim]",
                title="[bold yellow]Plugin Rules",
                border_style="yellow",
                box=box.ROUNDED
            ))
        else:
            rule_files = list(rules_dir.glob("*.py"))
            
            # Create a tree for plugin rules
            tree = Tree(
                f"[bold yellow]Plugin Rules ({len(rule_files)} files)[/bold yellow]",
                guide_style="yellow"
            )
            tree.add(f"[dim]Location: {rules_dir}[/dim]")
            
            for rule_file in sorted(rule_files):
                file_branch = tree.add(f"[yellow]📄 {rule_file.name}[/yellow]")
                
                # Try to load and show rules from the file
                try:
                    from .plugins import load_rule_file
                    rules = load_rule_file(str(rule_file))
                    if rules:
                        for rule_cls in rules:
                            rule = rule_cls()
                            rule_type = getattr(rule, 'rule_type', 'unknown')
                            order = getattr(rule, 'order', '?')
                            dialects = getattr(rule, 'supported_dialects', None)
                            dialect_info = f" ({', '.join(sorted(dialects))})" if dialects else " (all dialects)"
                            
                            type_color = "cyan" if rule_type == "tidy" else "magenta" if rule_type == "rewrite" else "white"
                            file_branch.add(f"[{type_color}]{rule_cls.__name__}[/{type_color}] [dim]type={rule_type}, order={order}{dialect_info}[/dim]")
                except Exception as e:
                    file_branch.add(f"[red]Error loading: {e}[/red]")
            
            console.print()
            console.print(tree)
        
        # Summary
        console.print()
        summary_table = Table(box=box.SIMPLE, show_header=False, border_style="dim")
        summary_table.add_column("Label", style="dim")
        summary_table.add_column("Count", justify="right", style="bold")
        
        summary_table.add_row("Built-in rules:", str(len(built_in_rules)))
        if rules_dir.exists():
            plugin_count = len(list(rules_dir.glob("*.py")))
            summary_table.add_row("Plugin files:", str(plugin_count))
        
        console.print(Panel(summary_table, title="[bold]Summary", border_style="cyan", box=box.ROUNDED))
        console.print()
        
    else:
        # Fallback to plain text output
        print("\n" + "=" * 70)
        print("BUILT-IN RULES")
        print("=" * 70)
        
        if tidy_rules:
            print("\nTidy Rules (formatting):")
            for rule in sorted(tidy_rules, key=lambda r: getattr(r, 'order', 100)):
                rule_name = rule.__class__.__name__
                order = getattr(rule, 'order', '?')
                dialects = getattr(rule, 'supported_dialects', None)
                dialect_info = f" [dialects: {', '.join(sorted(dialects))}]" if dialects else " [all dialects]"
                print(f"  • {rule_name} (order={order}){dialect_info}")
        
        if rewrite_rules:
            print("\nRewrite Rules (transformations):")
            for rule in sorted(rewrite_rules, key=lambda r: getattr(r, 'order', 100)):
                rule_name = rule.__class__.__name__
                order = getattr(rule, 'order', '?')
                dialects = getattr(rule, 'supported_dialects', None)
                dialect_info = f" [dialects: {', '.join(sorted(dialects))}]" if dialects else " [all dialects]"
                print(f"  • {rule_name} (order={order}){dialect_info}")
        
        if other_rules:
            print("\nOther Rules:")
            for rule in sorted(other_rules, key=lambda r: getattr(r, 'order', 100)):
                rule_name = rule.__class__.__name__
                order = getattr(rule, 'order', '?')
                print(f"  • {rule_name} (order={order})")
        
        # Load plugin rules
        print("\n" + "=" * 70)
        print("PLUGIN RULES")
        print("=" * 70)
        
        rules_dir = get_user_rules_dir()
        
        if not rules_dir.exists():
            print("\nNo plugin rules installed.")
            print(f"Plugin directory: {rules_dir}")
        else:
            rule_files = list(rules_dir.glob("*.py"))
            
            if not rule_files:
                print("\nNo plugin rules installed.")
                print(f"Plugin directory: {rules_dir}")
            else:
                print(f"\nInstalled plugin rules ({len(rule_files)}):")
                print(f"Location: {rules_dir}\n")
                
                for rule_file in sorted(rule_files):
                    print(f"  • {rule_file.name}")
                    
                    # Try to load and show rules from the file
                    try:
                        from .plugins import load_rule_file
                        rules = load_rule_file(str(rule_file))
                        if rules:
                            for rule_cls in rules:
                                rule = rule_cls()
                                rule_type = getattr(rule, 'rule_type', 'unknown')
                                order = getattr(rule, 'order', '?')
                                dialects = getattr(rule, 'supported_dialects', None)
                                dialect_info = f" [dialects: {', '.join(sorted(dialects))}]" if dialects else " [all dialects]"
                                print(f"    - {rule_cls.__name__} (type={rule_type}, order={order}){dialect_info}")
                    except Exception as e:
                        print(f"    Error loading: {e}")
        
        print("\n" + "=" * 70)
        print(f"Total: {len(built_in_rules)} built-in rules")
        if rules_dir.exists():
            plugin_count = len(list(rules_dir.glob("*.py")))
            print(f"       {plugin_count} plugin file(s)")
        print("=" * 70 + "\n")


def remove_rule(rule_name: str) -> None:
    """
    Remove a rule from the user's rule directory.
    
    Args:
        rule_name: Name of the rule file to remove
    """
    rules_dir = get_user_rules_dir()
    
    if not rules_dir.exists():
        print("No plugin rules installed.")
        return
    
    # Add .py extension if not provided
    if not rule_name.endswith('.py'):
        rule_name += '.py'
    
    rule_file = rules_dir / rule_name
    
    if not rule_file.exists():
        print(f"Rule not found: {rule_name}")
        print(f"\nUse 'sqltidy rules list' to see installed rules.")
        return
    
    # Confirm deletion
    confirm = input(f"Remove rule '{rule_name}'? [y/N]: ").strip().lower()
    if confirm in ('y', 'yes'):
        rule_file.unlink()
        print(f"\n✓ Removed rule: {rule_name}")
    else:
        print("\nRemoval cancelled.")


