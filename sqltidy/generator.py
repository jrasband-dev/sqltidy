"""
Interactive configuration generator for sqltidy.
Generates dialect-specific config files.
"""

import json
import os
import shutil
import subprocess  # nosec B404 - subprocess needed for opening files in default editor
from pathlib import Path
from typing import Dict, Any, Optional
from .rulebook import SQLTidyConfig, SUPPORTED_DIALECTS

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich import box

console = Console()


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
            save_dialect_config_to_json(
                dialect, str(user_rulebook), include_plugins=False
            )


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


def get_default_filename(dialect: str) -> str:
    """Get default rulebook filename for a dialect."""
    return f"sqltidy_{dialect}.json"


def create_rulebook(
    dialect: Optional[str] = None,
    template_file: Optional[str] = None,
    include_plugins: bool = True,
) -> None:
    """
    Create a new rulebook file in the user's rulebook directory.

    **Auto-loads user plugins:** Automatically includes custom rules from ~/.sqltidy/rules/
    when include_plugins=True (default).

    Auto-generates config from rule metadata and saves to ~/.sqltidy/rulebooks/

    Args:
        dialect: SQL dialect (if None, will prompt user to select)
        template_file: Optional template rulebook file to copy from
        include_plugins: If True, include plugin rules in the config (default: True)
    """
    try:
        # Prompt for dialect if not provided
        if dialect is None:
            console.print()
            table = Table(
                title="Select SQL Dialect", box=box.ROUNDED, border_style="cyan"
            )
            table.add_column("#", justify="center", style="yellow", no_wrap=True)
            table.add_column("Dialect", style="cyan bold")

            for i, d in enumerate(SUPPORTED_DIALECTS, 1):
                table.add_row(str(i), d)

            console.print(table)
            console.print()

            while True:
                choice = input(
                    f"Enter your choice (1-{len(SUPPORTED_DIALECTS)}): "
                ).strip()
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(SUPPORTED_DIALECTS):
                        dialect = SUPPORTED_DIALECTS[idx]
                        break
                except ValueError:
                    pass
                console.print(
                    f"[yellow]Please enter a number between 1 and {len(SUPPORTED_DIALECTS)}[/yellow]"
                )
        elif dialect not in SUPPORTED_DIALECTS:
            console.print(f"\n[red]✗ Error:[/red] Unsupported dialect '{dialect}'")
            console.print(
                f"[yellow]Supported dialects:[/yellow] {', '.join(SUPPORTED_DIALECTS)}\n"
            )
            return

        # Load template if provided
        if template_file:
            try:
                console.print(f"\n[cyan]Loading template from:[/cyan] {template_file}")
                config = SQLTidyConfig.from_file(template_file)
                config.dialect = dialect  # Override dialect
            except Exception as e:
                console.print(
                    f"[yellow]⚠ Warning:[/yellow] Could not load template file: {e}"
                )
                console.print(
                    "[dim]Proceeding with auto-generation from rules...[/dim]\n"
                )
                from .config_schema import generate_dialect_config

                config_dict = generate_dialect_config(
                    dialect, include_plugins=include_plugins
                )
                config = SQLTidyConfig.from_dict(config_dict)
        else:
            # Auto-generate from rules
            from .config_schema import generate_dialect_config

            console.print(
                "\n[cyan]Auto-generating config from rule metadata...[/cyan]"
            )
            if include_plugins:
                console.print("[dim]Including plugin rules in configuration...[/dim]")
            config_dict = generate_dialect_config(
                dialect, include_plugins=include_plugins
            )
            config = SQLTidyConfig.from_dict(config_dict)

        # Save to user's rulebook directory
        user_dir = get_user_rulebooks_dir()
        user_dir.mkdir(parents=True, exist_ok=True)
        output_path = user_dir / f"sqltidy_{dialect}.json"

        # Warn if rulebook already exists
        if output_path.exists():
            console.print()
            console.print(
                f"[yellow]⚠ Warning:[/yellow] Rulebook already exists: [cyan]{output_path}[/cyan]"
            )
            confirm = input("Overwrite existing rulebook? [y/N]: ").strip().lower()
            if confirm not in ("y", "yes"):
                console.print("[yellow]Rulebook creation cancelled.[/yellow]")
                return

        config.save(str(output_path))

        console.print()
        console.print(
            Panel(
                f"[green]✓ Rulebook created successfully![/green]\n\n"
                f"[cyan]File:[/cyan] {output_path}\n"
                f"{'[dim]Plugin rules included in configuration[/dim]' if include_plugins else ''}",
                title="[bold green]Success",
                border_style="green",
                box=box.ROUNDED,
            )
        )
        console.print()

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Rulebook creation cancelled.[/yellow]")
    except Exception as e:
        console.print(f"\n[red]✗ Error:[/red] {e}")
        raise


