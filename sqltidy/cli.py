# sqltidy/cli.py
import argparse
import sys
from .api import format_sql
from .config import FormatterConfig

def main():
    parser = argparse.ArgumentParser(description="sqltidy — A SQL formatting tool")
    parser.add_argument("command", choices=["tidy", "config"], help="Subcommand")
    parser.add_argument("input", nargs="?", help="SQL file to format")
    parser.add_argument("-o", "--output", help="Output file")
    parser.add_argument("--no-uppercase", action="store_true")
    parser.add_argument("--newline-after-select", action="store_true")
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()

    if args.command == "config":
        # Here you would implement your interactive config generator
        print("Launching config generator...")
        return

    # command == tidy
    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            sql = f.read()
    else:
        sql = sys.stdin.read()

    config = FormatterConfig(
        uppercase_keywords=not args.no_uppercase,
        newline_after_select=args.newline_after_select,
        compact=args.compact
    )

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

if __name__ == "__main__":
    main()
