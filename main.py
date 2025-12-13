#!/usr/bin/env python3
"""
F.U.C.K. - Fund Utilization and Categorization Kit
Main CLI entry point
"""

import argparse
import sys
from package import (
    initialize_crypto,
    load_hash_table,
    save_hash_table,
    process_csv_file,
    Config,
    cli
)
from package.storage import print_hash_table, get_categories_and_totals


def cmd_process(args):
    """Process a CSV file and categorize transactions."""
    print(f"Processing CSV file: {args.csv_file}")

    # Initialize crypto
    cipher_suite, SALT = initialize_crypto()

    # Load hash table
    hash_table = load_hash_table(cipher_suite)
    print("Hash table loaded successfully.")

    # Process CSV file
    try:
        process_csv_file(args.csv_file, hash_table, cipher_suite, SALT)
        print("CSV file processed successfully.")
    except FileNotFoundError:
        print(f"Error: File not found: {args.csv_file}")
        return 1
    except Exception as e:
        print(f"Error processing CSV: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    # Save hash table
    try:
        save_hash_table(hash_table, cipher_suite)
        print("Hash table saved successfully.")
    except Exception as e:
        print(f"Error saving hash table: {e}")
        return 1

    return 0


def cmd_view(args):
    """View category totals."""
    print("Viewing category totals...")

    # Initialize crypto
    cipher_suite, SALT = initialize_crypto()

    # Load hash table
    hash_table = load_hash_table(cipher_suite)

    if args.all:
        print_hash_table(hash_table)
    else:
        categories = get_categories_and_totals(hash_table)

    return 0


def cmd_config(args):
    """View or edit configuration."""
    config = Config.load()

    if args.show:
        print(f"\nConfiguration:")
        print(f"  Storage directory: {config.storage_dir}")
        print(f"  Hash table file: {config.hash_table_file}")
        print(f"  Config file: {config.config_file}")
        print(f"  Saved column mappings: {len(config.column_mappings)}")
        print(f"  Default categories: {len(config.default_categories)}")

    elif args.list_categories:
        print("\nDefault Categories:")
        for i, cat in enumerate(config.default_categories, 1):
            print(f"  {i}. {cat}")

    return 0


def cmd_version(args):
    """Show version information."""
    import package
    print(f"F.U.C.K. version {package.__version__}")
    print(f"Author: {package.__author__}")
    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="F.U.C.K. - Fund Utilization and Categorization Kit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s process statement.csv     Process a bank statement
  %(prog)s view                      View category totals
  %(prog)s config --show             Show configuration
  %(prog)s version                   Show version info
        """
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Process command
    process_parser = subparsers.add_parser(
        'process',
        help='Process a CSV file and categorize transactions'
    )
    process_parser.add_argument(
        'csv_file',
        type=str,
        help='Path to CSV file to process'
    )
    process_parser.set_defaults(func=cmd_process)

    # View command
    view_parser = subparsers.add_parser(
        'view',
        help='View category totals and statistics'
    )
    view_parser.add_argument(
        '--all',
        action='store_true',
        help='Show all details including addresses'
    )
    view_parser.set_defaults(func=cmd_view)

    # Config command
    config_parser = subparsers.add_parser(
        'config',
        help='View or edit configuration'
    )
    config_parser.add_argument(
        '--show',
        action='store_true',
        help='Show current configuration'
    )
    config_parser.add_argument(
        '--list-categories',
        action='store_true',
        help='List default categories'
    )
    config_parser.set_defaults(func=cmd_config)

    # Version command
    version_parser = subparsers.add_parser(
        'version',
        help='Show version information'
    )
    version_parser.set_defaults(func=cmd_version)

    # Parse arguments
    args = parser.parse_args()

    # If no command specified, show help
    if not args.command:
        parser.print_help()
        return 0

    # Execute command
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return 130
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