def list_rulebooks(directory: str = ".") -> None:
    """
    List rulebook files in user rulebook directory.

    Args:
        directory: Directory to search (default: current directory)
    """
    from rich.tree import Tree
    from rich.panel import Panel

    user_dir = get_user_rulebooks_dir()

    console.print()
    console.print(
        Panel(
            f"[cyan]{user_dir}[/cyan]",
            title="[bold]User Rulebook Directory",
            border_style="cyan",
            box=box.ROUNDED,
        )
    )
    console.print()

    # Check if directory exists
    if not user_dir.exists():
        console.print(
            Panel(
                "[yellow]Directory does not exist yet.[/yellow]\n\n"
                "[dim]Tip: Create a rulebook with[/dim]\n"
                "[cyan]sqltidy rulebooks create -d <dialect>[/cyan]",
                title="[bold yellow]No Rulebooks Found",
                border_style="yellow",
                box=box.ROUNDED,
            )
        )
        return

    # List all files in the user rulebook directory
    all_files = list(user_dir.glob("*"))

    if not all_files:
        console.print(
            Panel(
                "[yellow]Directory is empty.[/yellow]\n\n"
                "[dim]Tip: Create a rulebook with[/dim]\n"
                "[cyan]sqltidy rulebooks create -d <dialect>[/cyan]",
                title="[bold yellow]No Rulebooks Found",
                border_style="yellow",
                box=box.ROUNDED,
            )
        )
        return

    # Separate rulebook files from other files
    rulebook_files = [
        f
        for f in all_files
        if f.name.startswith("sqltidy_") and f.name.endswith(".json")
    ]
    other_files = [f for f in all_files if f not in rulebook_files]

    # Create tree for rulebooks
    tree = Tree(
        f"[bold cyan]📚 Rulebooks ({len(rulebook_files)} found)[/bold cyan]",
        guide_style="cyan",
    )

    if rulebook_files:
        for rulebook_file in sorted(rulebook_files):
            try:
                cfg = SQLTidyConfig.from_file(str(rulebook_file))
                # Count enabled rules
                tidy_rules = (
                    sum(1 for v in cfg.tidy.values() if v)
                    if hasattr(cfg, "tidy") and cfg.tidy
                    else 0
                )
                rewrite_rules = (
                    sum(1 for v in cfg.rewrite.values() if v)
                    if hasattr(cfg, "rewrite") and cfg.rewrite
                    else 0
                )
                total_rules = tidy_rules + rewrite_rules

                # Get file size
                file_size = rulebook_file.stat().st_size
                size_kb = file_size / 1024

                # Create tree entry
                file_branch = tree.add(f"[green]📄 {rulebook_file.name}[/green]")
                file_branch.add(f"[yellow]Dialect:[/yellow] [cyan]{cfg.dialect}[/cyan]")
                file_branch.add(
                    f"[yellow]Rules enabled:[/yellow] {total_rules} ([cyan]{tidy_rules} tidy[/cyan], [magenta]{rewrite_rules} rewrite[/magenta])"
                )
                file_branch.add(f"[yellow]Size:[/yellow] {size_kb:.1f} KB")
            except Exception as e:
                file_branch = tree.add(f"[red]📄 {rulebook_file.name}[/red]")
                file_branch.add(f"[red]Error: {e}[/red]")
    else:
        tree.add("[yellow]No rulebook files found[/yellow]")

    console.print(tree)

    # Show other files if any
    if other_files:
        console.print()
        other_tree = Tree(
            f"[bold yellow]📁 Other Files ({len(other_files)})[/bold yellow]",
            guide_style="yellow",
        )
        for file in sorted(other_files):
            if file.is_dir():
                other_tree.add(f"[blue]📁 {file.name}[/blue] [dim](directory)[/dim]")
            else:
                other_tree.add(f"[dim]📄 {file.name}[/dim] [dim](file)[/dim]")
        console.print(other_tree)

    console.print()


