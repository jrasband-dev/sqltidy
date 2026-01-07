import argparse
import sys
import json
from pathlib import Path
from . import __version__
from .api import format_sql, format_sql_folder
from .rulebook import SQLTidyConfig, SUPPORTED_DIALECTS
from .generator import create_rulebook, list_rulebooks, edit_rulebook, reset_rulebook, update_rulebook, load_rulebook_file, get_bundled_rulebook_path, get_user_rulebooks_dir, add_rule, list_rules, remove_rule
from .tokenizer import tokenize_with_types, TokenType, is_keyword
from .plugins import load_rule_file, load_rules_from_directory, load_rules_module
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
                rules = load_rules_module(rule_module)
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
                results = {
                    'total': 0, 'success': 0, 'failed': 0, 'errors': [],
                    'tidy_rules': set(), 'rewrite_rules': set(),
                    'all_tidy_rules': set(), 'all_rewrite_rules': set()
                }
                
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
                            
                            result = format_sql(sql, config=config, custom_rules=plugin_rules, rule_type='tidy', return_metadata=True)
                            formatted_sql = result['sql'] if isinstance(result, dict) else result
                            
                            # Track applied rules by type
                            if isinstance(result, dict) and 'applied_rules' in result:
                                for rule in result['applied_rules']:
                                    rule_type = rule.get('type', 'unknown')
                                    if rule_type == 'tidy':
                                        results['tidy_rules'].add(rule['name'])
                                    elif rule_type == 'rewrite':
                                        results['rewrite_rules'].add(rule['name'])
                            
                            # Track all available rules
                            if isinstance(result, dict) and 'all_applicable_rules' in result:
                                for rule in result['all_applicable_rules']:
                                    rule_type = rule.get('type', 'unknown')
                                    if rule_type == 'tidy':
                                        results['all_tidy_rules'].add(rule['name'])
                                    elif rule_type == 'rewrite':
                                        results['all_rewrite_rules'].add(rule['name'])
                            
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
                
                # Display applied rules checklist by type
                if results['tidy_rules'] or results['rewrite_rules'] or results['all_tidy_rules'] or results['all_rewrite_rules']:
                    console.print()
                    
                    if results['all_tidy_rules']:
                        # Separate applied and unapplied tidy rules
                        applied = sorted(results['tidy_rules'])
                        unapplied = sorted(results['all_tidy_rules'] - results['tidy_rules'])
                        
                        lines = []
                        lines.extend([f"[green]✓[/green] {rule}" for rule in applied])
                        lines.extend([f"[dim]✗ {rule}[/dim]" for rule in unapplied])
                        
                        tidy_panel = Panel(
                            "\n".join(lines),
                            title="[bold cyan]Tidy Rules[/bold cyan]",
                            border_style="cyan",
                            box=box.ROUNDED
                        )
                        console.print(tidy_panel)
                    
                    if results['all_rewrite_rules']:
                        console.print()
                        # Separate applied and unapplied rewrite rules
                        applied = sorted(results['rewrite_rules'])
                        unapplied = sorted(results['all_rewrite_rules'] - results['rewrite_rules'])
                        
                        lines = []
                        lines.extend([f"[green]✓[/green] {rule}" for rule in applied])
                        lines.extend([f"[dim]✗ {rule}[/dim]" for rule in unapplied])
                        
                        rewrite_panel = Panel(
                            "\n".join(lines),
                            title="[bold cyan]Rewrite Rules[/bold cyan]",
                            border_style="magenta",
                            box=box.ROUNDED
                        )
                        console.print(rewrite_panel)
                
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
                results = {
                    'total': 0, 'success': 0, 'failed': 0, 'errors': [],
                    'tidy_rules': set(), 'rewrite_rules': set(),
                    'all_tidy_rules': set(), 'all_rewrite_rules': set()
                }
                
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
                            
                            result = format_sql(sql, config=config, custom_rules=plugin_rules, rule_type='rewrite', return_metadata=True)
                            formatted_sql = result['sql'] if isinstance(result, dict) else result
                            
                            # Track applied rewrite rules
                            if isinstance(result, dict) and 'applied_rules' in result:
                                for rule in result['applied_rules']:
                                    rule_type = rule.get('type', 'unknown')
                                    if rule_type == 'rewrite':
                                        results['rewrite_rules'].add(rule['name'])
                            
                            # Track all available rewrite rules
                            if isinstance(result, dict) and 'all_applicable_rules' in result:
                                for rule in result['all_applicable_rules']:
                                    rule_type = rule.get('type', 'unknown')
                                    if rule_type == 'rewrite':
                                        results['all_rewrite_rules'].add(rule['name'])
                            
                            if args.tidy:
                                tidy_result = format_sql(formatted_sql, config=config, rule_type='tidy', return_metadata=True)
                                formatted_sql = tidy_result['sql'] if isinstance(tidy_result, dict) else tidy_result
                                
                                # Track applied tidy rules
                                if isinstance(tidy_result, dict) and 'applied_rules' in tidy_result:
                                    for rule in tidy_result['applied_rules']:
                                        rule_type = rule.get('type', 'unknown')
                                        if rule_type == 'tidy':
                                            results['tidy_rules'].add(rule['name'])
                                
                                # Track all available tidy rules
                                if isinstance(tidy_result, dict) and 'all_applicable_rules' in tidy_result:
                                    for rule in tidy_result['all_applicable_rules']:
                                        rule_type = rule.get('type', 'unknown')
                                        if rule_type == 'tidy':
                                            results['all_tidy_rules'].add(rule['name'])
                            
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
                
                # Display applied rules checklist by type
                if results['tidy_rules'] or results['rewrite_rules'] or results['all_tidy_rules'] or results['all_rewrite_rules']:
                    console.print()
                    
                    if results['all_rewrite_rules']:
                        # Separate applied and unapplied rewrite rules
                        applied = sorted(results['rewrite_rules'])
                        unapplied = sorted(results['all_rewrite_rules'] - results['rewrite_rules'])
                        
                        lines = []
                        lines.extend([f"[green]✓[/green] {rule}" for rule in applied])
                        lines.extend([f"[dim]✗ {rule}[/dim]" for rule in unapplied])
                        
                        rewrite_panel = Panel(
                            "\n".join(lines),
                            title="[bold magenta]Rewrite Rules[/bold magenta]",
                            border_style="magenta",
                            box=box.ROUNDED
                        )
                        console.print(rewrite_panel)
                    
                    if results['all_tidy_rules']:
                        console.print()
                        # Separate applied and unapplied tidy rules
                        applied = sorted(results['tidy_rules'])
                        unapplied = sorted(results['all_tidy_rules'] - results['tidy_rules'])
                        
                        lines = []
                        lines.extend([f"[green]✓[/green] {rule}" for rule in applied])
                        lines.extend([f"[dim]✗ {rule}[/dim]" for rule in unapplied])
                        
                        tidy_panel = Panel(
                            "\n".join(lines),
                            title="[bold cyan]Tidy Rules[/bold cyan]",
                            border_style="cyan",
                            box=box.ROUNDED
                        )
                        console.print(tidy_panel)
                
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
    parse_parameter_group.add_argument("--format", choices=["table", "json", "simple", "tree"], default="table",
                                       help="Output format (default: table)")
    parse_parameter_group.add_argument("--level", choices=["basic", "grouped", "structured", "semantic"], default="semantic",
                                       help="Tokenization level: basic (tokens only), grouped (+functions), structured (+clauses), semantic (full analysis)")
    parse_parameter_group.add_argument("--dialect", choices=SUPPORTED_DIALECTS, default="sqlserver",
                                       help="SQL dialect for tokenization (default: sqlserver)")
    parse_parameter_group.add_argument("--show-whitespace", action="store_true",
                                      help="Include whitespace tokens in output")
    parse_parameter_group.add_argument("--keywords-only", action="store_true",
                                      help="Show only SQL keywords")
    parse_parameter_group.add_argument("--show-tokens", action="store_true",
                                      help="Show detailed token table (hidden by default when semantic analysis shown)")
    parse_parameter_group.add_argument("--no-semantic", action="store_true",
                                      help="Skip semantic SQL analysis (use with --show-tokens)")

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

        # Import semantic tokenizer components
        from sqltidy.tokenizer import SemanticLevel, TokenGroup, GroupType, Token
        
        # Tokenize the SQL with semantic analysis
        level = SemanticLevel(args.level)
        if HAS_RICH:
            with console.status(f"[cyan]Tokenizing SQL at {args.level} level...", spinner="dots"):
                tokens = tokenize_with_types(sql, dialect=args.dialect, level=level)
        else:
            tokens = tokenize_with_types(sql, dialect=args.dialect, level=level)
        
        # Generate output
        output_lines = []
        
        # Show semantic analysis (unless disabled)
        if not args.no_semantic and level != SemanticLevel.BASIC:
            # Helper function to find all groups recursively
            def find_all_groups(items, target_type):
                results = []
                for item in items:
                    if isinstance(item, TokenGroup):
                        if item.group_type == target_type:
                            results.append(item)
                        results.extend(find_all_groups(item.tokens, target_type))
                return results
            
            # Use Rich only if not outputting to file
            use_rich = HAS_RICH and not args.output
            
            
            # Find semantic groups
            join_groups = find_all_groups(tokens, GroupType.JOIN_CLAUSE)
            case_groups = find_all_groups(tokens, GroupType.CASE_EXPRESSION)
            window_groups = find_all_groups(tokens, GroupType.WINDOW_FUNCTION)
            cte_groups = find_all_groups(tokens, GroupType.CTE)
            subquery_groups = find_all_groups(tokens, GroupType.SUBQUERY)
            select_groups = find_all_groups(tokens, GroupType.SELECT_CLAUSE)
            from_groups = find_all_groups(tokens, GroupType.FROM_CLAUSE)
            where_groups = find_all_groups(tokens, GroupType.WHERE_CLAUSE)
            groupby_groups = find_all_groups(tokens, GroupType.GROUP_BY_CLAUSE)
            having_groups = find_all_groups(tokens, GroupType.HAVING_CLAUSE)
            orderby_groups = find_all_groups(tokens, GroupType.ORDER_BY_CLAUSE)
            union_groups = find_all_groups(tokens, GroupType.UNION_CLAUSE)
            limit_groups = find_all_groups(tokens, GroupType.LIMIT_CLAUSE)
            func_groups = find_all_groups(tokens, GroupType.FUNCTION)
        
            # 1. CLAUSES FOUND
            clause_counts = []
            if select_groups:
                clause_counts.append(("SELECT", len(select_groups)))
            if from_groups:
                clause_counts.append(("FROM", len(from_groups)))
            if where_groups:
                clause_counts.append(("WHERE", len(where_groups)))
            if groupby_groups:
                clause_counts.append(("GROUP BY", len(groupby_groups)))
            if having_groups:
                clause_counts.append(("HAVING", len(having_groups)))
            if orderby_groups:
                clause_counts.append(("ORDER BY", len(orderby_groups)))
            if join_groups:
                clause_counts.append(("JOIN", len(join_groups)))
            if subquery_groups:
                clause_counts.append(("Subqueries", len(subquery_groups)))
            if union_groups:
                clause_counts.append(("UNION", len(union_groups)))
            if limit_groups:
                clause_counts.append(("LIMIT/TOP", len(limit_groups)))
            
            if clause_counts:
                if use_rich:
                    clause_table = Table(title="Clauses Found", box=box.ROUNDED, border_style="green")
                    clause_table.add_column("Clause Type", style="cyan")
                    clause_table.add_column("Count", justify="right", style="yellow")
                    
                    for name, count in clause_counts:
                        clause_table.add_row(name, str(count))
                    
                    console.print(clause_table)
                    console.print()
                else:
                    output_lines.append("\n[Clauses Found]")
                    for name, count in clause_counts:
                        output_lines.append(f"  {name}: {count}")
            
            # 2. TABLES REFERENCED (Comprehensive - includes both FROM and JOIN tables)
            all_table_refs = []
            
            # Extract from FROM clauses
            if from_groups:
                def extract_table_names(group):
                    """Extract table names and aliases from a FROM clause group"""
                    tables = []
                    tokens = group.tokens if isinstance(group, TokenGroup) else [group]
                    
                    i = 0
                    while i < len(tokens):
                        item = tokens[i]
                        
                        # Skip JOIN groups - they're handled separately
                        if isinstance(item, TokenGroup) and item.group_type == GroupType.JOIN_CLAUSE:
                            i += 1
                            continue
                        
                        # Skip whitespace and operators
                        if isinstance(item, Token) and item.type in (TokenType.WHITESPACE, TokenType.NEWLINE, TokenType.OPERATOR, TokenType.PUNCTUATION):
                            i += 1
                            continue
                        
                        # Look for pattern: FROM table_name [AS] alias
                        if isinstance(item, Token) and item.type == TokenType.KEYWORD and item.value.upper() == 'FROM':
                            # Next non-whitespace token should be table name
                            i += 1
                            while i < len(tokens) and isinstance(tokens[i], Token) and tokens[i].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                                i += 1
                            
                            if i < len(tokens):
                                table_item = tokens[i]
                                if isinstance(table_item, Token) and table_item.type in (TokenType.IDENTIFIER, TokenType.KEYWORD):
                                    table_name = table_item.value
                                    alias = None
                                    
                                    # Look ahead for alias
                                    j = i + 1
                                    while j < len(tokens) and isinstance(tokens[j], Token) and tokens[j].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                                        j += 1
                                    
                                    if j < len(tokens):
                                        next_token = tokens[j]
                                        if isinstance(next_token, Token):
                                            if next_token.value.upper() == 'AS':
                                                # Skip AS and whitespace
                                                j += 1
                                                while j < len(tokens) and isinstance(tokens[j], Token) and tokens[j].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                                                    j += 1
                                                if j < len(tokens) and isinstance(tokens[j], Token) and tokens[j].type == TokenType.IDENTIFIER:
                                                    alias = tokens[j].value
                                            elif next_token.type == TokenType.IDENTIFIER and next_token.value.upper() not in ('JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'CROSS', 'FULL', 'WHERE', 'GROUP', 'ORDER', 'HAVING', 'UNION'):
                                                alias = next_token.value
                                    
                                    tables.append((table_name, alias, 'FROM'))
                        
                        elif isinstance(item, TokenGroup) and item.group_type != GroupType.SUBQUERY and item.group_type != GroupType.JOIN_CLAUSE:
                            # Recursively check other groups
                            tables.extend(extract_table_names(item))
                        
                        i += 1
                    
                    return tables
                
                for group in from_groups:
                    tables = extract_table_names(group)
                    all_table_refs.extend(tables)
            
            # Add JOIN tables
            if join_groups:
                for group in join_groups:
                    table = group.metadata.get('table', '?')
                    alias = group.metadata.get('alias', None)
                    join_type = group.metadata.get('join_type', 'JOIN')
                    all_table_refs.append((table, alias, join_type))
            
            # Remove duplicates while preserving order
            seen = set()
            unique_tables = []
            for table, alias, source in all_table_refs:
                key = table.lower()
                if key not in seen:
                    seen.add(key)
                    unique_tables.append((table, alias, source))
            
            if unique_tables:
                if use_rich:
                    table_table = Table(title="Tables Referenced", box=box.ROUNDED, border_style="cyan")
                    table_table.add_column("Table", style="yellow")
                    table_table.add_column("Alias", style="magenta")
                    table_table.add_column("Source", style="dim")
                    
                    for table_name, alias, source in unique_tables:
                        table_table.add_row(table_name, alias or '-', source)
                    
                    console.print(table_table)
                    console.print()
                else:
                    output_lines.append(f"\n[Tables Referenced] {len(unique_tables)} table(s):")
                    for table_name, alias, source in unique_tables:
                        line = f"  {table_name}"
                        if alias:
                            line += f" AS {alias}"
                        line += f" ({source})"
                        output_lines.append(line)
            
            # 3. FUNCTION CALLS
            if func_groups:
                func_names = [g.name for g in func_groups if g.name]
                unique_funcs = sorted(set(func_names))
                
                if use_rich:
                    func_table = Table(title="Function Calls", box=box.ROUNDED, border_style="blue")
                    func_table.add_column("Function", style="cyan")
                    func_table.add_column("Count", justify="right", style="yellow")
                    
                    for func_name in unique_funcs:
                        count = func_names.count(func_name)
                        func_table.add_row(func_name, str(count))
                    
                    console.print(func_table)
                    console.print()
                else:
                    output_lines.append(f"\n[Function Calls] {len(func_groups)} function call(s):")
                    for func_name in unique_funcs:
                        count = func_names.count(func_name)
                        output_lines.append(f"  {func_name}: {count}")
            
            # 4. CASE WHEN CLAUSES
            if case_groups:
                if use_rich:
                    case_table = Table(title="CASE WHEN Clauses", box=box.ROUNDED, border_style="magenta")
                    case_table.add_column("#", justify="right", style="cyan")
                    case_table.add_column("WHEN Count", justify="center", style="yellow")
                    case_table.add_column("Has ELSE", justify="center", style="green")
                    
                    for i, group in enumerate(case_groups, 1):
                        when_count = group.metadata.get('when_count', '?')
                        has_else = "✓" if group.metadata.get('has_else') else ""
                        case_table.add_row(str(i), str(when_count), has_else)
                    
                    console.print(case_table)
                    console.print()
                else:
                    output_lines.append(f"\n[CASE WHEN Clauses] {len(case_groups)} CASE expression(s):")
                    for i, group in enumerate(case_groups, 1):
                        when_count = group.metadata.get('when_count', '?')
                        has_else = group.metadata.get('has_else', False)
                        output_lines.append(f"  {i}. {when_count} WHEN clause(s)" + (", has ELSE" if has_else else ""))
            
            # 5. JOIN CLAUSES
            if join_groups:
                if use_rich:
                    join_table = Table(title="JOIN Clauses", box=box.ROUNDED, border_style="green")
                    join_table.add_column("Join Type", style="cyan", no_wrap=True)
                    join_table.add_column("Table", style="yellow")
                    join_table.add_column("Alias", style="magenta")
                    join_table.add_column("Has ON", justify="center", style="green")
                    
                    for group in join_groups:
                        join_type = group.metadata.get('join_type', 'JOIN')
                        table = group.metadata.get('table', '?')
                        alias = group.metadata.get('alias', '-')
                        has_on = "✓" if group.metadata.get('has_on') else ""
                        join_table.add_row(join_type, table, alias, has_on)
                    
                    console.print(join_table)
                else:
                    output_lines.append(f"\n[JOINs] Found {len(join_groups)} JOIN clause(s):")
                    for i, group in enumerate(join_groups, 1):
                        join_type = group.metadata.get('join_type', 'JOIN')
                        table = group.metadata.get('table', '?')
                        alias = group.metadata.get('alias')
                        has_on = group.metadata.get('has_on')
                        
                        line = f"  {i}. {join_type} {table}"
                        if alias:
                            line += f" AS {alias}"
                        if has_on:
                            line += " (with ON clause)"
                        output_lines.append(line)
            
            # === OPTIONAL SECTIONS (if present) ===
            
            # Window Functions (optional - show if present)
            if window_groups:
                if use_rich:
                    win_table = Table(title="Window Functions", box=box.ROUNDED, border_style="blue")
                    win_table.add_column("Function", style="cyan")
                    win_table.add_column("PARTITION BY", style="yellow")
                    win_table.add_column("ORDER BY", style="green")
                    
                    for group in window_groups:
                        func_name = group.metadata.get('function_name', '?')
                        partition_by = ', '.join(group.metadata.get('partition_by', []))
                        order_by = ', '.join(group.metadata.get('order_by', []))
                        win_table.add_row(func_name, partition_by or '-', order_by or '-')
                    
                    console.print()
                    console.print(win_table)
                else:
                    output_lines.append(f"\n[Window Functions] Found {len(window_groups)} window function(s):")
                    for i, group in enumerate(window_groups, 1):
                        func_name = group.metadata.get('function_name', '?')
                        partition = group.metadata.get('partition_by', [])
                        order = group.metadata.get('order_by', [])
                        line = f"  {i}. {func_name}"
                        if partition:
                            line += f" PARTITION BY {', '.join(partition)}"
                        if order:
                            line += f" ORDER BY {', '.join(order)}"
                        output_lines.append(line)
            
            # CTEs (optional - show if present)
            if cte_groups:
                if use_rich:
                    cte_table = Table(title="Common Table Expressions (CTEs)", box=box.ROUNDED, border_style="yellow")
                    cte_table.add_column("CTE Name", style="cyan")
                    cte_table.add_column("Columns", style="yellow")
                    cte_table.add_column("Recursive", justify="center", style="red")
                    
                    for group in cte_groups:
                        cte_name = group.metadata.get('cte_name', '?')
                        columns = ', '.join(group.metadata.get('columns', []))
                        is_recursive = "✓" if group.metadata.get('is_recursive') else ""
                        cte_table.add_row(cte_name, columns or '-', is_recursive)
                    
                    console.print()
                    console.print(cte_table)
                else:
                    output_lines.append(f"\n[CTEs] Found {len(cte_groups)} CTE(s):")
                    for i, group in enumerate(cte_groups, 1):
                        cte_name = group.metadata.get('cte_name', '?')
                        columns = group.metadata.get('columns', [])
                        is_recursive = group.metadata.get('is_recursive', False)
                        line = f"  {i}. {cte_name}"
                        if columns:
                            line += f" ({', '.join(columns)})"
                        if is_recursive:
                            line += " [RECURSIVE]"
                        output_lines.append(line)
            
            # Summary
            total_groups = (len(join_groups) + len(case_groups) + len(window_groups) + 
                          len(cte_groups) + len(func_groups) + len(subquery_groups) +
                          len(select_groups) + len(where_groups) + len(groupby_groups) +
                          len(having_groups) + len(orderby_groups) + len(union_groups) + len(limit_groups))
            
            if total_groups == 0:
                if use_rich:
                    console.print("\n[yellow]No semantic SQL structures detected at this level[/yellow]")
                    console.print(f"[dim]Try using --level=semantic for full analysis[/dim]")
                else:
                    output_lines.append("\nNo semantic SQL structures detected at this level")
                    output_lines.append(f"Try using --level=semantic for full analysis")
            else:
                if use_rich:
                    console.print(f"\n[bold green]Total semantic groups found: {total_groups}[/bold green]")
                else:
                    output_lines.append(f"\nTotal semantic groups found: {total_groups}")
        
        # Show token table only if explicitly requested or if semantic analysis is disabled
        show_token_table = args.show_tokens or args.no_semantic or args.format != "table"
        
        if show_token_table:
            # For grouped/structured/semantic levels, show hierarchy by default
            # Use tree format unless explicitly requesting flat view
            show_hierarchy = level != SemanticLevel.BASIC and args.format in ("table", "tree")
            
            if show_hierarchy:
                # Display hierarchical structure
                def build_tree(items, parent_tree=None, show_ws=False):
                    """Build a Rich Tree showing token groups and tokens"""
                    if parent_tree is None and HAS_RICH:
                        parent_tree = Tree(f"[bold cyan]SQL Structure ({level.value.upper()} level)[/bold cyan]")
                    
                    for item in items:
                        if isinstance(item, TokenGroup):
                            # Create node for group
                            group_label = f"[yellow]{item.group_type.value}[/yellow]"
                            if item.name:
                                group_label += f" [cyan]'{item.name}'[/cyan]"
                            if item.metadata:
                                meta_str = ", ".join(f"{k}={v}" for k, v in list(item.metadata.items())[:3])
                                if len(item.metadata) > 3:
                                    meta_str += "..."
                                group_label += f" [dim]({meta_str})[/dim]"
                            
                            if HAS_RICH:
                                branch = parent_tree.add(group_label)
                                build_tree(item.tokens, branch, show_ws)
                            else:
                                # Text-based tree (for non-rich output)
                                print(f"  {group_label}")
                        else:
                            # Token
                            if not show_ws and item.type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                                continue
                            
                            token_label = f"[green]{item.type.value}[/green]: "
                            value_str = repr(item.value)
                            if len(value_str) > 40:
                                value_str = value_str[:37] + "..."
                            token_label += f"[white]{value_str}[/white]"
                            
                            if HAS_RICH:
                                parent_tree.add(token_label)
                            else:
                                print(f"    {item.type.value}: {value_str}")
                    
                    return parent_tree
                
                if HAS_RICH and not args.output:
                    # Display Rich tree
                    tree = build_tree(tokens, show_ws=args.show_whitespace)
                    console.print()
                    console.print(tree)
                else:
                    # Text-based hierarchical output
                    def print_structure(items, indent=0, show_ws=False):
                        prefix = "  " * indent
                        for item in items:
                            if isinstance(item, TokenGroup):
                                group_label = f"{item.group_type.value}"
                                if item.name:
                                    group_label += f" '{item.name}'"
                                if item.metadata:
                                    meta_items = list(item.metadata.items())[:2]
                                    meta_str = ", ".join(f"{k}={v}" for k, v in meta_items)
                                    group_label += f" ({meta_str})"
                                output_lines.append(f"{prefix}[{group_label}]")
                                print_structure(item.tokens, indent + 1, show_ws)
                            else:
                                if not show_ws and item.type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                                    continue
                                value_str = repr(item.value)
                                if len(value_str) > 50:
                                    value_str = value_str[:47] + "..."
                                output_lines.append(f"{prefix}  {item.type.value}: {value_str}")
                    
                    output_lines.append("")
                    output_lines.append("=" * 80)
                    output_lines.append(f"SQL Structure ({level.value.upper()} level)")
                    output_lines.append("=" * 80)
                    print_structure(tokens, show_ws=args.show_whitespace)
            
            else:
                # Flatten tokens for basic level or when explicitly requested
                def flatten_to_tokens(items):
                    result = []
                    for item in items:
                        if isinstance(item, TokenGroup):
                            result.extend(flatten_to_tokens(item.tokens))
                        else:
                            result.append(item)
                    return result
                
                # Get flat token list
                flat_tokens = flatten_to_tokens(tokens) if level != SemanticLevel.BASIC else tokens
                
                # Filter tokens based on options
                display_tokens = flat_tokens
                if not args.show_whitespace:
                    display_tokens = [t for t in display_tokens if t.type not in (TokenType.WHITESPACE, TokenType.NEWLINE)]
                
                if args.keywords_only:
                    display_tokens = [t for t in display_tokens if t.type == TokenType.KEYWORD]
                
                # Generate token output
                if args.format == "json":
                    # JSON format
                    token_data = [{"value": t.value, "type": t.type.value} for t in display_tokens]
                    output_lines.append(json.dumps(token_data, indent=2))
                
                elif args.format == "simple":
                    # Simple format: one token per line
                    for token in display_tokens:
                        output_lines.append(f"{token.type.value}: {repr(token.value)}")
                
                else:  # table format
                    if HAS_RICH and not args.output:
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
