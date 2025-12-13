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
from package.storage import print_hash_table, get_categories_and_totals, filter_categories
from package.category_manager import search_addresses, recategorize_address, get_all_addresses_with_categories, bulk_recategorize
from package import reports
from package import export as export_module


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
        strict_mode = args.strict if hasattr(args, 'strict') else False
        stats = process_csv_file(args.csv_file, hash_table, cipher_suite, SALT, review=enable_review, strict=strict_mode)
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

    # Check if any filters are applied
    has_filters = args.category or args.min_amount is not None or args.max_amount is not None

    # Display data with error handling
    try:
        if args.all:
            # Full hash table display (doesn't support filters)
            if has_filters:
                print("Warning: --all mode doesn't support filters. Showing all data.")
            print_hash_table(hash_table)
        elif has_filters:
            # Apply filters and display
            filtered_categories = filter_categories(
                hash_table,
                category_filter=args.category,
                min_amount=args.min_amount,
                max_amount=args.max_amount
            )

            filters_info = {
                'category': args.category,
                'min_amount': args.min_amount,
                'max_amount': args.max_amount
            }

            cli.display_filtered_categories(filtered_categories, filters_info)
        else:
            # No filters, show all categories
            categories = get_categories_and_totals(hash_table)
            # Display using the same function but without filter info
            cli.display_filtered_categories(categories)
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


