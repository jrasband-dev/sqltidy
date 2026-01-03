import argparse
import sys
import json
from pathlib import Path
from . import __version__
from .api import format_sql, format_sql_file, format_sql_folder
from .config import SQLTidyConfig, SUPPORTED_DIALECTS
from .generator import create_config, list_configs, edit_config, reset_config, load_config_file, get_bundled_config_path, get_user_configs_dir, add_rule, list_rules, remove_rule
from .tokenizer import tokenize_with_types, TokenType, is_keyword
from .plugins import load_rule_file, load_rules_from_directory, load_rules_module

try:
    from rich.console import Console
    from rich.text import Text
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


def print_logo():
    """Print the sqltidy ASCII art logo."""
    if not HAS_RICH:
        return
        
    console = Console()
    
    logo = Text("""
███████╗ ██████╗ ██╗  ████████╗██╗██████╗ ██╗   ██╗
██╔════╝██╔═══██╗██║  ╚══██╔══╝██║██╔══██╗╚██╗ ██╔╝
███████╗██║   ██║██║     ██║   ██║██║  ██║ ╚████╔╝ 
╚════██║██║▄▄ ██║██║     ██║   ██║██║  ██║  ╚██╔╝  
███████║╚██████╔╝███████╗██║   ██║██████╔╝   ██║   
╚══════╝ ╚══▀▀═╝ ╚══════╝╚═╝   ╚═╝╚═════╝    ╚═╝   
""", style="bold #328a32")
    
    console.print(logo)
    console.print("[#328a32]SQL Formatting & Rewriting Tool[/#328a32]\n")


def resolve_config_path(config_ref: str) -> str:
    """
    Resolve a config reference to an actual file path.
    
    Tries in order:
    1. Exact path/filename (if exists)
    2. Dialect name -> user config if exists, otherwise bundled
    3. Filename in user configs, then bundled configs
    
    Args:
        config_ref: Config file reference (path, dialect name, or filename)
    
    Returns:
        str: Resolved path to config file
        
    Raises:
        FileNotFoundError: If config cannot be found
    """
    # Try as direct path first
    config_path = Path(config_ref)
    if config_path.exists():
        return str(config_path)
    
    # Try as dialect name (check user config first, then bundled)
    if config_ref in SUPPORTED_DIALECTS:
        user_path = get_user_configs_dir() / f"sqltidy_{config_ref}.json"
        if user_path.exists():
            return str(user_path)
        bundled_path = get_bundled_config_path(config_ref)
        if bundled_path.exists():
            return str(bundled_path)
    
    # Try as filename in user configs first, then bundled
    if config_ref.endswith('.json'):
        user_path = get_user_configs_dir() / config_ref
        if user_path.exists():
            return str(user_path)
        bundled_path = get_bundled_config_path('').parent / config_ref
        if bundled_path.exists():
            return str(bundled_path)
    
    # Not found anywhere
    raise FileNotFoundError(
        f"Config not found: '{config_ref}'\n"
        f"  Tried: current directory, user configs (~/.sqltidy/configs/), bundled configs\n"
        f"  Hint: Use dialect name (e.g., 'postgresql') or path to config file"
    )


def create_config_from_file(config_file: str) -> SQLTidyConfig:
    """
    Load SQLTidyConfig from a JSON configuration file.
    Also resolves bundled config references.
    
    Args:
        config_file: Path, dialect name, or filename of the configuration
    
    Returns:
        SQLTidyConfig: Configuration object with loaded values
    """
    try:
        resolved_path = resolve_config_path(config_file)
        config_data = load_config_file(resolved_path)
        
        # Create SQLTidyConfig with loaded values
        return SQLTidyConfig.from_dict(config_data)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading config file: {e}", file=sys.stderr)
        sys.exit(1)


