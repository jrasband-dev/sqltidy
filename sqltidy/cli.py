import argparse
import sys
import json
from pathlib import Path
from . import __version__
from .api import format_sql
from .config import SQLTidyConfig, SUPPORTED_DIALECTS
from .generator import create_config, list_configs, edit_config, reset_config, load_config_file, get_bundled_config_path, get_user_configs_dir, add_plugin, list_plugins, remove_plugin
from .tokenizer import tokenize_with_types, TokenType, is_keyword
from .plugins import load_plugin_file, load_plugins_from_directory, load_plugin_module

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
    tidy_input_group.add_argument("input", nargs="?", help="SQL file to format")
    
    tidy_parameter_group = tidy_parser.add_argument_group('Parameters')
    tidy_parameter_group.add_argument("-o", "--output", help="Output file")
    tidy_parameter_group.add_argument("-d", "--dialect",
                                     choices=SUPPORTED_DIALECTS,
                                     help="SQL dialect (sqlserver, postgresql, mysql, oracle, sqlite). Default: sqlserver")
    
    tidy_plugin_group = tidy_parser.add_argument_group('Plugins')
    tidy_plugin_group.add_argument("--plugin", action="append", dest="plugin_files",
                                   help="Load plugin from Python file (can be used multiple times)")
    tidy_plugin_group.add_argument("--plugin-dir", action="append", dest="plugin_dirs",
                                   help="Load all plugins from directory (can be used multiple times)")
    tidy_plugin_group.add_argument("--plugin-module", action="append", dest="plugin_modules",
                                   help="Import plugin module (can be used multiple times)")



    # -------------------
    # rewrite Command
    # -------------------

    rewrite_parser = subparsers.add_parser(
        "rewrite",
        help="Rewrite SQL queries",
        description="Rewrite SQL queries according to specified rules"
    )
    
    
    rewrite_plugin_group = rewrite_parser.add_argument_group('Plugins')
    rewrite_plugin_group.add_argument("--plugin", action="append", dest="plugin_files",
                                      help="Load plugin from Python file (can be used multiple times)")
    rewrite_plugin_group.add_argument("--plugin-dir", action="append", dest="plugin_dirs",
                                      help="Load all plugins from directory (can be used multiple times)")
    rewrite_plugin_group.add_argument("--plugin-module", action="append", dest="plugin_modules",
                                      help="Import plugin module (can be used multiple times)")
    rewrite_input_group = rewrite_parser.add_argument_group(title='Input')
    rewrite_input_group.add_argument("input", nargs="?", help="SQL file to rewrite")
    
    rewrite_parameter_group = rewrite_parser.add_argument_group('Parameters')
    rewrite_parameter_group.add_argument("-o", "--output", help="Output file")
    rewrite_parameter_group.add_argument("-d", "--dialect",
                                        choices=SUPPORTED_DIALECTS,
                                        help="SQL dialect (sqlserver, postgresql, mysql, oracle, sqlite). Default: sqlserver")
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
    # plugin Command
    # -------------------
    plugin_parser = subparsers.add_parser(
        "plugin",
        help="Manage custom plugins",
        description="Add, list, or remove custom rule plugins"
    )
    
    plugin_subparsers = plugin_parser.add_subparsers(title='Plugin Commands', dest="plugin_command", required=True)
    
    # plugin add
    add_plugin_parser = plugin_subparsers.add_parser(
        "add",
        help="Add a custom plugin",
        description="Add a Python file containing custom rules to the plugin directory"
    )
    add_plugin_parser.add_argument(
        "plugin_file",
        help="Path to the Python plugin file to add"
    )
    
    # plugin list
    list_plugin_parser = plugin_subparsers.add_parser(
        "list",
        help="List installed plugins",
        description="List all custom plugins in the user plugin directory"
    )
    
    # plugin remove
    remove_plugin_parser = plugin_subparsers.add_parser(
        "remove",
        help="Remove a plugin",
        description="Remove a custom plugin from the plugin directory"
    )
    remove_plugin_parser.add_argument(
        "plugin_name",
        help="Name of the plugin file to remove (e.g., my_plugin.py)"
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

    # plugin command
    if args.command == "plugin":
        if args.plugin_command == "add":
            add_plugin(args.plugin_file)
        elif args.plugin_command == "list":
            list_plugins()
        elif args.plugin_command == "remove":
            remove_plugin(args.plugin_name)
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
        if args.input:
            with open(args.input, "r", encoding="utf-8") as f:
                sql = f.read()
        else:
            # Check if stdin is a TTY (interactive terminal)
            if sys.stdin.isatty():
                print("Error: No input file provided and no data piped to stdin.", file=sys.stderr)
                print("Usage: sqltidy tidy <file> or pipe data like: cat file.sql | sqltidy tidy", file=sys.stderr)
                print("Run 'sqltidy tidy --help' for more information.", file=sys.stderr)
                sys.exit(1)
            sql = sys.stdin.read()

        # Load config file based on dialect (default: sqlserver)
        dialect = args.dialect if args.dialect else 'sqlserver'
        config = create_config_from_file(dialect)

        # Load plugins if specified
        plugin_rules = []
        if args.plugin_files:
            for plugin_file in args.plugin_files:
                try:
                    rules = load_plugin_file(plugin_file)
                    plugin_rules.extend([r() for r in rules])
                except Exception as e:
                    print(f"Warning: Could not load plugin {plugin_file}: {e}", file=sys.stderr)
        
        if args.plugin_dirs:
            for plugin_dir in args.plugin_dirs:
                try:
                    rules = load_plugins_from_directory(plugin_dir)
                    plugin_rules.extend([r() for r in rules])
                except Exception as e:
                    print(f"Warning: Could not load plugins from {plugin_dir}: {e}", file=sys.stderr)
        
        if args.plugin_modules:
            for plugin_module in args.plugin_modules:
                try:
                    rules = load_plugin_module(plugin_module)
                    plugin_rules.extend([r() for r in rules])
                except Exception as e:
                    print(f"Warning: Could not load plugin module {plugin_module}: {e}", file=sys.stderr)

        formatted_sql = format_sql(sql, config=config, custom_rules=plugin_rules, rule_type='tidy')

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(formatted_sql)
        elif args.input:
            # overwrite input file if no output specified
            with open(args.input, "w", encoding="utf-8") as f:
                f.write(formatted_sql)
        else:
            print(formatted_sql)

    # rewrite command
    if args.command == "rewrite":
        if args.input:
            with open(args.input, "r", encoding="utf-8") as f:
                sql = f.read()
        else:
            # Check if stdin is a TTY (interactive terminal)
            if sys.stdin.isatty():
                print("Error: No input file provided and no data piped to stdin.", file=sys.stderr)
                print("Usage: sqltidy rewrite <file> or pipe data like: cat file.sql | sqltidy rewrite", file=sys.stderr)
                print("Run 'sqltidy rewrite --help' for more information.", file=sys.stderr)
                sys.exit(1)
            sql = sys.stdin.read()

        # Load config file based on dialect (default: sqlserver)
        dialect = args.dialect if args.dialect else 'sqlserver'
        config = create_config_from_file(dialect)

        # Load plugins if specified
        plugin_rules = []
        if args.plugin_files:
            for plugin_file in args.plugin_files:
                try:
                    rules = load_plugin_file(plugin_file)
                    plugin_rules.extend([r() for r in rules])
                except Exception as e:
                    print(f"Warning: Could not load plugin {plugin_file}: {e}", file=sys.stderr)
        
        if args.plugin_dirs:
            for plugin_dir in args.plugin_dirs:
                try:
                    rules = load_plugins_from_directory(plugin_dir)
                    plugin_rules.extend([r() for r in rules])
                except Exception as e:
                    print(f"Warning: Could not load plugins from {plugin_dir}: {e}", file=sys.stderr)
        
        if args.plugin_modules:
            for plugin_module in args.plugin_modules:
                try:
                    rules = load_plugin_module(plugin_module)
                    plugin_rules.extend([r() for r in rules])
                except Exception as e:
                    print(f"Warning: Could not load plugin module {plugin_module}: {e}", file=sys.stderr)

        formatted_sql = format_sql(sql, config=config, custom_rules=plugin_rules, rule_type='rewrite')

        # Apply tidy rules if requested
        if args.tidy:
            tidy_config = SQLTidyConfig()
            formatted_sql = format_sql(formatted_sql, config=tidy_config, rule_type='tidy')

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(formatted_sql)
        elif args.input:
            # overwrite input file if no output specified
            with open(args.input, "w", encoding="utf-8") as f:
                f.write(formatted_sql)
        else:
            print(formatted_sql)

if __name__ == "__main__":
    main()
