
# Fund Utilization and Categorization Kit

## Overview

The Fund Utilization and Categorization Kit (F.U.C.K.) is a locally run financial tracker for personal finance management. It processes downloadable .csv formatted bank statements from online banking platforms, categorizing transactions and remembering specific addresses for future reference. The main goal is to not having to do it manually in a spreadsheet.
## Features

- **Local Database**: Utilizes a hashed and encrypted local database to match known addresses to their respective categories
- **Transaction Categorization**: Automatically categorizes transactions from CSV bank statements based on previously encountered addresses
- **Interactive Review**: Preview all transactions before saving with option to cancel
- **Search and Edit**: Fix categorization mistakes with search functionality
- **Bulk Operations**: Recategorize multiple addresses at once with pattern matching
- **Filtering**: View categories by name or amount range
- **Reports and Insights**: Generate spending breakdowns with percentages and ASCII charts
- **Statistics**: Calculate mean, median, highest, and lowest spending categories
- **Spending Patterns**: Analyze merchant spending patterns, detect recurring transactions, and track investment vs. consumption habits
- **Interactive Help**: Comprehensive help system with topics for setup, categories, CSV formats, security, and patterns
- **Setup Wizard**: Guided first-time setup for new users
- **Strong Encryption**: All sensitive data encrypted with Fernet (AES-128)

## Quick Start

New to F.U.C.K.? Run the setup wizard:
```bash
python3 main.py init
```

Or jump straight to processing your first CSV:
```bash
python3 main.py process your-statement.csv
```

For help on any topic:
```bash
python3 main.py help setup
```

## Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/yourgithubusername/FUCK.git
cd FUCK
pip install -r requirements.txt
```

## Requirements

Ensure you have Python 3.6+ installed on your system. Dependencies are listed in the `requirements.txt` file.

## Usage

F.U.C.K. provides a comprehensive CLI for managing your finances:

### Getting Started

For new users, start with the interactive setup wizard:
```bash
python3 main.py init
```

Or get help on any topic:
```bash
python3 main.py help           # Show all help topics
python3 main.py help setup     # First-time setup guide
python3 main.py help categories    # Category management
python3 main.py help csv-format    # CSV format requirements
python3 main.py help security      # Security and encryption
```

### Processing Transactions

Import and categorize transactions from your bank's CSV export:
```bash
python3 main.py process statement.csv
```

The process command will:
- Ask you to select which CSV columns contain the date, address, and amount
- Show a preview of all transactions
- Ask you to categorize new addresses
- Let you review before saving

Skip the review step with `--no-review`:
```bash
python3 main.py process statement.csv --no-review
```

### Viewing Data

View all category totals:
```bash
python3 main.py view
```

Filter by category name:
```bash
python3 main.py view --category "Groceries"
```

Filter by amount range:
```bash
python3 main.py view --min-amount 100 --max-amount 500
```

Combine filters:
```bash
python3 main.py view --category "Dining" --min-amount 50
```

### Fixing Mistakes

Edit a single address categorization:
```bash
python3 main.py edit --search "walmart"
```

The edit command will:
- Search for addresses matching "walmart"
- Let you select the address to edit
- Show current category
- Let you choose a new category

### Bulk Operations

Recategorize multiple addresses at once:
```bash
python3 main.py bulk-edit --pattern "amazon" --category "Shopping"
```

Preview changes before confirming:
```bash
python3 main.py bulk-edit --pattern "store" --category "Retail"
```

Skip confirmation prompt:
```bash
python3 main.py bulk-edit --pattern "walmart" --category "Groceries/Food" --yes
```

### Reports and Insights

Generate a spending breakdown report:
```bash
python3 main.py report
```

The report shows:
- Total spending
- Category breakdown with percentages
- ASCII bar charts for visualization
- Sorted by amount (highest first)

Disable bar charts:
```bash
python3 main.py report --no-bars
```

Show additional statistics:
```bash
python3 main.py report --stats
```

Statistics include:
- Average per category
- Median spending
- Highest and lowest categories

### Spending Patterns Analysis

Analyze your spending habits and detect recurring patterns:
```bash
python3 main.py report --patterns
```

The patterns analysis shows:
- **Top Merchants by Spending**: Your top 10 merchants ranked by total spending
- **Regularity Breakdown**: How often you shop at each merchant (Weekly, Monthly, Yearly, Irregular)
- **Investment vs. Consumption**: Percentage of spending going to investments vs. regular expenses

Pattern types:
- **Weekly**: Purchases every 5-10 days (e.g., grocery stores)
- **Monthly**: Purchases every 20-40 days (e.g., subscriptions, bills)
- **Yearly**: Purchases every 330-400 days (e.g., annual fees)
- **Irregular**: Purchases at varying intervals
- **Single**: One-time purchases

Combine with other report flags:
```bash
python3 main.py report --patterns --stats
```

**Note**: Pattern detection requires transaction history, which is only available for newly processed transactions. Process multiple CSV files to build up your transaction history.

Get help on patterns:
```bash
python3 main.py help patterns
```

## Configuration

For security reasons, you can set up environment variables for the encryption key and salt for hashing:

- **Linux/Unix**: `export FUCK_GLOBAL_SALT=your_salt_here` and `export FUCK_ENCRYPTION_KEY=your_encryption_key_here`
- **Windows**: `set FUCK_GLOBAL_SALT=your_salt_here` and `set FUCK_ENCRYPTION_KEY=your_encryption_key_here`

Or save the respective strings in your Password Manager.

## Contribution

Feel free to reach out through GitHub.

## License

This project is licensed under the GNU General Public License v3.0. A copy of the license can be found in the LICENSE file within the project repository.