def load_rule_rules(args):
    """
    Load rule rules from command line arguments.
    
    Args:
        args: Parsed command line arguments with rule_files, rule_dirs, rule_modules
        
    Returns:
        list: List of instantiated rule rule objects
    """
    rule_rules = []
    
    if hasattr(args, 'rule_files') and args.rule_files:
        for rule_file in args.rule_files:
            try:
                rules = load_rule_file(rule_file)
                rule_rules.extend([r() for r in rules])
            except Exception as e:
                print(f"Warning: Could not load rule {rule_file}: {e}", file=sys.stderr)
    
    if hasattr(args, 'rule_dirs') and args.rule_dirs:
        for rule_dir in args.rule_dirs:
            try:
                rules = load_rules_from_directory(rule_dir)
                rule_rules.extend([r() for r in rules])
            except Exception as e:
                print(f"Warning: Could not load rules from {rule_dir}: {e}", file=sys.stderr)
    
    if hasattr(args, 'rule_modules') and args.rule_modules:
        for rule_module in args.rule_modules:
            try:
                rules = load_rule_module(rule_module)
                rule_rules.extend([r() for r in rules])
            except Exception as e:
                print(f"Warning: Could not load rule module {rule_module}: {e}", file=sys.stderr)
    
    return rule_rules


def handle_tidy_command(args):
    """Handle the tidy command for file, folder, or stdin input."""
    dialect = args.dialect if args.dialect else 'sqlserver'
    config = create_config_from_file(dialect)
    rule_rules = load_rule_rules(args)
    
    if args.input:
        input_path = Path(args.input)
        
        if input_path.is_file():
            # Single file processing
            with open(args.input, "r", encoding="utf-8") as f:
                sql = f.read()
            
            formatted_sql = format_sql(sql, config=config, custom_rules=rule_rules, rule_type='tidy')
            
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(formatted_sql)
            elif not args.no_in_place:
                with open(args.input, "w", encoding="utf-8") as f:
                    f.write(formatted_sql)
            else:
                print(formatted_sql)
                
        elif input_path.is_dir():
            # Folder processing
            print(f"Processing SQL files in: {input_path}")
            if args.recursive:
                print(f"  Mode: Recursive")
            print(f"  Pattern: {args.pattern}")
            print(f"  Dialect: {dialect}")
            
            results = format_sql_folder(
                folder_path=input_path,
                output_folder=args.output,
                config=config,
                custom_rules=rule_rules,
                rule_type='tidy',
                pattern=args.pattern,
                recursive=args.recursive,
                in_place=not args.no_in_place
            )
            
            print(f"\nResults:")
            print(f"  Total files: {results['total']}")
            print(f"  Successful: {results['success']}")
            print(f"  Failed: {results['failed']}")
            
            if results['errors']:
                print(f"\nErrors:")
                for error in results['errors']:
                    print(f"  {error['file']}: {error['error']}")
            
            if results['failed'] > 0:
                sys.exit(1)
        else:
            print(f"Error: Input path does not exist: {args.input}", file=sys.stderr)
            sys.exit(1)
    else:
        # stdin processing
        if sys.stdin.isatty():
            print("Error: No input file provided and no data piped to stdin.", file=sys.stderr)
            print("Usage: sqltidy tidy <file> or pipe data like: cat file.sql | sqltidy tidy", file=sys.stderr)
            print("Run 'sqltidy tidy --help' for more information.", file=sys.stderr)
            sys.exit(1)
        
        sql = sys.stdin.read()
        formatted_sql = format_sql(sql, config=config, custom_rules=rule_rules, rule_type='tidy')
        print(formatted_sql)


