import argparse
import sys
import json
from pathlib import Path
from . import __version__
from .api import format_sql, format_sql_folder
from .rulebook import SQLTidyConfig, SUPPORTED_DIALECTS
from .generator import create_rulebook, list_rulebooks, edit_rulebook, reset_rulebook, load_rulebook_file, get_bundled_rulebook_path, get_user_rulebooks_dir, add_rule, list_rules, remove_rule
from .tokenizer import tokenize_with_types, TokenType, is_keyword
from .plugins import load_rule_file, load_rules_from_directory

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


def resolve_rulebook_path(rulebook_ref: str) -> str:
    """
    Resolve a rulebook reference to an actual file path.
    
    Tries in order:
    1. Exact path/filename (if exists)
    2. Dialect name -> user rulebook if exists, otherwise bundled
    3. Filename in user rulebooks, then bundled rulebooks
    
    Args:
        rulebook_ref: Rulebook file reference (path, dialect name, or filename)
    
    Returns:
        str: Resolved path to rulebook file
        
    Raises:
        FileNotFoundError: If rulebook cannot be found
    """
    # Try as direct path first
    rulebook_path = Path(rulebook_ref)
    if rulebook_path.exists():
        return str(rulebook_path)
    
    # Try as dialect name (check user rulebook first, then bundled)
    if rulebook_ref in SUPPORTED_DIALECTS:
        user_path = get_user_rulebooks_dir() / f"sqltidy_{rulebook_ref}.json"
        if user_path.exists():
            return str(user_path)
        bundled_path = get_bundled_rulebook_path(rulebook_ref)
        if bundled_path.exists():
            return str(bundled_path)
    
    # Try as filename in user rulebooks first, then bundled
    if rulebook_ref.endswith('.json'):
        user_path = get_user_rulebooks_dir() / rulebook_ref
        if user_path.exists():
            return str(user_path)
        bundled_path = get_bundled_rulebook_path('').parent / rulebook_ref
        if bundled_path.exists():
            return str(bundled_path)
    
    # Not found anywhere
    raise FileNotFoundError(
        f"Rulebook not found: '{rulebook_ref}'\n"
        f"  Tried: current directory, user rulebooks (~/.sqltidy/rulebooks/), bundled rulebooks\n"
        f"  Hint: Use dialect name (e.g., 'postgresql') or path to rulebook file"
    )


def create_rulebook_from_file(rulebook_file: str) -> SQLTidyConfig:
    """
    Load SQLTidyConfig from a JSON rulebook file.
    Also resolves bundled rulebook references.
    
    Args:
        rulebook_file: Path, dialect name, or filename of the rulebook
    
    Returns:
        SQLTidyConfig: Configuration object with loaded values
    """
    try:
        resolved_path = resolve_rulebook_path(rulebook_file)
        rulebook_data = load_rulebook_file(resolved_path)
        
        # Create SQLTidyConfig with loaded values
        return SQLTidyConfig.from_dict(rulebook_data)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading rulebook file: {e}", file=sys.stderr)
        sys.exit(1)


def load_plugin_rules(args):
    """
    Load plugin rules from command line arguments.
    
    Args:
        args: Parsed command line arguments with rule_files, rule_dirs, rule_modules
        
    Returns:
        list: List of instantiated plugin rule objects
    """
    plugin_rules = []
    
    if hasattr(args, 'rule_files') and args.rule_files:
        for rule_file in args.rule_files:
            try:
                rules = load_rule_file(rule_file)
                plugin_rules.extend([r() for r in rules])
            except Exception as e:
                print(f"Warning: Could not load rule {rule_file}: {e}", file=sys.stderr)
    
    if hasattr(args, 'rule_dirs') and args.rule_dirs:
        for rule_dir in args.rule_dirs:
            try:
                rules = load_rules_from_directory(rule_dir)
                plugin_rules.extend([r() for r in rules])
            except Exception as e:
                print(f"Warning: Could not load rules from {rule_dir}: {e}", file=sys.stderr)
    
    if hasattr(args, 'rule_modules') and args.rule_modules:
        for rule_module in args.rule_modules:
            try:
                rules = load_rule_module(rule_module)
                plugin_rules.extend([r() for r in rules])
            except Exception as e:
                print(f"Warning: Could not load rule module {rule_module}: {e}", file=sys.stderr)
    
    return plugin_rules

