"""
Interactive configuration generator for sqltidy.
Generates dialect-specific config files.
"""

import json
import os
import shutil
import subprocess
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Any, Optional
from .rulebook import SQLTidyConfig, SUPPORTED_DIALECTS


def get_user_rulebooks_dir() -> Path:
    """Get the path to user's rulebook directory."""
    return Path.home() / ".sqltidy" / "rulebooks"


def get_bundled_rulebooks_dir() -> Path:
    """Get the path to bundled rulebook templates."""
    return Path(__file__).parent / "rulebooks"


def initialize_user_rulebooks() -> None:
    """
    Initialize user rulebook directory with all bundled rulebooks if not already present.
    Copies all bundled rulebooks to user directory.
    """
    user_dir = get_user_rulebooks_dir()
    bundled_dir = get_bundled_rulebooks_dir()
    
    # Create user rulebook directory if it doesn't exist
    user_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy all bundled rulebooks if they don't exist in user directory
    if bundled_dir.exists():
        bundled_rulebooks = list(bundled_dir.glob("sqltidy_*.json"))
        for bundled_rulebook in bundled_rulebooks:
            user_rulebook = user_dir / bundled_rulebook.name
            if not user_rulebook.exists():
                shutil.copy2(bundled_rulebook, user_rulebook)


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


def create_rulebook(dialect: Optional[str] = None, template_file: Optional[str] = None) -> None:
    """
    Create a new rulebook file.
    
    Args:
        dialect: SQL dialect (if None, will prompt)
        template_file: Optional template rulebook file to copy from
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
                print("Proceeding with dialect defaults...\n")
        
        # Generate rulebook interactively
        config = generate_rulebook_interactive(dialect, base_config)
        
        # Get output filename
        default_filename = get_default_filename(dialect)
        filename = input(f"\nOutput filename [{default_filename}]: ").strip()
        if not filename:
            filename = default_filename
        
        # Save rulebook
        config.save(filename)
        
        print("\n" + "=" * 70)
        print("✓ Rulebook saved successfully!")
        print(f"File: {Path(filename).absolute()}")
        print("=" * 70)
        print("\nUsage:")
        print(f"  sqltidy tidy -cfg {filename} <input_file>")
        print(f"  sqltidy rewrite -cfg {filename} <input_file>")
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
    # Initialize user rulebooks with bundled defaults
    initialize_user_rulebooks()
    
    user_dir = get_user_rulebooks_dir()
    
    print(f"\nUser rulebook directory: {user_dir}\n")
    
    # List all files in the user rulebook directory
    all_files = list(user_dir.glob("*"))
    
    if not all_files:
        print("Directory is empty.")
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
    Edit a rulebook file in the user's rulebook directory.
    Copies from bundled rulebook if user rulebook doesn't exist yet.
    Opens the file in the system's default editor.
    
    Args:
        rulebook_name: Name of the rulebook file or dialect (e.g., 'postgresql' or 'sqltidy_postgresql.json')
    """
    bundled_dir = get_bundled_rulebooks_dir()
    user_dir = get_user_rulebooks_dir()
    
    if not bundled_dir.exists():
        print("Error: No bundled rulebooks found.")
        return
    
    bundled_rulebooks = list(bundled_dir.glob("sqltidy_*.json"))
    
    if not bundled_rulebooks:
        print("Error: No bundled rulebooks found.")
        return
    
    # If no rulebook specified, let user choose
    if rulebook_name is None:
        print("\nAvailable rulebooks to edit:\n")
        for i, rulebook_file in enumerate(sorted(bundled_rulebooks), 1):
            try:
                cfg = SQLTidyConfig.from_file(str(rulebook_file))
                dialect = cfg.dialect
                # Check if user has customized this rulebook
                user_rulebook = user_dir / rulebook_file.name
                status = " (customized)" if user_rulebook.exists() else ""
                print(f"{i}. {dialect}{status}")
            except Exception:
                print(f"{i}. {rulebook_file.name}")
        
        while True:
            choice = input(f"\nSelect rulebook to edit (1-{len(bundled_rulebooks)}): ").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(bundled_rulebooks):
                    source_file = sorted(bundled_rulebooks)[idx]
                    break
            except ValueError:
                pass
            print(f"Please enter a number between 1 and {len(bundled_rulebooks)}")
    else:
        # Try to find the rulebook by name or dialect
        # First try as dialect name
        if rulebook_name in SUPPORTED_DIALECTS:
            source_file = bundled_dir / f"sqltidy_{rulebook_name}.json"
        # Then try as filename
        elif rulebook_name.startswith("sqltidy_") and rulebook_name.endswith(".json"):
            source_file = bundled_dir / rulebook_name
        # Then try adding the prefix/suffix
        else:
            source_file = bundled_dir / f"sqltidy_{rulebook_name}.json"
        
        if not source_file.exists():
            print(f"Error: Rulebook '{rulebook_name}' not found in bundled rulebooks.")
            print(f"\nAvailable rulebooks: {', '.join([d for d in SUPPORTED_DIALECTS])}")
            return
    
    # Ensure user rulebook directory exists and is initialized with defaults
    initialize_user_rulebooks()
    
    # Path to user's rulebook file
    user_rulebook_file = user_dir / source_file.name
    
    # The file should already exist from initialization, just inform the user
    print(f"\n✓ Opening user rulebook: {user_rulebook_file}")
    
    # Open in default editor
    try:
        if os.name == 'nt':  # Windows
            os.startfile(user_rulebook_file)
        elif os.name == 'posix':  # macOS and Linux
            opener = "open" if os.uname().sysname == "Darwin" else "xdg-open"
            subprocess.run([opener, str(user_rulebook_file)])
        
        print(f"\nThis rulebook will be used instead of the bundled default.")
        print(f"To reset to default, delete: {user_rulebook_file}")
    except Exception as e:
        print(f"\nCouldn't open editor automatically: {e}")
        print(f"Please manually edit: {user_rulebook_file}")


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
    print("\n" + "=" * 70)
    print("BUILT-IN RULES")
    print("=" * 70)
    
    built_in_rules = load_rules()
    
    # Group by rule type
    tidy_rules = [r for r in built_in_rules if getattr(r, 'rule_type', None) == 'tidy']
    rewrite_rules = [r for r in built_in_rules if getattr(r, 'rule_type', None) == 'rewrite']
    other_rules = [r for r in built_in_rules if getattr(r, 'rule_type', None) not in ['tidy', 'rewrite']]
    
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
        print("No Rules installed.")
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