def handle_rewrite_command(args):
    """Handle the rewrite command for file, folder, or stdin input."""
    dialect = args.dialect if args.dialect else 'sqlserver'
    config = create_config_from_file(dialect)
    rule_rules = load_rule_rules(args)
    
    if args.input:
        input_path = Path(args.input)
        
        if input_path.is_file():
            # Single file processing
            with open(args.input, "r", encoding="utf-8") as f:
                sql = f.read()
            
            formatted_sql = format_sql(sql, config=config, custom_rules=rule_rules, rule_type='rewrite')
            
            if args.tidy:
                formatted_sql = format_sql(formatted_sql, config=config, rule_type='tidy')
            
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(formatted_sql)
            elif not args.no_in_place:
                with open(args.input, "w", encoding="utf-8") as f:
                    f.write(formatted_sql)
            else:
                print(formatted_sql)
                
        elif input_path.is_dir():
            # Folder processing
            print(f"Processing SQL files in: {input_path}")
            if args.recursive:
                print(f"  Mode: Recursive")
            print(f"  Pattern: {args.pattern}")
            print(f"  Dialect: {dialect}")
            
            if args.tidy:
                print("  Mode: Rewrite + Tidy")
                results = format_sql_folder(
                    folder_path=input_path,
                    output_folder=args.output,
                    config=config,
                    custom_rules=rule_rules,
                    rule_type='rewrite',
                    pattern=args.pattern,
                    recursive=args.recursive,
                    in_place=not args.no_in_place
                )
                
                if results['success'] > 0:
                    target_folder = Path(args.output) if args.output else input_path
                    tidy_results = format_sql_folder(
                        folder_path=target_folder,
                        output_folder=None,
                        config=config,
                        custom_rules=[],
                        rule_type='tidy',
                        pattern=args.pattern,
                        recursive=args.recursive,
                        in_place=True
                    )
                    results['failed'] += tidy_results['failed']
                    results['errors'].extend(tidy_results['errors'])
            else:
                results = format_sql_folder(
                    folder_path=input_path,
                    output_folder=args.output,
                    config=config,
                    custom_rules=rule_rules,
                    rule_type='rewrite',
                    pattern=args.pattern,
                    recursive=args.recursive,
                    in_place=not args.no_in_place
                )
            
            print(f"\nResults:")
            print(f"  Total files: {results['total']}")
            print(f"  Successful: {results['success']}")
            print(f"  Failed: {results['failed']}")
            
            if results['errors']:
                print(f"\nErrors:")
                for error in results['errors']:
                    print(f"  {error['file']}: {error['error']}")
            
            if results['failed'] > 0:
                sys.exit(1)
        else:
            print(f"Error: Input path does not exist: {args.input}", file=sys.stderr)
            sys.exit(1)
    else:
        # stdin processing
        if sys.stdin.isatty():
            print("Error: No input file provided and no data piped to stdin.", file=sys.stderr)
            print("Usage: sqltidy rewrite <file> or pipe data like: cat file.sql | sqltidy rewrite", file=sys.stderr)
            print("Run 'sqltidy rewrite --help' for more information.", file=sys.stderr)
            sys.exit(1)
        
        sql = sys.stdin.read()
        formatted_sql = format_sql(sql, config=config, custom_rules=rule_rules, rule_type='rewrite')
        
        if args.tidy:
            formatted_sql = format_sql(formatted_sql, config=config, rule_type='tidy')
        
        print(formatted_sql)


