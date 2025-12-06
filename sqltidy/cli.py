import argparse
import sys
from .api import format_sql
from .config import TidyConfig

def main():
    parser = argparse.ArgumentParser(
        description="A SQL formatting tool"
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



    # -------------------
    # rewrite Command
    # -------------------

    rewrite_parser = subparsers.add_parser(
        "rewrite",
        help="Rewrite SQL queries",
        description="Rewrite SQL queries according to specified rules"
    )
    # You can add config-specific arguments here if needed


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
    # parse arguments
    # -------------------
    args = parser.parse_args()

    if args.command == "config":
        print("Launching config generator...")
        return

    # tidy command
    if args.command == "tidy":
        if args.input:
            with open(args.input, "r", encoding="utf-8") as f:
                sql = f.read()
        else:
            sql = sys.stdin.read()

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

if __name__ == "__main__":
    main()