def edit_rulebook(rulebook_name: Optional[str] = None) -> None:
    """
    Edit an existing rulebook file in the user's rulebook directory.
    Opens the file in the system's default editor.

    Note: This only edits existing files. Use 'sqltidy rulebooks create' to create new rulebooks.

    Args:
        rulebook_name: Name of the rulebook file or dialect (e.g., 'postgresql' or 'sqltidy_postgresql.json')
    """
    from rich.panel import Panel
    from rich.table import Table

    user_dir = get_user_rulebooks_dir()

    # Check if user directory exists
    if not user_dir.exists():
        console.print()
        console.print(
            Panel(
                "[yellow]No user rulebooks found.[/yellow]\n\n"
                "[dim]Tip: Create a rulebook with[/dim]\n"
                "[cyan]sqltidy rulebooks create -d <dialect>[/cyan]",
                title="[bold yellow]No Rulebooks",
                border_style="yellow",
                box=box.ROUNDED,
            )
        )
        return

    # Get all existing user rulebooks
    existing_user_rulebooks = list(user_dir.glob("sqltidy_*.json"))

    if not existing_user_rulebooks:
        console.print()
        console.print(
            Panel(
                f"[yellow]No user rulebooks found.[/yellow]\n\n"
                f"[dim]User rulebook directory: {user_dir}[/dim]\n\n"
                f"[dim]Tip: Create a rulebook with[/dim]\n"
                f"[cyan]sqltidy rulebooks create -d <dialect>[/cyan]",
                title="[bold yellow]No Rulebooks",
                border_style="yellow",
                box=box.ROUNDED,
            )
        )
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
            name = rulebook_file.stem.replace("sqltidy_", "")
            available_options[name] = rulebook_file

    # If no rulebook specified, let user choose
    if rulebook_name is None:
        console.print()
        table = Table(title="Available Rulebooks", box=box.ROUNDED, border_style="cyan")
        table.add_column("#", justify="center", style="yellow", no_wrap=True)
        table.add_column("Dialect", style="cyan bold")
        table.add_column("File", style="dim")

        sorted_options = sorted(available_options.items())
        for i, (name, filepath) in enumerate(sorted_options, 1):
            table.add_row(str(i), name, filepath.name)

        console.print(table)
        console.print()

        while True:
            choice = input(
                f"\nSelect rulebook to edit (1-{len(sorted_options)}): "
            ).strip()
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
            console.print()
            console.print(
                Panel(
                    f"[red]Rulebook '{rulebook_name}' not found.[/red]\n\n"
                    f"[yellow]Existing rulebooks:[/yellow] {', '.join(sorted(available_options.keys()))}\n\n"
                    f"[dim]Tip: Create with[/dim]\n"
                    f"[cyan]sqltidy rulebooks create -d {rulebook_name}[/cyan]",
                    title="[bold red]Not Found",
                    border_style="red",
                    box=box.ROUNDED,
                )
            )
            return

    console.print()
    console.print(
        f"[green]✓[/green] Opening user rulebook: [cyan]{selected_file.name}[/cyan]"
    )

    # Open in default editor
    try:
        if os.name == "nt":  # Windows
            os.startfile(selected_file)  # nosec B606 - User's own rulebook file
        elif os.name == "posix":  # macOS and Linux
            opener = "open" if os.uname().sysname == "Darwin" else "xdg-open"
            subprocess.run([opener, str(selected_file)], check=False)  # nosec B603 - Opening user's own rulebook file

        console.print()
        console.print(
            Panel(
                f"[dim]This file overrides auto-generated defaults.[/dim]\n\n"
                f"[yellow]To revert to auto-generated config, delete:[/yellow]\n"
                f"[cyan]{selected_file}[/cyan]",
                title="[bold]💡 Tip",
                border_style="blue",
                box=box.ROUNDED,
            )
        )
    except Exception as e:
        console.print(
            f"\n[yellow]⚠ Warning:[/yellow] Couldn't open editor automatically: {e}"
        )
        console.print(f"[dim]Please manually edit:[/dim] [cyan]{selected_file}[/cyan]")


