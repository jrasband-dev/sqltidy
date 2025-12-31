import argparse
import sys
import json
from . import __version__
from .api import format_sql
from .config import TidyConfig, RewriteConfig
from .generator import run_generator, load_config_file
from .tokenizer import tokenize_with_types, TokenType, is_keyword
from .plugins import load_plugin_file, load_plugins_from_directory, load_plugin_module


def create_tidy_config_from_file(config_file: str) -> TidyConfig:
    """
    Load TidyConfig from a JSON configuration file.
    
    Args:
        config_file: Path to the configuration JSON file
    
    Returns:
        TidyConfig: Configuration object with loaded values
    """
    try:
        config_data = load_config_file(config_file)
        
        # Create TidyConfig with loaded values (no nesting needed)
        return TidyConfig(**config_data)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading config file: {e}", file=sys.stderr)
        sys.exit(1)


def create_rewrite_config_from_file(config_file: str) -> RewriteConfig:
    """
    Load RewriteConfig from a JSON configuration file.
    
    Args:
        config_file: Path to the configuration JSON file
    
    Returns:
        RewriteConfig: Configuration object with loaded values
    """
    try:
        config_data = load_config_file(config_file)
        
        # Create RewriteConfig with loaded values (no nesting needed)
        return RewriteConfig(**config_data)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading config file: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="A SQL formatting tool"
    )
    
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
    tidy_parameter_group.add_argument("-cfg","--rules", help="Path to custom rules json file")
    
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
    rewrite_parameter_group.add_argument("-cfg", "--rules", help="Path to custom rules json file")
    # Use config.py defaults for rewrite behavior. No CLI enable/disable flags are provided.
    rewrite_parameter_group.add_argument("--tidy", action="store_true", help="Apply tidy rules after rewriting")


    # -------------------
    # config Command
    # -------------------
    config_parser = subparsers.add_parser(
        "config",
        help="Interactive config generator",
        description="Launch an interactive configuration generator for sqltidy"
    )
    # You can add config-specific arguments here if needed


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

    if args.command == "config":
        run_generator()
        return

    # parse command
    if args.command == "parse":
        if args.input:
            with open(args.input, "r", encoding="utf-8") as f:
                sql = f.read()
        else:
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

        formatted_sql = format_sql(sql, config=config, custom_rules=plugin_rules

        # Load config from file if provided, otherwise use defaults
        if args.rules:
            config = create_tidy_config_from_file(args.rules)
        else:
            config = TidyConfig()

        formatted_sql = format_sql(sql, config=config)

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
            sql = sys.stdin.read()

        # Load config from file if provided, otherwise use defaults
        if args.rules:
            config = create_rewrite_config_from_file(args.rules)
        else:
            config = RewriteConfig()

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

        formatted_sql = format_sql(sql, config=config, custom_rules=plugin_rules)

        # Apply tidy rules if requested
        if args.tidy:
            tidy_config = TidyConfig()
            formatted_sql = format_sql(formatted_sql, config=tidy_config)

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
