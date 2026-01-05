import argparse
import sys
import json
from pathlib import Path
from . import __version__
from .api import format_sql, format_sql_folder
from .rulebook import SQLTidyConfig, SUPPORTED_DIALECTS
from .generator import create_rulebook, list_rulebooks, edit_rulebook, reset_rulebook, update_rulebook, load_rulebook_file, get_bundled_rulebook_path, get_user_rulebooks_dir, add_rule, list_rules, remove_rule
from .tokenizer import tokenize_with_types, TokenType, is_keyword
from .plugins import load_rule_file, load_rules_from_directory
from .dialects.registry import list_dialects, get_dialect, is_dialect_available

try:
    from rich.console import Console
    from rich.text import Text
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
    from rich.syntax import Syntax
    from rich.tree import Tree
    from rich import box
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

# Create a global console instance
console = Console() if HAS_RICH else None


def print_logo():
    """Print the sqltidy ASCII art logo."""
    if not HAS_RICH:
        return
    
    logo = Text("""
███████╗ ██████╗ ██╗  ████████╗██╗██████╗ ██╗   ██╗
██╔════╝██╔═══██╗██║  ╚══██╔══╝██║██╔══██╗╚██╗ ██╔╝
███████╗██║   ██║██║     ██║   ██║██║  ██║ ╚████╔╝ 
╚════██║██║▄▄ ██║██║     ██║   ██║██║  ██║  ╚██╔╝  
███████║╚██████╔╝███████╗██║   ██║██████╔╝   ██║   
╚══════╝ ╚══▀▀═╝ ╚══════╝╚═╝   ╚═╝╚═════╝    ╚═╝   
""", style="bold cyan")
    
    console.print(logo)
    console.print(Panel("[bold cyan]SQL Formatting & Rewriting Tool[/bold cyan]", 
                        border_style="cyan", 
                        box=box.ROUNDED))


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
        # No file found - return None to trigger auto-generation
        return None
    
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
    Load SQLTidyConfig from a JSON rulebook file or auto-generate from rules.
    
    Priority:
    1. User's custom rulebook
    2. Bundled rulebook (if exists)
    3. Auto-generate from rule metadata
    
    Args:
        rulebook_file: Path, dialect name, or filename of the rulebook
    
    Returns:
        SQLTidyConfig: Configuration object with loaded values
    """
    try:
        resolved_path = resolve_rulebook_path(rulebook_file)
        
        # If path is None, auto-generate from rules
        if resolved_path is None:
            from .config_schema import generate_dialect_config
            # Extract dialect from rulebook_file (should be a dialect name)
            dialect = rulebook_file if rulebook_file in SUPPORTED_DIALECTS else 'sqlserver'
            config_dict = generate_dialect_config(dialect, include_plugins=False)
            return SQLTidyConfig.from_dict(config_dict)
        
        # Load from file
        rulebook_data = load_rulebook_file(resolved_path)
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
            if HAS_RICH:
                with console.status(f"[cyan]Processing {input_path.name}...", spinner="dots"):
                    with open(args.input, "r", encoding="utf-8") as f:
                        sql = f.read()
                    formatted_sql = format_sql(sql, config=config, custom_rules=plugin_rules, rule_type='tidy')
                
                console.print(f"[green]✓[/green] Formatted {input_path.name}")
            else:
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
            if HAS_RICH:
                console.print(Panel(
                    f"[cyan]Path:[/cyan] {input_path}\n"
                    f"[cyan]Mode:[/cyan] {'Recursive' if args.recursive else 'Non-recursive'}\n"
                    f"[cyan]Pattern:[/cyan] {args.pattern}\n"
                    f"[cyan]Dialect:[/cyan] {dialect}",
                    title="[bold cyan]Processing SQL Files",
                    border_style="cyan"
                ))
            else:
                print(f"Processing SQL files in: {input_path}")
                if args.recursive:
                    print(f"  Mode: Recursive")
                print(f"  Pattern: {args.pattern}")
                print(f"  Dialect: {dialect}")
            
            # Get list of files to process
            if args.recursive:
                files = list(input_path.rglob(args.pattern))
            else:
                files = list(input_path.glob(args.pattern))
            
            # Process with progress bar
            if HAS_RICH and files:
                results = {'total': 0, 'success': 0, 'failed': 0, 'errors': []}
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    TimeElapsedColumn(),
                    console=console
                ) as progress:
                    task = progress.add_task("[cyan]Formatting files...", total=len(files))
                    
                    for file_path in files:
                        results['total'] += 1
                        try:
                            with open(file_path, "r", encoding="utf-8") as f:
                                sql = f.read()
                            
                            formatted_sql = format_sql(sql, config=config, custom_rules=plugin_rules, rule_type='tidy')
                            
                            if args.output:
                                output_path = Path(args.output) / file_path.relative_to(input_path)
                                output_path.parent.mkdir(parents=True, exist_ok=True)
                                with open(output_path, "w", encoding="utf-8") as f:
                                    f.write(formatted_sql)
                            elif not args.no_in_place:
                                with open(file_path, "w", encoding="utf-8") as f:
                                    f.write(formatted_sql)
                            
                            results['success'] += 1
                            progress.update(task, advance=1, description=f"[cyan]Formatting files...")
                            console.print(f"  [green]✓[/green] {file_path.name}")
                        except Exception as e:
                            results['failed'] += 1
                            results['errors'].append({'file': str(file_path), 'error': str(e)})
                            progress.update(task, advance=1, description=f"[cyan]Formatting files...")
                            console.print(f"  [red]✗[/red] {file_path.name}: {str(e)}")
                
                # Display results in a table
                table = Table(title="Results", box=box.ROUNDED, border_style="cyan")
                table.add_column("Metric", style="cyan", no_wrap=True)
                table.add_column("Count", justify="right", style="bold")
                
                table.add_row("Total files", str(results['total']))
                table.add_row("Successful", f"[green]{results['success']}[/green]")
                table.add_row("Failed", f"[red]{results['failed']}[/red]")
                
                console.print()
                console.print(table)
                
                if results['errors']:
                    console.print("\n[bold red]Errors:[/bold red]")
                    for error in results['errors']:
                        console.print(f"  [red]✗[/red] {error['file']}: {error['error']}")
                
                if results['failed'] > 0:
                    sys.exit(1)
            else:
                # Fallback to original implementation
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
            if HAS_RICH:
                with console.status(f"[cyan]Rewriting {input_path.name}...", spinner="dots"):
                    with open(args.input, "r", encoding="utf-8") as f:
                        sql = f.read()
                    formatted_sql = format_sql(sql, config=config, custom_rules=plugin_rules, rule_type='rewrite')
                    
                    if args.tidy:
                        formatted_sql = format_sql(formatted_sql, config=config, rule_type='tidy')
                
                console.print(f"[green]✓[/green] Rewritten {input_path.name}")
            else:
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
            mode_text = "Rewrite + Tidy" if args.tidy else "Rewrite"
            
            if HAS_RICH:
                console.print(Panel(
                    f"[cyan]Path:[/cyan] {input_path}\n"
                    f"[cyan]Mode:[/cyan] {mode_text} ({'Recursive' if args.recursive else 'Non-recursive'})\n"
                    f"[cyan]Pattern:[/cyan] {args.pattern}\n"
                    f"[cyan]Dialect:[/cyan] {dialect}",
                    title="[bold cyan]Processing SQL Files",
                    border_style="cyan"
                ))
            else:
                print(f"Processing SQL files in: {input_path}")
                if args.recursive:
                    print(f"  Mode: Recursive")
                print(f"  Pattern: {args.pattern}")
                print(f"  Dialect: {dialect}")
                if args.tidy:
                    print("  Mode: Rewrite + Tidy")
            
            # Get list of files to process
            if args.recursive:
                files = list(input_path.rglob(args.pattern))
            else:
                files = list(input_path.glob(args.pattern))
            
            # Process with progress bar
            if HAS_RICH and files:
                results = {'total': 0, 'success': 0, 'failed': 0, 'errors': []}
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    TimeElapsedColumn(),
                    console=console
                ) as progress:
                    task = progress.add_task(f"[cyan]{mode_text}...", total=len(files))
                    
                    for file_path in files:
                        results['total'] += 1
                        try:
                            with open(file_path, "r", encoding="utf-8") as f:
                                sql = f.read()
                            
                            formatted_sql = format_sql(sql, config=config, custom_rules=plugin_rules, rule_type='rewrite')
                            
                            if args.tidy:
                                formatted_sql = format_sql(formatted_sql, config=config, rule_type='tidy')
                            
                            if args.output:
                                output_path = Path(args.output) / file_path.relative_to(input_path)
                                output_path.parent.mkdir(parents=True, exist_ok=True)
                                with open(output_path, "w", encoding="utf-8") as f:
                                    f.write(formatted_sql)
                            elif not args.no_in_place:
                                with open(file_path, "w", encoding="utf-8") as f:
                                    f.write(formatted_sql)
                            
                            results['success'] += 1
                            progress.update(task, advance=1, description=f"[cyan]{mode_text}...")
                            console.print(f"  [green]✓[/green] {file_path.name}")
                        except Exception as e:
                            results['failed'] += 1
                            results['errors'].append({'file': str(file_path), 'error': str(e)})
                            progress.update(task, advance=1, description=f"[cyan]{mode_text}...")
                            console.print(f"  [red]✗[/red] {file_path.name}: {str(e)}")
                
                # Display results in a table
                table = Table(title="Results", box=box.ROUNDED, border_style="cyan")
                table.add_column("Metric", style="cyan", no_wrap=True)
                table.add_column("Count", justify="right", style="bold")
                
                table.add_row("Total files", str(results['total']))
                table.add_row("Successful", f"[green]{results['success']}[/green]")
                table.add_row("Failed", f"[red]{results['failed']}[/red]")
                
                console.print()
                console.print(table)
                
                if results['errors']:
                    console.print("\n[bold red]Errors:[/bold red]")
                    for error in results['errors']:
                        console.print(f"  [red]✗[/red] {error['file']}: {error['error']}")
                
                if results['failed'] > 0:
                    sys.exit(1)
            else:
                # Fallback to original implementation
                if args.tidy:
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


def handle_dialects_command(args):
    """Handle the dialects command to show information about SQL dialects."""
    
    # List subcommand
    if args.dialects_command == "list":
        dialects = list_dialects()
        
        if args.format == "json":
            import json
            dialect_info = []
            for dialect_name in dialects:
                dialect = get_dialect(dialect_name)
                dialect_info.append({
                    "name": dialect_name,
                    "keywords_count": len(dialect.keywords),
                    "data_types_count": len(dialect.data_types),
                    "functions_count": len(dialect.functions)
                })
            print(json.dumps(dialect_info, indent=2))
        else:
            if HAS_RICH:
                table = Table(title="Available SQL Dialects", box=box.ROUNDED, border_style="cyan")
                table.add_column("Dialect", style="cyan bold", no_wrap=True)
                table.add_column("Keywords", justify="right", style="yellow")
                table.add_column("Data Types", justify="right", style="green")
                table.add_column("Functions", justify="right", style="magenta")
                
                for dialect_name in dialects:
                    dialect = get_dialect(dialect_name)
                    table.add_row(
                        dialect_name,
                        str(len(dialect.keywords)),
                        str(len(dialect.data_types)),
                        str(len(dialect.functions))
                    )
                
                console.print()
                console.print(table)
                console.print(f"\n[cyan]Total:[/cyan] {len(dialects)} dialects\n")
            else:
                print(f"\n{'='*60}")
                print(f"Available SQL Dialects")
                print(f"{'='*60}\n")
                
                for dialect_name in dialects:
                    dialect = get_dialect(dialect_name)
                    print(f"  {dialect_name:<15} - {len(dialect.keywords):>3} keywords, "
                          f"{len(dialect.data_types):>2} types, {len(dialect.functions):>2} functions")
                
                print(f"\n{'='*60}")
                print(f"Total: {len(dialects)} dialects\n")
    
    # Keywords subcommand
    elif args.dialects_command == "keywords":
        try:
            dialect = get_dialect(args.dialect)
            keywords = sorted(list(dialect.keywords))
            
            if args.format == "json":
                import json
                print(json.dumps(keywords, indent=2))
            else:
                if HAS_RICH:
                    panel = Panel(
                        "\n".join([f"  {k}" for k in keywords]),
                        title=f"[bold cyan]Keywords for {dialect.name.upper()} ({len(keywords)} total)",
                        border_style="cyan",
                        box=box.ROUNDED
                    )
                    console.print()
                    console.print(panel)
                    console.print()
                else:
                    print(f"\n{'='*60}")
                    print(f"Keywords for {dialect.name.upper()} ({len(keywords)} total)")
                    print(f"{'='*60}\n")
                    
                    # Display keywords in columns
                    cols = 5
                    max_len = max(len(k) for k in keywords) + 2 if keywords else 10
                    for i in range(0, len(keywords), cols):
                        row = keywords[i:i+cols]
                        print("  " + "".join(f"{k:<{max_len}}" for k in row))
                    
                    print(f"\n{'='*60}\n")
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Datatypes subcommand
    elif args.dialects_command == "datatypes":
        try:
            dialect = get_dialect(args.dialect)
            types = sorted(list(dialect.data_types))
            
            if args.format == "json":
                import json
                print(json.dumps(types, indent=2))
            else:
                if HAS_RICH:
                    if types:
                        panel = Panel(
                            "\n".join([f"  {t}" for t in types]),
                            title=f"[bold cyan]Data Types for {dialect.name.upper()} ({len(types)} total)",
                            border_style="cyan",
                            box=box.ROUNDED
                        )
                    else:
                        panel = Panel(
                            "No data types categorized separately for this dialect.\n"
                            "Data types may be included in the general keywords list.",
                            title=f"[bold cyan]Data Types for {dialect.name.upper()}",
                            border_style="yellow",
                            box=box.ROUNDED
                        )
                    console.print()
                    console.print(panel)
                    console.print()
                else:
                    print(f"\n{'='*60}")
                    print(f"Data Types for {dialect.name.upper()} ({len(types)} total)")
                    print(f"{'='*60}\n")
                    
                    if types:
                        # Display types in columns
                        cols = 5
                        max_len = max(len(t) for t in types) + 2
                        for i in range(0, len(types), cols):
                            row = types[i:i+cols]
                            print("  " + "".join(f"{t:<{max_len}}" for t in row))
                    else:
                        print("  No data types categorized separately for this dialect.")
                        print("  Data types may be included in the general keywords list.")
                    
                    print(f"\n{'='*60}\n")
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Functions subcommand
    elif args.dialects_command == "functions":
        try:
            dialect = get_dialect(args.dialect)
            functions = sorted(list(dialect.functions))
            
            if args.format == "json":
                import json
                print(json.dumps(functions, indent=2))
            else:
                if HAS_RICH:
                    if functions:
                        panel = Panel(
                            "\n".join([f"  {f}" for f in functions]),
                            title=f"[bold cyan]Built-in Functions for {dialect.name.upper()} ({len(functions)} total)",
                            border_style="cyan",
                            box=box.ROUNDED
                        )
                    else:
                        panel = Panel(
                            "No functions categorized separately for this dialect.\n"
                            "Functions may be included in the general keywords list.",
                            title=f"[bold cyan]Built-in Functions for {dialect.name.upper()}",
                            border_style="yellow",
                            box=box.ROUNDED
                        )
                    console.print()
                    console.print(panel)
                    console.print()
                else:
                    print(f"\n{'='*60}")
                    print(f"Built-in Functions for {dialect.name.upper()} ({len(functions)} total)")
                    print(f"{'='*60}\n")
                    
                    if functions:
                        # Display functions in columns
                        cols = 5
                        max_len = max(len(f) for f in functions) + 2
                        for i in range(0, len(functions), cols):
                            row = functions[i:i+cols]
                            print("  " + "".join(f"{f:<{max_len}}" for f in row))
                    else:
                        print("  No functions categorized separately for this dialect.")
                        print("  Functions may be included in the general keywords list.")
                    
                    print(f"\n{'='*60}\n")
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


def main():
    # Print logo
    print_logo()
    
    parser = argparse.ArgumentParser()

    # create subparsers for subcommands
    subparsers = parser.add_subparsers(title='Commands', dest="command", required=True)

    # -------------------
    # version Command
    # -------------------
    version_parser = subparsers.add_parser(
        "version",
        help="Show version information",
        description="Display the sqltidy version number"
    )

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
    create_parser.add_argument(
        "--no-plugins",
        dest="include_plugins",
        action="store_false",
        default=True,
        help="Exclude user plugin rules from the generated configuration (by default, plugins are included)"
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
        help="Edit an existing rulebook file",
        description="Edit an existing rulebook in user directory (~/.sqltidy/rulebooks/). Use 'create' command to make new rulebooks."
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
        description="Remove user customization and revert to auto-generated defaults"
    )
    reset_parser.add_argument(
        "rulebook",
        nargs="?",
        help="Dialect name (e.g., 'postgresql'), rulebook filename to reset, or 'all' to reset all rulebooks"
    )
    
    # rulebook update
    update_parser = rulebook_subparsers.add_parser(
        "update",
        help="Update rulebook with new rules",
        description="Sync existing rulebook with newly registered rules (preserves existing settings)"
    )
    update_parser.add_argument(
        "rulebook",
        nargs="?",
        help="Dialect name (e.g., 'postgresql'), rulebook filename to update, or 'all' to update all rulebooks"
    )
    update_parser.add_argument(
        "--no-plugins",
        dest="include_plugins",
        action="store_false",
        default=True,
        help="Exclude user plugin rules from the update (by default, plugins are included)"
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
    # dialects Command
    # -------------------
    dialects_parser = subparsers.add_parser(
        "dialects",
        help="Show SQL dialect information",
        description="Display information about supported SQL dialects"
    )
    
    dialects_subparsers = dialects_parser.add_subparsers(
        title='Dialects Commands',
        dest="dialects_command",
        required=True
    )
    
    # dialects list
    dialects_list_parser = dialects_subparsers.add_parser(
        "list",
        help="List all available dialects",
        description="Display a list of all supported SQL dialects"
    )
    dialects_list_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)"
    )
    
    # dialects keywords
    dialects_keywords_parser = dialects_subparsers.add_parser(
        "keywords",
        help="Show keywords for a dialect",
        description="Display all SQL keywords for a specific dialect"
    )
    dialects_keywords_parser.add_argument(
        "dialect",
        choices=SUPPORTED_DIALECTS,
        help="SQL dialect name"
    )
    dialects_keywords_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)"
    )
    
    # dialects datatypes
    dialects_datatypes_parser = dialects_subparsers.add_parser(
        "datatypes",
        help="Show data types for a dialect",
        description="Display all data types for a specific dialect"
    )
    dialects_datatypes_parser.add_argument(
        "dialect",
        choices=SUPPORTED_DIALECTS,
        help="SQL dialect name"
    )
    dialects_datatypes_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)"
    )
    
    # dialects functions
    dialects_functions_parser = dialects_subparsers.add_parser(
        "functions",
        help="Show built-in functions for a dialect",
        description="Display all built-in functions for a specific dialect"
    )
    dialects_functions_parser.add_argument(
        "dialect",
        choices=SUPPORTED_DIALECTS,
        help="SQL dialect name"
    )
    dialects_functions_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)"
    )







    # -------------------
    # parse arguments
    # -------------------
    args = parser.parse_args()

    # version command
    if args.command == "version":
        print(f"sqltidy {__version__}")
        return

    # rulebooks command
    if args.command == "rulebooks":
        if args.rulebook_command == "create":
            include_plugins = args.include_plugins
            create_rulebook(dialect=args.dialect, template_file=args.template, include_plugins=include_plugins)
        elif args.rulebook_command == "list":
            list_rulebooks(directory=args.directory)
        elif args.rulebook_command == "edit":
            edit_rulebook(rulebook_name=args.rulebook)
        elif args.rulebook_command == "reset":
            reset_rulebook(rulebook_name=args.rulebook)
        elif args.rulebook_command == "update":
            include_plugins = args.include_plugins
            update_rulebook(rulebook_name=args.rulebook, include_plugins=include_plugins)
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
        if HAS_RICH:
            with console.status("[cyan]Tokenizing SQL...", spinner="dots"):
                tokens = tokenize_with_types(sql)
        else:
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
            if HAS_RICH:
                # Use rich table
                table = Table(title="SQL Tokens", box=box.ROUNDED, border_style="cyan")
                table.add_column("Type", style="yellow", no_wrap=True)
                table.add_column("Value", style="white")
                table.add_column("Keyword", justify="center", style="green")
                
                for token in display_tokens:
                    value_str = repr(token.value)
                    if len(value_str) > 60:
                        value_str = value_str[:57] + "..."
                    
                    is_kw = "✓" if is_keyword(token.value) else ""
                    table.add_row(token.type.value, value_str, is_kw)
                
                console.print()
                console.print(table)
            else:
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
            # Count by type
            type_counts = {}
            for token in tokens:
                type_counts[token.type] = type_counts.get(token.type, 0) + 1
            
            if HAS_RICH:
                # Display stats in a rich panel
                stats_table = Table(box=box.SIMPLE, show_header=True, border_style="cyan")
                stats_table.add_column("Token Type", style="cyan")
                stats_table.add_column("Count", justify="right", style="yellow")
                stats_table.add_column("Percentage", justify="right", style="green")
                
                for token_type in sorted(type_counts.keys(), key=lambda t: type_counts[t], reverse=True):
                    count = type_counts[token_type]
                    pct = count / len(tokens) * 100
                    stats_table.add_row(token_type.value, str(count), f"{pct:.1f}%")
                
                console.print()
                console.print(Panel(stats_table, title=f"[bold cyan]Token Statistics (Total: {len(tokens)})", border_style="cyan"))
                
                # Keyword statistics
                keywords = sorted(set(t.value.upper() for t in tokens if t.type == TokenType.KEYWORD))
                if keywords:
                    console.print(Panel(
                        ", ".join(keywords),
                        title=f"[bold cyan]Unique Keywords ({len(keywords)})",
                        border_style="cyan"
                    ))
                
                # Identifier statistics
                identifiers = sorted(set(t.value for t in tokens if t.type == TokenType.IDENTIFIER))
                if identifiers:
                    if len(identifiers) <= 20:
                        id_text = ", ".join(identifiers)
                    else:
                        id_text = ", ".join(identifiers[:20]) + f"\n... and {len(identifiers) - 20} more"
                    
                    console.print(Panel(
                        id_text,
                        title=f"[bold cyan]Unique Identifiers ({len(identifiers)})",
                        border_style="cyan"
                    ))
            else:
                output_lines.append("\nToken Statistics:")
                output_lines.append("-" * 40)
                
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
        if not HAS_RICH or args.output or args.format != "table":
            result = "\n".join(output_lines)
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(result)
            else:
                if output_lines:
                    print(result)
        
        return

    # dialects command
    if args.command == "dialects":
        handle_dialects_command(args)
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