def cmd_edit(args):
    """Edit/recategorize an existing address."""
    print("Edit Mode: Recategorize an address")

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
    except FileNotFoundError:
        print("✗ Error: No hash table found. Process a CSV file first.")
        return 1
    except Exception as e:
        print(f"✗ Error loading hash table: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    # Load config for categories
    try:
        config = Config.load()
        available_categories = config.default_categories
    except Exception as e:
        print(f"Warning: Could not load config: {e}")
        available_categories = []

    try:
        # If search term provided, use it; otherwise prompt
        if args.search:
            search_term = args.search
        else:
            search_term = input("\nEnter search term (address substring): ").strip()
            if not search_term:
                print("Search term required")
                return 1

        # Search for addresses
        print(f"\nSearching for addresses matching '{search_term}'...")
        results = search_addresses(hash_table, cipher_suite, search_term)

        if not results:
            print(f"\n✗ No addresses found matching '{search_term}'")
            return 1

        # Display results
        cli.display_address_search_results(results)

        # Let user select which address
        selected = cli.select_address_from_results(results)
        if not selected:
            print("\nEdit cancelled")
            return 0

        address, current_category, encrypted_hash = selected

        # Prompt for new category
        new_category = cli.prompt_for_new_category(current_category, available_categories)
        if not new_category:
            print("\nEdit cancelled")
            return 0

        # Perform recategorization
        success, message = recategorize_address(encrypted_hash, new_category, hash_table, cipher_suite)

        if success:
            # Save updated hash table
            try:
                save_hash_table(hash_table, cipher_suite)
                print(f"\n✓ {message}")
                print("✓ Changes saved successfully")
                print("\nNote: Category totals will be updated when you next process this address")
                return 0
            except Exception as e:
                print(f"✗ Error saving changes: {e}")
                return 1
        else:
            print(f"\n✗ {message}")
            return 1

    except KeyboardInterrupt:
        print("\n\nEdit cancelled by user")
        return 130
    except Exception as e:
        print(f"✗ Error during edit: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_bulk_edit(args):
    """Bulk recategorize addresses matching a pattern."""
    print("Bulk Edit Mode: Recategorize multiple addresses")

    # Validate arguments
    if not args.pattern:
        print("✗ Error: --pattern is required")
        return 1

    if not args.category:
        print("✗ Error: --category is required")
        return 1

    # Initialize crypto
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

    # Load hash table
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

    try:
        # Preview mode (dry run)
        print(f"\nSearching for addresses matching '{args.pattern}'...")
        count, affected = bulk_recategorize(
            args.pattern,
            args.category,
            hash_table,
            cipher_suite,
            dry_run=True
        )

        if count == 0:
            print(f"\n✗ No addresses found matching pattern '{args.pattern}'")
            print("(or all matching addresses already have the target category)")
            return 1

        # Show preview
        cli.preview_bulk_changes(affected, args.category)

        # Confirm unless --yes flag
        if not args.yes:
            if not cli.confirm_action("\nApply these changes?"):
                print("\nBulk edit cancelled")
                return 0

        # Actually apply changes
        print("\nApplying changes...")
        count, affected = bulk_recategorize(
            args.pattern,
            args.category,
            hash_table,
            cipher_suite,
            dry_run=False
        )

        # Save changes
        save_hash_table(hash_table, cipher_suite)

        print(f"\n✓ Successfully recategorized {count} address{'es' if count != 1 else ''}")
        print("✓ Changes saved successfully")
        print("\nNote: Category totals will be updated when you next process these addresses")

        return 0

    except KeyboardInterrupt:
        print("\n\nBulk edit cancelled by user")
        return 130
    except Exception as e:
        print(f"✗ Error during bulk edit: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_report(args):
    """Generate spending insights and reports."""
    print("Generating spending report...")

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
    except FileNotFoundError:
        print("✗ Error: No hash table found. Process a CSV file first.")
        return 1
    except Exception as e:
        print(f"✗ Error loading hash table: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    try:
        categories = hash_table.get('categories', {})

        if not categories:
            print("\nNo category data available for reporting.")
            print("Process some transactions first with: python3 main.py process <csv_file>")
            return 1

        # Generate category breakdown report
        report_data = reports.generate_category_breakdown(categories)

        # Format and display
        report_output = reports.format_category_report(report_data, show_bars=not args.no_bars)
        print(report_output)

        # Show statistics if requested
        if args.stats:
            stats = reports.calculate_category_statistics(categories)
            print("\n" + "="*80)
            print("STATISTICS")
            print("="*80)
            print(f"Average per category: ${stats['mean']:.2f}")
            print(f"Median: ${stats['median']:.2f}")
            if stats['highest']:
                print(f"Highest: {stats['highest'][0]} (${stats['highest'][1]:.2f})")
            if stats['lowest']:
                print(f"Lowest: {stats['lowest'][0]} (${stats['lowest'][1]:.2f})")
            print("="*80)

        return 0

    except Exception as e:
        print(f"✗ Error generating report: {e}")
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


def cmd_help(args):
    """Display help for a specific topic."""
    from package import help as help_module

    try:
        help_content = help_module.get_help_topic(args.topic)
        print(help_content)
        return 0
    except Exception as e:
        print(f"✗ Error displaying help: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_init(args):
    """Run the interactive setup wizard."""
    try:
        cli.run_setup_wizard()
        return 0
    except KeyboardInterrupt:
        print("\n\nSetup wizard cancelled by user")
        return 130
    except Exception as e:
        print(f"✗ Error running setup wizard: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_export(args):
    """Export category data to file in specified format."""
    print(f"Exporting data to {args.format.upper()} format...")

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
    except FileNotFoundError:
        print("✗ Error: No hash table found. Process a CSV file first.")
        return 1
    except Exception as e:
        print(f"✗ Error loading hash table: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    try:
        categories = hash_table.get('categories', {})

        if not categories:
            print("\nNo category data available for export.")
            print("Process some transactions first with: python3 main.py process <csv_file>")
            return 1

        # Apply filters if specified (reuse filtering from Session 3)
        if args.category or args.min_amount is not None or args.max_amount is not None:
            print("Applying filters...")
            categories = filter_categories(
                hash_table,
                category_filter=args.category,
                min_amount=args.min_amount,
                max_amount=args.max_amount
            )

            if not categories:
                print("✗ No categories match the specified filters.")
                return 1

            filters_applied = []
            if args.category:
                filters_applied.append(f"category='{args.category}'")
            if args.min_amount is not None:
                filters_applied.append(f"min=${args.min_amount:.2f}")
            if args.max_amount is not None:
                filters_applied.append(f"max=${args.max_amount:.2f}")
            print(f"  Filters: {', '.join(filters_applied)}")
            print(f"  Matching categories: {len(categories)}")

        # Export data
        output_file = export_module.export_categories(
            categories,
            format_type=args.format,
            output_file=args.output
        )

        print(f"✓ Successfully exported {len(categories)} categor{'y' if len(categories) == 1 else 'ies'}")
        print(f"✓ Output file: {output_file}")

        return 0

    except ValueError as e:
        print(f"✗ Export error: {e}")
        return 1
    except Exception as e:
        print(f"✗ Error during export: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


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
    process_parser.add_argument(
        '--strict',
        action='store_true',
        help='Fail on first validation error instead of skipping invalid transactions'
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
    view_parser.add_argument(
        '--category',
        type=str,
        help='Filter by category (case-insensitive substring match)'
    )
    view_parser.add_argument(
        '--min-amount',
        type=float,
        help='Filter by minimum transaction amount'
    )
    view_parser.add_argument(
        '--max-amount',
        type=float,
        help='Filter by maximum transaction amount'
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

    # Edit command
    edit_parser = subparsers.add_parser(
        'edit',
        help='Edit/recategorize an existing address'
    )
    edit_parser.add_argument(
        '--search',
        type=str,
        help='Search term to find addresses (optional, will prompt if not provided)'
    )
    edit_parser.set_defaults(func=cmd_edit)

    # Report command
    report_parser = subparsers.add_parser(
        'report',
        help='Generate spending insights and reports'
    )
    report_parser.add_argument(
        '--no-bars',
        action='store_true',
        help='Disable ASCII bar charts'
    )
    report_parser.add_argument(
        '--stats',
        action='store_true',
        help='Show additional statistics'
    )
    report_parser.set_defaults(func=cmd_report)

    # Bulk Edit command
    bulk_edit_parser = subparsers.add_parser(
        'bulk-edit',
        help='Bulk recategorize addresses matching a pattern'
    )
    bulk_edit_parser.add_argument(
        '--pattern',
        type=str,
        required=True,
        help='Search pattern to match addresses (case-insensitive substring)'
    )
    bulk_edit_parser.add_argument(
        '--category',
        type=str,
        required=True,
        help='New category to assign to matching addresses'
    )
    bulk_edit_parser.add_argument(
        '--yes',
        action='store_true',
        help='Skip confirmation prompt (auto-confirm)'
    )
    bulk_edit_parser.set_defaults(func=cmd_bulk_edit)

    # Version command
    version_parser = subparsers.add_parser(
        'version',
        help='Show version information'
    )
    version_parser.set_defaults(func=cmd_version)

    # Help command
    help_parser = subparsers.add_parser(
        'help',
        help='Display help for a specific topic'
    )
    help_parser.add_argument(
        'topic',
        nargs='?',
        type=str,
        help='Help topic (setup, categories, csv-format, security)'
    )
    help_parser.set_defaults(func=cmd_help)

    # Init command
    init_parser = subparsers.add_parser(
        'init',
        help='Run interactive setup wizard for new users'
    )
    init_parser.set_defaults(func=cmd_init)

    # Export command
    export_parser = subparsers.add_parser(
        'export',
        help='Export category data to file'
    )
    export_parser.add_argument(
        '--format',
        type=str,
        choices=['csv', 'json', 'txt'],
        default='csv',
        help='Export format (default: csv)'
    )
    export_parser.add_argument(
        '--output',
        type=str,
        help='Output filename (default: auto-generated with timestamp)'
    )
    export_parser.add_argument(
        '--category',
        type=str,
        help='Filter by category (case-insensitive substring match)'
    )
    export_parser.add_argument(
        '--min-amount',
        type=float,
        help='Filter by minimum amount'
    )
    export_parser.add_argument(
        '--max-amount',
        type=float,
        help='Filter by maximum amount'
    )
    export_parser.set_defaults(func=cmd_export)

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
