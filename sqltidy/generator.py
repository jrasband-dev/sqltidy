"""
Interactive configuration generator for sqltidy.
Generates config files that can override default settings.
"""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Any
from .config import TidyConfig, RewriteConfig


TIDY_DESCRIPTIONS = {
    "uppercase_keywords": "Convert SQL keywords to uppercase? (e.g., SELECT, FROM, WHERE)",
    "newline_after_select": "Add newline after SELECT keyword?",
    "compact": "Use compact formatting (reduce unnecessary whitespace)?",
    "leading_commas": "Use leading commas in column lists? (e.g., col1\\n  , col2\\n  , col3)",
    "indent_select_columns": "Indent SELECT columns on separate lines?",
}

REWRITE_DESCRIPTIONS = {
    "enable_subquery_to_cte": "Convert subqueries to Common Table Expressions (CTEs)?",
    "enable_alias_style_abc": "Apply uppercase A, B, C ... table aliases?",
    "enable_alias_style_t_numeric": "Apply uppercase T1, T2, T3 ... table aliases?",
}


def prompt_yes_no(question: str, default: bool = True) -> bool:
    """
    Prompt user for a yes/no question.
    
    Args:
        question: The question to ask
        default: The default value if user just presses enter
    
    Returns:
        bool: The user's choice
    """
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


def generate_tidy_config() -> Dict[str, Any]:
    """
    Interactively generate a TidyConfig.
    Automatically includes any new boolean fields added to TidyConfig.
    """
    print("\n" + "=" * 60)
    print("TIDY CONFIGURATION GENERATOR")
    print("=" * 60)
    print("Configure SQL formatting rules for the 'tidy' command.\n")
    
    config = {}
    default_config = asdict(TidyConfig())

    for field_name, default_value in default_config.items():
        if not isinstance(default_value, bool):
            continue  # only prompt for boolean options
        question = TIDY_DESCRIPTIONS.get(
            field_name,
            f"Enable {field_name.replace('_', ' ')}?"
        )
        config[field_name] = prompt_yes_no(question, default=default_value)
    
    return config


def generate_rewrite_config() -> Dict[str, Any]:
    """
    Interactively generate a RewriteConfig.
    Automatically includes any new boolean fields added to RewriteConfig.
    """
    print("\n" + "=" * 60)
    print("REWRITE CONFIGURATION GENERATOR")
    print("=" * 60)
    print("Configure SQL rewriting rules for the 'rewrite' command.\n")
    
    config = {}
    default_config = asdict(RewriteConfig())
    
    for field_name, default_value in default_config.items():
        if not isinstance(default_value, bool):
            continue  # only prompt for boolean options
        question = REWRITE_DESCRIPTIONS.get(
            field_name,
            f"Enable {field_name.replace('_', ' ')}?"
        )
        config[field_name] = prompt_yes_no(question, default=default_value)
    
    return config


def select_config_type() -> str:
    """
    Prompt user to select which config type to generate.
    
    Returns:
        str: "tidy" or "rewrite"
    """
    print("\n" + "=" * 60)
    print("SQLTIDY CONFIGURATION GENERATOR")
    print("=" * 60)
    print("\nSelect which configuration to generate:\n")
    print("1. Tidy configuration")
    print("2. Rewrite configuration")
    
    while True:
        choice = input("\nEnter your choice (1-2): ").strip()
        if choice == "1":
            return "tidy"
        elif choice == "2":
            return "rewrite"
        print("Please enter 1 or 2")


def get_output_filename(config_type: str) -> str:
    """
    Prompt user for output filename.
    
    Args:
        config_type: Type of config ("tidy" or "rewrite")
    
    Returns:
        str: Output filename
    """
    if config_type == "tidy":
        default = "tidy_config.json"
    else:
        default = "rewrite_config.json"
    
    filename = input(f"\nOutput filename [{default}]: ").strip()
    return filename if filename else default


def save_config(config_data: Dict[str, Any], filename: str) -> Path:
    """
    Save configuration to a JSON file.
    
    Args:
        config_data: Configuration dictionary
        filename: Output filename
    
    Returns:
        Path: Path to the saved file
    """
    filepath = Path(filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)
    
    return filepath


def run_generator():
    """
    Run the interactive configuration generator.
    """
    try:
        config_type = select_config_type()
        
        if config_type == "tidy":
            config_data = generate_tidy_config()
        else:
            config_data = generate_rewrite_config()
        
        # Get output filename
        output_file = get_output_filename(config_type)
        
        # Save config
        filepath = save_config(config_data, output_file)
        
        print("\n" + "=" * 60)
        print("✓ Configuration saved successfully!")
        print(f"File: {filepath.absolute()}")
        print("=" * 60)
        print("\nUsage:")
        if config_type == "tidy":
            print(f"  sqltidy tidy -cfg {output_file} <input_file>")
        else:
            print(f"  sqltidy rewrite -cfg {output_file} <input_file>")
        print()
        
    except KeyboardInterrupt:
        print("\n\nConfiguration generation cancelled.")
        return
    except Exception as e:
        print(f"\nError: {e}")
        raise


def load_config_file(filepath: str) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.
    
    Args:
        filepath: Path to the configuration file
    
    Returns:
        dict: Configuration data
    """
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)