def handle_tidy_command(args):
    """Handle the tidy command for file, folder, or stdin input."""
    dialect = args.dialect if args.dialect else 'sqlserver'
    config = create_rulebook_from_file(dialect)
    plugin_rules = load_plugin_rules(args)
    
    if args.input:
        input_path = Path(args.input)
        
        if input_path.is_file():
            # Single file processing
            with open(args.input, "r", encoding="utf-8") as f:
                sql = f.read()
            
            formatted_sql = format_sql(sql, config=config, custom_rules=plugin_rules, rule_type='tidy')
            
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
                custom_rules=plugin_rules,
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
        formatted_sql = format_sql(sql, config=config, custom_rules=plugin_rules, rule_type='tidy')
        print(formatted_sql)


def handle_rewrite_command(args):
    """Handle the rewrite command for file, folder, or stdin input."""
    dialect = args.dialect if args.dialect else 'sqlserver'
    config = create_rulebook_from_file(dialect)
    plugin_rules = load_plugin_rules(args)
    
    if args.input:
        input_path = Path(args.input)
        
        if input_path.is_file():
            # Single file processing
            with open(args.input, "r", encoding="utf-8") as f:
                sql = f.read()
            
            formatted_sql = format_sql(sql, config=config, custom_rules=plugin_rules, rule_type='rewrite')
            
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
                    custom_rules=plugin_rules,
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
                    custom_rules=plugin_rules,
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
        formatted_sql = format_sql(sql, config=config, custom_rules=plugin_rules, rule_type='rewrite')
        
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
    # rulebook Command
    # -------------------
    rulebook_parser = subparsers.add_parser(
        "rulebooks",
        help="Manage rulebooks",
        description="Create, edit, or list rulebook files for sqltidy"
    )
    
    rulebook_subparsers = rulebook_parser.add_subparsers(title='Rulebook Commands', dest="rulebook_command", required=True)
    
    # rulebook create
    create_parser = rulebook_subparsers.add_parser(
        "create",
        help="Create a new rulebook file",
        description="Interactively create a new dialect-specific rulebook file"
    )
    create_parser.add_argument(
        "-d", "--dialect",
        choices=['sqlserver', 'postgresql', 'mysql', 'oracle', 'sqlite'],
        help="SQL dialect for the rulebook"
    )
    create_parser.add_argument(
        "-t", "--template",
        help="Use existing rulebook file as template"
    )
    
    # rulebook list
    list_parser = rulebook_subparsers.add_parser(
        "list",
        help="List rulebook files",
        description="List all sqltidy rulebook files in a directory"
    )
    list_parser.add_argument(
        "-d", "--directory",
        default=".",
        help="Directory to search for rulebook files (default: current directory)"
    )
    
    # rulebook edit
    edit_parser = rulebook_subparsers.add_parser(
        "edit",
        help="Edit a rulebook file",
        description="Edit a rulebook in user directory (~/.sqltidy/rulebooks/). Creates from bundled template if needed."
    )
    edit_parser.add_argument(
        "rulebook",
        nargs="?",
        help="Dialect name (e.g., 'postgresql') or rulebook filename to edit"
    )
    
    # rulebook reset
    reset_parser = rulebook_subparsers.add_parser(
        "reset",
        help="Reset a rulebook to default",
        description="Remove user customization and revert to bundled default"
    )
    reset_parser.add_argument(
        "rulebook",
        nargs="?",
        help="Dialect name (e.g., 'postgresql'), rulebook filename to reset, or 'all' to reset all rulebooks"
    )


    # -------------------
    # rules Command
    # -------------------
    rules_parser = subparsers.add_parser(
        "rules",
        help="Manage custom rules",
        description="Add, list, or remove custom plugin rules"
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

    # rulebooks command
    if args.command == "rulebooks":
        if args.rulebook_command == "create":
            create_rulebook(dialect=args.dialect, template_file=args.template)
        elif args.rulebook_command == "list":
            list_rulebooks(directory=args.directory)
        elif args.rulebook_command == "edit":
            edit_rulebook(rulebook_name=args.rulebook)
        elif args.rulebook_command == "reset":
            reset_rulebook(rulebook_name=args.rulebook)
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
