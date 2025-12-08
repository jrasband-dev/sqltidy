"""
Interactive configuration generator for sqltidy.
Generates config files that can override default settings.
"""

import json
from pathlib import Path
from typing import Dict, Any
from .config import TidyConfig, RewriteConfig


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
    
    Returns:
        dict: Configuration dictionary with TidyConfig settings
    """
    print("\n" + "=" * 60)
    print("TIDY CONFIGURATION GENERATOR")
    print("=" * 60)
    print("Configure SQL formatting rules for the 'tidy' command.\n")
    
    config = {}
    
    # Get default values from TidyConfig dataclass
    default_config = TidyConfig()
    
    print("1. Keyword Formatting")
    config["uppercase_keywords"] = prompt_yes_no(
        "Convert SQL keywords to uppercase? (e.g., SELECT, FROM, WHERE)",
        default=default_config.uppercase_keywords
    )
    
    print("\n2. Select Statement Formatting")
    config["newline_after_select"] = prompt_yes_no(
        "Add newline after SELECT keyword?",
        default=default_config.newline_after_select
    )
    
    print("\n3. Compactness")
    config["compact"] = prompt_yes_no(
        "Use compact formatting (reduce unnecessary whitespace)?",
        default=default_config.compact
    )
    
    print("\n4. Comma Placement")
    config["leading_commas"] = prompt_yes_no(
        "Use leading commas in column lists? (e.g., col1\\n  , col2\\n  , col3)",
        default=default_config.leading_commas
    )
    
    print("\n5. Column Indentation")
    config["indent_select_columns"] = prompt_yes_no(
        "Indent SELECT columns on separate lines?",
        default=default_config.indent_select_columns
    )
    
    return config


def generate_rewrite_config() -> Dict[str, Any]:
    """
    Interactively generate a RewriteConfig.
    
    Returns:
        dict: Configuration dictionary with RewriteConfig settings
    """
    print("\n" + "=" * 60)
    print("REWRITE CONFIGURATION GENERATOR")
    print("=" * 60)
    print("Configure SQL rewriting rules for the 'rewrite' command.\n")
    
    config = {}
    
    # Get default values from RewriteConfig dataclass
    default_config = RewriteConfig()
    
    print("1. Subquery Optimization")
    config["enable_subquery_to_cte"] = prompt_yes_no(
        "Convert subqueries to Common Table Expressions (CTEs)?",
        default=default_config.enable_subquery_to_cte
    )
    
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