def reset_rulebook(rulebook_name: Optional[str] = None) -> None:
    """
    Reset a user rulebook to bundled default by removing the user's customization.

    Args:
        rulebook_name: Name of the rulebook file or dialect to reset, or 'all' to reset all
    """
    from rich.panel import Panel
    from rich.table import Table

    user_dir = get_user_rulebooks_dir()

    if not user_dir.exists():
        console.print()
        console.print(
            Panel(
                "[yellow]No user rulebooks to reset.[/yellow]",
                border_style="yellow",
                box=box.ROUNDED,
            )
        )
        return

    user_rulebooks = list(user_dir.glob("sqltidy_*.json"))

    if not user_rulebooks:
        console.print()
        console.print(
            Panel(
                "[yellow]No user rulebooks to reset.[/yellow]",
                border_style="yellow",
                box=box.ROUNDED,
            )
        )
        return

    # Handle 'all' option to reset all rulebooks
    if rulebook_name == "all":
        console.print()
        table = Table(
            title=f"Rulebooks to Reset ({len(user_rulebooks)} found)",
            box=box.ROUNDED,
            border_style="yellow",
        )
        table.add_column("Dialect", style="cyan bold")
        table.add_column("File", style="dim")

        for rulebook_file in sorted(user_rulebooks):
            try:
                cfg = SQLTidyConfig.from_file(str(rulebook_file))
                table.add_row(cfg.dialect, rulebook_file.name)
            except Exception:
                table.add_row("?", rulebook_file.name)

        console.print(table)
        console.print()

        confirm = (
            input(
                f"Reset all {len(user_rulebooks)} rulebook(s) to bundled defaults? [y/N]: "
            )
            .strip()
            .lower()
        )
        if confirm in ("y", "yes"):
            count = 0
            for rulebook_file in user_rulebooks:
                rulebook_file.unlink()
                count += 1
            console.print()
            console.print(
                Panel(
                    f"[green]✓ Reset {count} rulebook(s) to bundled defaults.[/green]",
                    border_style="green",
                    box=box.ROUNDED,
                )
            )
        else:
            console.print("\n[yellow]Reset cancelled.[/yellow]")
        return

    # If no rulebook specified, let user choose
    if rulebook_name is None:
        console.print()
        table = Table(
            title="Customized Rulebooks", box=box.ROUNDED, border_style="cyan"
        )
        table.add_column("#", justify="center", style="yellow", no_wrap=True)
        table.add_column("Dialect", style="cyan bold")
        table.add_column("File", style="dim")

        for i, rulebook_file in enumerate(sorted(user_rulebooks), 1):
            try:
                cfg = SQLTidyConfig.from_file(str(rulebook_file))
                table.add_row(str(i), cfg.dialect, rulebook_file.name)
            except Exception:
                table.add_row(str(i), "?", rulebook_file.name)

        console.print(table)
        console.print()

        while True:
            choice = input(
                f"\nSelect rulebook to reset (1-{len(user_rulebooks)}): "
            ).strip()
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
            console.print()
            console.print(
                Panel(
                    f"[yellow]No user customization found for '{rulebook_name}'.[/yellow]",
                    border_style="yellow",
                    box=box.ROUNDED,
                )
            )
            return

    # Confirm deletion
    confirm = (
        input(f"\nReset {rulebook_file.name} to bundled default? [y/N]: ")
        .strip()
        .lower()
    )
    if confirm in ("y", "yes"):
        rulebook_file.unlink()
        console.print()
        console.print(
            Panel(
                f"[green]✓ Reset {rulebook_file.name} to bundled default.[/green]",
                border_style="green",
                box=box.ROUNDED,
            )
        )
    else:
        console.print("\n[yellow]Reset cancelled.[/yellow]")