def main():
    # Print logo
    print_logo()
    
    parser = argparse.ArgumentParser()
    
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )

    # create subparsers for subcommands
    subparsers = parser.add_subparsers(title='Commands', dest="command", required=True)

    # -------------------
    # tidy Command
    # -------------------
    tidy_parser = subparsers.add_parser(
        name="tidy",
        help="Format a SQL file",
        description="Format SQL with tidy rules."
    )

    tidy_input_group = tidy_parser.add_argument_group(title='Input')
    tidy_input_group.add_argument("input", nargs="?", help="SQL file or folder to format")
    
    tidy_parameter_group = tidy_parser.add_argument_group('Parameters')
    tidy_parameter_group.add_argument("-o", "--output", help="Output file or folder")
    tidy_parameter_group.add_argument("-d", "--dialect",
                                     choices=SUPPORTED_DIALECTS,
                                     help="SQL dialect (sqlserver, postgresql, mysql, oracle, sqlite). Default: sqlserver")
    tidy_parameter_group.add_argument("-r", "--recursive", action="store_true",
                                     help="Process folders recursively")
    tidy_parameter_group.add_argument("--pattern", default="*.sql",
                                     help="File pattern for folder processing (default: *.sql)")
    tidy_parameter_group.add_argument("--no-in-place", action="store_true",
                                     help="Don't modify files in place (requires --output)")
    tidy_parameter_group.add_argument("--summary", action="store_true",
                                     help="Show summary of processed files")
    
    tidy_rule_group = tidy_parser.add_argument_group('rules')
    tidy_rule_group.add_argument("--rule", action="append", dest="rule_files",
                                   help="Load rule from Python file (can be used multiple times)")
    tidy_rule_group.add_argument("--rule-dir", action="append", dest="rule_dirs",
                                   help="Load all rules from directory (can be used multiple times)")
    tidy_rule_group.add_argument("--rule-module", action="append", dest="rule_modules",
                                   help="Import rule module (can be used multiple times)")



    # -------------------
    # rewrite Command
    # -------------------

    rewrite_parser = subparsers.add_parser(
        "rewrite",
        help="Rewrite SQL queries",
        description="Rewrite SQL queries according to specified rules"
    )
    
    
    rewrite_rule_group = rewrite_parser.add_argument_group('rules')
    rewrite_rule_group.add_argument("--rule", action="append", dest="rule_files",
                                      help="Load rule from Python file (can be used multiple times)")
    rewrite_rule_group.add_argument("--rule-dir", action="append", dest="rule_dirs",
                                      help="Load all rules from directory (can be used multiple times)")
    rewrite_rule_group.add_argument("--rule-module", action="append", dest="rule_modules",
                                      help="Import rule module (can be used multiple times)")
    rewrite_input_group = rewrite_parser.add_argument_group(title='Input')
    rewrite_input_group.add_argument("input", nargs="?", help="SQL file or folder to rewrite")
    
    rewrite_parameter_group = rewrite_parser.add_argument_group('Parameters')
    rewrite_parameter_group.add_argument("-o", "--output", help="Output file or folder")
    rewrite_parameter_group.add_argument("-d", "--dialect",
                                        choices=SUPPORTED_DIALECTS,
                                        help="SQL dialect (sqlserver, postgresql, mysql, oracle, sqlite). Default: sqlserver")
    rewrite_parameter_group.add_argument("-r", "--recursive", action="store_true",
                                        help="Process folders recursively")
    rewrite_parameter_group.add_argument("--pattern", default="*.sql",
                                        help="File pattern for folder processing (default: *.sql)")
    rewrite_parameter_group.add_argument("--no-in-place", action="store_true",
                                        help="Don't modify files in place (requires --output)")
    rewrite_parameter_group.add_argument("--summary", action="store_true",
                                        help="Show summary of processed files")
    # Use config.py defaults for rewrite behavior. No CLI enable/disable flags are provided.
    rewrite_parameter_group.add_argument("--tidy", action="store_true", help="Apply tidy rules after rewriting")


    # -------------------
    # config Command
    # -------------------
    config_parser = subparsers.add_parser(
        "config",
        help="Manage configuration files",
        description="Create, edit, or list configuration files for sqltidy"
    )
    
    config_subparsers = config_parser.add_subparsers(title='Config Commands', dest="config_command", required=True)
    
    # config create
    create_parser = config_subparsers.add_parser(
        "create",
        help="Create a new configuration file",
        description="Interactively create a new dialect-specific configuration file"
    )
    create_parser.add_argument(
        "-d", "--dialect",
        choices=['sqlserver', 'postgresql', 'mysql', 'oracle', 'sqlite'],
        help="SQL dialect for the configuration"
    )
    create_parser.add_argument(
        "-t", "--template",
        help="Use existing config file as template"
    )
    
    # config list
    list_parser = config_subparsers.add_parser(
        "list",
        help="List configuration files",
        description="List all sqltidy configuration files in a directory"
    )
    list_parser.add_argument(
        "-d", "--directory",
        default=".",
        help="Directory to search for config files (default: current directory)"
    )
    
    # config edit
    edit_parser = config_subparsers.add_parser(
        "edit",
        help="Edit a configuration file",
        description="Edit a config in user directory (~/.sqltidy/configs/). Creates from bundled template if needed."
    )
    edit_parser.add_argument(
        "config",
        nargs="?",
        help="Dialect name (e.g., 'postgresql') or config filename to edit"
    )
    
    # config reset
    reset_parser = config_subparsers.add_parser(
        "reset",
        help="Reset a configuration to default",
        description="Remove user customization and revert to bundled default"
    )
    reset_parser.add_argument(
        "config",
        nargs="?",
        help="Dialect name (e.g., 'postgresql') or config filename to reset"
    )


    # -------------------
    # rules Command
    # -------------------
    rules_parser = subparsers.add_parser(
        "rules",
        help="Manage custom rules",
        description="Add, list, or remove custom rule rules"
    )
    
    rules_subparsers = rules_parser.add_subparsers(title='Rules Commands', dest="rules_command", required=True)
    
    # rules add
    add_rules_parser = rules_subparsers.add_parser(
        "add",
        help="Add a custom rule",
        description="Add a Python file containing custom rules to the rule directory"
    )
    add_rules_parser.add_argument(
        "rule_file",
        help="Path to the Python rule file to add"
    )
    
    # rules list
    list_rules_parser = rules_subparsers.add_parser(
        "list",
        help="List installed rules",
        description="List all custom rules in the user rule directory"
    )
    
    # rules remove
    remove_rules_parser = rules_subparsers.add_parser(
        "remove",
        help="Remove a rule",
        description="Remove a custom rule from the rule directory"
    )
    remove_rules_parser.add_argument(
        "rule_name",
        help="Name of the rule file to remove (e.g., my_rule.py)"
    )


    # -------------------
    # parse Command
    # -------------------
    parse_parser = subparsers.add_parser(
        "parse",
        help="Parse and analyze SQL tokens",
        description="Tokenize SQL and display detailed token information"
    )
    
    parse_input_group = parse_parser.add_argument_group(title='Input')
    parse_input_group.add_argument("input", nargs="?", help="SQL file to parse")
    
    parse_parameter_group = parse_parser.add_argument_group('Parameters')
    parse_parameter_group.add_argument("-o", "--output", help="Output file for token analysis")
    parse_parameter_group.add_argument("--format", choices=["table", "json", "simple"], default="table",
                                       help="Output format (default: table)")
    parse_parameter_group.add_argument("--show-whitespace", action="store_true",
                                      help="Include whitespace tokens in output")
    parse_parameter_group.add_argument("--keywords-only", action="store_true",
                                      help="Show only SQL keywords")
    parse_parameter_group.add_argument("--stats", action="store_true",
                                      help="Show token statistics")







    # -------------------
    # parse arguments
    # -------------------
    args = parser.parse_args()

    # config command
    if args.command == "config":
        if args.config_command == "create":
            create_config(dialect=args.dialect, template_file=args.template)
        elif args.config_command == "list":
            list_configs(directory=args.directory)
        elif args.config_command == "edit":
            edit_config(config_name=args.config)
        elif args.config_command == "reset":
            reset_config(config_name=args.config)
        return

    # rules command
    if args.command == "rules":
        if args.rules_command == "add":
            add_rule(args.rule_file)
        elif args.rules_command == "list":
            list_rules()
        elif args.rules_command == "remove":
            remove_rule(args.rule_name)
        return

    # parse command
    if args.command == "parse":
        if args.input:
            with open(args.input, "r", encoding="utf-8") as f:
                sql = f.read()
        else:
            # Check if stdin is a TTY (interactive terminal)
            if sys.stdin.isatty():
                print("Error: No input file provided and no data piped to stdin.", file=sys.stderr)
                print("Usage: sqltidy parse <file> or pipe data like: cat file.sql | sqltidy parse", file=sys.stderr)
                print("Run 'sqltidy parse --help' for more information.", file=sys.stderr)
                sys.exit(1)
            sql = sys.stdin.read()

        # Tokenize the SQL
        tokens = tokenize_with_types(sql)
        
        # Filter tokens based on options
        display_tokens = tokens
        if not args.show_whitespace:
            display_tokens = [t for t in tokens if t.type not in (TokenType.WHITESPACE, TokenType.NEWLINE)]
        
        if args.keywords_only:
            display_tokens = [t for t in tokens if t.type == TokenType.KEYWORD]
        
        # Generate output
        output_lines = []
        
        if args.format == "json":
            # JSON format
            token_data = [{"value": t.value, "type": t.type.value} for t in display_tokens]
            output_lines.append(json.dumps(token_data, indent=2))
        
        elif args.format == "simple":
            # Simple format: one token per line
            for token in display_tokens:
                output_lines.append(f"{token.type.value}: {repr(token.value)}")
        
        else:  # table format
            # Calculate column widths
            max_type_len = max(len(t.type.value) for t in display_tokens) if display_tokens else 10
            max_value_len = max(len(repr(t.value)) for t in display_tokens) if display_tokens else 10
            max_type_len = max(max_type_len, 10)
            max_value_len = min(max_value_len, 60)  # Cap at 60 chars
            
            # Header
            output_lines.append("=" * (max_type_len + max_value_len + 10))
            output_lines.append(f"{'Type':<{max_type_len}} | {'Value':<{max_value_len}} | Keyword")
            output_lines.append("-" * (max_type_len + max_value_len + 10))
            
            # Tokens
            for token in display_tokens:
                value_str = repr(token.value)
                if len(value_str) > max_value_len:
                    value_str = value_str[:max_value_len-3] + "..."
                
                is_kw = "✓" if is_keyword(token.value) else ""
                output_lines.append(f"{token.type.value:<{max_type_len}} | {value_str:<{max_value_len}} | {is_kw}")
            
            output_lines.append("=" * (max_type_len + max_value_len + 10))
        
        # Add statistics if requested
        if args.stats:
            output_lines.append("\nToken Statistics:")
            output_lines.append("-" * 40)
            
            # Count by type
            type_counts = {}
            for token in tokens:
                type_counts[token.type] = type_counts.get(token.type, 0) + 1
            
            output_lines.append(f"Total tokens: {len(tokens)}")
            output_lines.append("\nToken distribution:")
            for token_type in sorted(type_counts.keys(), key=lambda t: type_counts[t], reverse=True):
                count = type_counts[token_type]
                pct = count / len(tokens) * 100
                output_lines.append(f"  {token_type.value:12s}: {count:4d} ({pct:5.1f}%)")
            
            # Keyword statistics
            keywords = sorted(set(t.value.upper() for t in tokens if t.type == TokenType.KEYWORD))
            if keywords:
                output_lines.append(f"\nUnique keywords ({len(keywords)}):")
                output_lines.append(f"  {', '.join(keywords)}")
            
            # Identifier statistics
            identifiers = sorted(set(t.value for t in tokens if t.type == TokenType.IDENTIFIER))
            if identifiers:
                output_lines.append(f"\nUnique identifiers ({len(identifiers)}):")
                # Show first 20
                if len(identifiers) <= 20:
                    output_lines.append(f"  {', '.join(identifiers)}")
                else:
                    output_lines.append(f"  {', '.join(identifiers[:20])}")
                    output_lines.append(f"  ... and {len(identifiers) - 20} more")
        
        # Write output
        result = "\n".join(output_lines)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result)
        else:
            print(result)
        
        return

    # tidy command
    if args.command == "tidy":
        handle_tidy_command(args)
        return

    # rewrite command
    if args.command == "rewrite":
        handle_rewrite_command(args)
        return

if __name__ == "__main__":
    main()
