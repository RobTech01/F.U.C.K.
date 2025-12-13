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

    # Initialize crypto with error handling
    try:
        cipher_suite, SALT = initialize_crypto()
    except KeyboardInterrupt:
        print("\nCrypto initialization cancelled by user")
        return 130
    except Exception as e:
        print(f"Error initializing crypto: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    # Load hash table with error handling
    try:
        hash_table = load_hash_table(cipher_suite)
        print("Hash table loaded successfully.")
    except Exception as e:
        print(f"Error loading hash table: {e}")
        if cli.confirm_action("Start with a new empty hash table?"):
            from package.storage import initialize_hash_table
            hash_table = initialize_hash_table()
            print("Initialized new hash table.")
        else:
            print("Cannot proceed without hash table.")
            return 1

    # Process CSV file with comprehensive error handling
    try:
        enable_review = not args.no_review
        stats = process_csv_file(args.csv_file, hash_table, cipher_suite, SALT, review=enable_review)
        print(f"\n✓ CSV file processed successfully.")
        print(f"  Processed: {stats['processed']}/{stats['total']} transactions")
        if stats['skipped'] > 0:
            print(f"  Skipped: {stats['skipped']} transactions (validation errors)")
        if stats['errors'] > 0:
            print(f"  Errors: {stats['errors']} transactions (processing errors)")
    except FileNotFoundError:
        print(f"✗ Error: File not found: {args.csv_file}")
        return 1
    except ValueError as e:
        print(f"✗ Error: Invalid CSV file: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n\nProcessing interrupted by user.")
        if cli.confirm_action("Save progress so far?"):
            try:
                save_hash_table(hash_table, cipher_suite)
                print("✓ Progress saved successfully.")
                return 130
            except Exception as e:
                print(f"✗ Error saving progress: {e}")
                return 1
        else:
            print("Progress discarded.")
            return 130
    except Exception as e:
        print(f"✗ Error processing CSV: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        if cli.confirm_action("Save partial results?"):
            try:
                save_hash_table(hash_table, cipher_suite)
                print("✓ Partial results saved.")
            except Exception as save_error:
                print(f"✗ Error saving partial results: {save_error}")
        return 1

    # Save hash table with error handling
    try:
        save_hash_table(hash_table, cipher_suite)
        print("✓ Hash table saved successfully.")
    except Exception as e:
        print(f"✗ Error saving hash table: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        print("WARNING: Changes were not saved! Hash table may be corrupted.")
        return 1

    return 0


def cmd_view(args):
    """View category totals."""
    print("Viewing category totals...")

    # Initialize crypto with error handling
    try:
        cipher_suite, SALT = initialize_crypto()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 130
    except Exception as e:
        print(f"Error initializing crypto: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    # Load hash table with error handling
    try:
        hash_table = load_hash_table(cipher_suite)
    except FileNotFoundError:
        print("✗ Error: No hash table found. Process a CSV file first.")
        return 1
    except Exception as e:
        print(f"✗ Error loading hash table: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    # Display data with error handling
    try:
        if args.all:
            print_hash_table(hash_table)
        else:
            categories = get_categories_and_totals(hash_table)
    except Exception as e:
        print(f"✗ Error displaying data: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    return 0


def cmd_config(args):
    """View or edit configuration."""
    try:
        config = Config.load()
    except Exception as e:
        print(f"✗ Error loading configuration: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    try:
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
    except Exception as e:
        print(f"✗ Error displaying configuration: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


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
    process_parser.add_argument(
        '--no-review',
        action='store_true',
        help='Skip transaction review (save immediately)'
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