def update_rulebook(
    rulebook_name: Optional[str] = None, include_plugins: bool = True
) -> None:
    """
    Update an existing rulebook file with new rules that have been added since creation.
    Preserves user's existing settings and only adds new fields from newly registered rules.

    **Auto-loads user plugins:** Automatically includes custom rules from ~/.sqltidy/rules/
    when include_plugins=True (default).

    Args:
        rulebook_name: Name of the rulebook file or dialect to update, or 'all' to update all
        include_plugins: Whether to include plugin rules in the update (default: True)
    """
    from .config_schema import generate_dialect_config
    from rich.panel import Panel
    from rich.table import Table
    from rich.tree import Tree

    user_dir = get_user_rulebooks_dir()

    if not user_dir.exists():
        console.print()
        console.print(
            Panel(
                "[yellow]No user rulebooks to update.[/yellow]\n\n"
                "[dim]Tip: Use[/dim] [cyan]sqltidy rulebooks create[/cyan] [dim]to create a new rulebook.[/dim]",
                border_style="yellow",
                box=box.ROUNDED,
            )
        )
        return

    user_rulebooks = list(user_dir.glob("sqltidy_*.json"))

    if not user_rulebooks:
        console.print()
        console.print(
            Panel(
                "[yellow]No user rulebooks to update.[/yellow]\n\n"
                "[dim]Tip: Use[/dim] [cyan]sqltidy rulebooks create[/cyan] [dim]to create a new rulebook.[/dim]",
                border_style="yellow",
                box=box.ROUNDED,
            )
        )
        return

    # Handle 'all' option to update all rulebooks
    if rulebook_name == "all":
        console.print()
        table = Table(
            title=f"Rulebooks to Update ({len(user_rulebooks)} found)",
            box=box.ROUNDED,
            border_style="cyan",
        )
        table.add_column("Dialect", style="cyan bold")
        table.add_column("File", style="dim")

        for rulebook_file in sorted(user_rulebooks):
            try:
                cfg = SQLTidyConfig.from_file(str(rulebook_file))
                table.add_row(cfg.dialect, rulebook_file.name)
            except Exception:
                table.add_row("?", rulebook_file.name)

        console.print(table)
        console.print()

        confirm = (
            input(
                f"Update all {len(user_rulebooks)} rulebook(s) with new rules? [y/N]: "
            )
            .strip()
            .lower()
        )
        if confirm not in ("y", "yes"):
            console.print("\n[yellow]Update cancelled.[/yellow]")
            return

        console.print()
        updated_count = 0
        for rulebook_file in sorted(user_rulebooks):
            try:
                # Load existing config
                existing_config = load_rulebook_file(str(rulebook_file))
                dialect = existing_config.get("dialect", "postgresql")

                # Generate fresh config from current rules
                fresh_config = generate_dialect_config(
                    dialect, include_plugins=include_plugins
                )

                # Merge nested structure: keep existing values, add new fields
                merged_config = {"dialect": dialect, "tidy": {}, "rewrite": {}}

                # Get existing tidy and rewrite sections
                existing_tidy = existing_config.get("tidy", {})
                existing_rewrite = existing_config.get("rewrite", {})

                # Merge tidy section
                fresh_tidy = fresh_config.get("tidy", {})
                merged_config["tidy"] = {**fresh_tidy, **existing_tidy}

                # Merge rewrite section
                fresh_rewrite = fresh_config.get("rewrite", {})
                merged_config["rewrite"] = {**fresh_rewrite, **existing_rewrite}

                # Find new fields
                new_tidy_fields = set(fresh_tidy.keys()) - set(existing_tidy.keys())
                new_rewrite_fields = set(fresh_rewrite.keys()) - set(
                    existing_rewrite.keys()
                )
                new_fields = new_tidy_fields | new_rewrite_fields

                if new_fields:
                    # Save updated config
                    with open(rulebook_file, "w", encoding="utf-8") as f:
                        json.dump(merged_config, f, indent=2)
                    console.print(
                        f"  [green]✓[/green] Updated [cyan]{dialect}[/cyan]: Added {len(new_fields)} new field(s)"
                    )
                    if new_tidy_fields:
                        console.print("    [yellow]Tidy rules:[/yellow]")
                        for field in sorted(new_tidy_fields):
                            console.print(f"      [green]+[/green] {field}")
                    if new_rewrite_fields:
                        console.print("    [magenta]Rewrite rules:[/magenta]")
                        for field in sorted(new_rewrite_fields):
                            console.print(f"      [green]+[/green] {field}")
                    updated_count += 1
                else:
                    console.print(f"  [dim]• {dialect}: Already up-to-date[/dim]")
            except Exception as e:
                console.print(
                    f"  [red]✗[/red] Error updating {rulebook_file.name}: {e}"
                )

        console.print()
        if updated_count > 0:
            console.print(
                Panel(
                    f"[green]✓ Updated {updated_count} rulebook(s).[/green]",
                    border_style="green",
                    box=box.ROUNDED,
                )
            )
        else:
            console.print(
                Panel(
                    "[yellow]All rulebooks are already up-to-date![/yellow]",
                    border_style="yellow",
                    box=box.ROUNDED,
                )
            )
        return

    # Handle single rulebook update
    if rulebook_name is None:
        console.print()
        table = Table(
            title="Available Rulebooks to Update", box=box.ROUNDED, border_style="cyan"
        )
        table.add_column("#", justify="center", style="yellow", no_wrap=True)
        table.add_column("Dialect", style="cyan bold")
        table.add_column("File", style="dim")

        for i, rulebook_file in enumerate(sorted(user_rulebooks), 1):
            try:
                cfg = SQLTidyConfig.from_file(str(rulebook_file))
                table.add_row(str(i), cfg.dialect, rulebook_file.name)
            except Exception:
                table.add_row(str(i), "?", rulebook_file.name)

        console.print(table)
        console.print()

        while True:
            choice = input(
                f"\nSelect rulebook to update (1-{len(user_rulebooks)}): "
            ).strip()
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
            console.print()
            console.print(
                Panel(
                    f"[yellow]No user customization found for '{rulebook_name}'.[/yellow]\n\n"
                    f"[dim]Tip: Use[/dim] [cyan]sqltidy rulebooks create -d {rulebook_name}[/cyan] [dim]to create one.[/dim]",
                    border_style="yellow",
                    box=box.ROUNDED,
                )
            )
            return

    # Load existing config
    try:
        existing_config = load_rulebook_file(str(rulebook_file))
        dialect = existing_config.get("dialect", "postgresql")
    except Exception as e:
        console.print()
        console.print(
            Panel(
                f"[red]Error loading {rulebook_file.name}:[/red] {e}",
                border_style="red",
                box=box.ROUNDED,
            )
        )
        return

    # Generate fresh config from current rules
    try:
        fresh_config = generate_dialect_config(dialect, include_plugins=include_plugins)
    except Exception as e:
        console.print()
        console.print(
            Panel(
                f"[red]Error generating config for {dialect}:[/red] {e}",
                border_style="red",
                box=box.ROUNDED,
            )
        )
        return

    # Merge nested structure: keep existing values, add new fields
    merged_config = {"dialect": dialect, "tidy": {}, "rewrite": {}}

    # Get existing tidy and rewrite sections
    existing_tidy = existing_config.get("tidy", {})
    existing_rewrite = existing_config.get("rewrite", {})

    # Merge tidy section
    fresh_tidy = fresh_config.get("tidy", {})
    merged_config["tidy"] = {**fresh_tidy, **existing_tidy}

    # Merge rewrite section
    fresh_rewrite = fresh_config.get("rewrite", {})
    merged_config["rewrite"] = {**fresh_rewrite, **existing_rewrite}

    # Find new fields
    new_tidy_fields = set(fresh_tidy.keys()) - set(existing_tidy.keys())
    new_rewrite_fields = set(fresh_rewrite.keys()) - set(existing_rewrite.keys())
    new_fields = new_tidy_fields | new_rewrite_fields

    if not new_fields:
        console.print()
        console.print(
            Panel(
                f"[green]✓ {dialect} rulebook is already up-to-date![/green]",
                border_style="green",
                box=box.ROUNDED,
            )
        )
        return

    # Show what will be added
    console.print()
    tree = Tree(
        f"[bold cyan]New Fields for {dialect} Rulebook ({len(new_fields)} found)[/bold cyan]",
        guide_style="cyan",
    )

    if new_tidy_fields:
        tidy_branch = tree.add("[yellow]Tidy Rules[/yellow]")
        for field in sorted(new_tidy_fields):
            default_value = fresh_tidy[field]
            tidy_branch.add(f"[green]+[/green] {field} = [dim]{default_value}[/dim]")

    if new_rewrite_fields:
        rewrite_branch = tree.add("[magenta]Rewrite Rules[/magenta]")
        for field in sorted(new_rewrite_fields):
            default_value = fresh_rewrite[field]
            rewrite_branch.add(f"[green]+[/green] {field} = [dim]{default_value}[/dim]")

    console.print(tree)
    console.print()

    confirm = (
        input(f"Update {rulebook_file.name} with new fields? [Y/n]: ").strip().lower()
    )
    if confirm in ("", "y", "yes"):
        # Save updated config
        with open(rulebook_file, "w", encoding="utf-8") as f:
            json.dump(merged_config, f, indent=2)
        console.print()
        console.print(
            Panel(
                f"[green]✓ Updated {rulebook_file.name} with {len(new_fields)} new field(s).[/green]",
                border_style="green",
                box=box.ROUNDED,
            )
        )
    else:
        console.print("\n[yellow]Update cancelled.[/yellow]")


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

    if not source_path.suffix == ".py":
        print(f"Error: rule file must be a Python file (.py): {rule_file}")
        return

    # Validate the rule file by attempting to load it
    try:
        from .plugins import load_rule_file

        rules = load_rule_file(str(source_path))
        if not rules:
            print(f"Warning: No rules found in {rule_file}")
            print(
                "Make sure your file uses @sqltidy_rule decorator or defines BaseRule classes."
            )
            confirm = input("Add anyway? [y/N]: ").strip().lower()
            if confirm not in ("y", "yes"):
                print("rule not added.")
                return
    except Exception as e:
        print(f"Error validating rule: {e}")
        confirm = input("Add anyway? [y/N]: ").strip().lower()
        if confirm not in ("y", "yes"):
            print("rule not added.")
            return

    # Create user rules directory if it doesn't exist
    rules_dir = get_user_rules_dir()
    rules_dir.mkdir(parents=True, exist_ok=True)

    # Copy rule file to user directory
    dest_path = rules_dir / source_path.name

    if dest_path.exists():
        confirm = (
            input(f"rule '{source_path.name}' already exists. Overwrite? [y/N]: ")
            .strip()
            .lower()
        )
        if confirm not in ("y", "yes"):
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
    tidy_rules = [r for r in built_in_rules if getattr(r, "rule_type", None) == "tidy"]
    rewrite_rules = [
        r for r in built_in_rules if getattr(r, "rule_type", None) == "rewrite"
    ]
    other_rules = [
        r
        for r in built_in_rules
        if getattr(r, "rule_type", None) not in ["tidy", "rewrite"]
    ]

    # Rich formatted output
    console.print()

    # Built-in Tidy Rules
    if tidy_rules:
        tidy_table = Table(
            title="Built-in Tidy Rules (Formatting)",
            box=box.ROUNDED,
            border_style="cyan",
        )
        tidy_table.add_column("Rule Name", style="cyan bold", no_wrap=True)
        tidy_table.add_column("Order", justify="center", style="yellow")
        tidy_table.add_column("Dialects", style="green")

        for rule in sorted(tidy_rules, key=lambda r: getattr(r, "order", 100)):
            rule_name = rule.__class__.__name__
            order = str(getattr(rule, "order", "?"))
            dialects = getattr(rule, "supported_dialects", None)
            dialect_info = ", ".join(sorted(dialects)) if dialects else "all dialects"
            tidy_table.add_row(rule_name, order, dialect_info)

        console.print(tidy_table)
        console.print()

    # Built-in Rewrite Rules
    if rewrite_rules:
        rewrite_table = Table(
            title="Built-in Rewrite Rules (Transformations)",
            box=box.ROUNDED,
            border_style="magenta",
        )
        rewrite_table.add_column("Rule Name", style="magenta bold", no_wrap=True)
        rewrite_table.add_column("Order", justify="center", style="yellow")
        rewrite_table.add_column("Dialects", style="green")

        for rule in sorted(rewrite_rules, key=lambda r: getattr(r, "order", 100)):
            rule_name = rule.__class__.__name__
            order = str(getattr(rule, "order", "?"))
            dialects = getattr(rule, "supported_dialects", None)
            dialect_info = ", ".join(sorted(dialects)) if dialects else "all dialects"
            rewrite_table.add_row(rule_name, order, dialect_info)

        console.print(rewrite_table)
        console.print()

    # Other Rules
    if other_rules:
        other_table = Table(
            title="Other Built-in Rules", box=box.ROUNDED, border_style="blue"
        )
        other_table.add_column("Rule Name", style="blue bold", no_wrap=True)
        other_table.add_column("Order", justify="center", style="yellow")

        for rule in sorted(other_rules, key=lambda r: getattr(r, "order", 100)):
            rule_name = rule.__class__.__name__
            order = str(getattr(rule, "order", "?"))
            other_table.add_row(rule_name, order)

        console.print(other_table)
        console.print()

    # Plugin Rules
    rules_dir = get_user_rules_dir()

    if not rules_dir.exists() or not list(rules_dir.glob("*.py")):
        console.print(
            Panel(
                f"[yellow]No plugin rules installed.[/yellow]\n"
                f"[dim]Plugin directory: {rules_dir}[/dim]",
                title="[bold yellow]Plugin Rules",
                border_style="yellow",
                box=box.ROUNDED,
            )
        )
    else:
        rule_files = list(rules_dir.glob("*.py"))

        # Create a tree for plugin rules
        tree = Tree(
            f"[bold yellow]Plugin Rules ({len(rule_files)} files)[/bold yellow]",
            guide_style="yellow",
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
                        rule_type = getattr(rule, "rule_type", "unknown")
                        order = getattr(rule, "order", "?")
                        dialects = getattr(rule, "supported_dialects", None)
                        dialect_info = (
                            f" ({', '.join(sorted(dialects))})"
                            if dialects
                            else " (all dialects)"
                        )

                        type_color = (
                            "cyan"
                            if rule_type == "tidy"
                            else "magenta"
                            if rule_type == "rewrite"
                            else "white"
                        )
                        file_branch.add(
                            f"[{type_color}]{rule_cls.__name__}[/{type_color}] [dim]type={rule_type}, order={order}{dialect_info}[/dim]"
                        )
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

        console.print(
            Panel(
                summary_table,
                title="[bold]Summary",
                border_style="cyan",
                box=box.ROUNDED,
            )
        )
        console.print()


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
    if not rule_name.endswith(".py"):
        rule_name += ".py"

    rule_file = rules_dir / rule_name

    if not rule_file.exists():
        print(f"Rule not found: {rule_name}")
        print("\nUse 'sqltidy rules list' to see installed rules.")
        return

    # Confirm deletion
    confirm = input(f"Remove rule '{rule_name}'? [y/N]: ").strip().lower()
    if confirm in ("y", "yes"):
        rule_file.unlink()
        print(f"\n✓ Removed rule: {rule_name}")
    else:
        print("\nRemoval cancelled.")
