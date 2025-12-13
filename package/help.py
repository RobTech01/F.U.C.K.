"""
Help and onboarding module for F.U.C.K.
Provides interactive help topics and setup wizard.
"""

from typing import Optional


# Help topics content
HELP_TOPICS = {
    "setup": """
================================================================================
FIRST-TIME SETUP GUIDE
================================================================================

Welcome to F.U.C.K. (Fund Utilization and Categorization Kit)!

Getting started is easy:

1. PREPARE YOUR DATA
   - Export your bank transactions as CSV
   - Common formats supported: Chase, Bank of America, Wells Fargo, etc.
   - Required columns: Date, Address/Description, Amount
   - Optional columns: Name, Type, Description

2. SECURITY SETUP
   - F.U.C.K. uses encryption to protect your financial data
   - You'll need to set two environment variables:

     export FUCK_GLOBAL_SALT=<32-character hex string>
     export FUCK_ENCRYPTION_KEY=<44-character Fernet key>

   - If not set, F.U.C.K. will generate these for you on first run
   - IMPORTANT: Save these values! You'll need them to access your data

3. PROCESS YOUR FIRST CSV
   Run: python3 main.py process your-transactions.csv

   - Select which columns contain Date, Address, Amount
   - Categorize new addresses as they appear
   - Review transactions before saving
   - Confirm to save or cancel to retry

4. VIEW YOUR DATA
   Run: python3 main.py view

   - See category totals
   - Use filters to find specific categories
   - Generate reports for insights

5. NEXT STEPS
   - Learn about categories: python3 main.py help categories
   - Understand CSV format: python3 main.py help csv-format
   - Review security: python3 main.py help security

TIP: Use 'python3 main.py init' to run the interactive setup wizard!

================================================================================
""",

    "categories": """
================================================================================
CATEGORY MANAGEMENT GUIDE
================================================================================

Categories help you organize your spending and track where your money goes.

BUILT-IN CATEGORIES:
F.U.C.K. suggests these common categories:
  • Groceries/Food
  • Utilities/Bills
  • Entertainment
  • Transportation
  • Healthcare
  • Shopping
  • Rent/Mortgage
  • Dining Out
  • Subscriptions
  • Income
  • Savings/Investments
  • Other

CREATING CUSTOM CATEGORIES:
When processing transactions, you can:
  1. Select from existing categories (enter the number)
  2. Type a new category name (any text)

Categories are case-sensitive and can contain spaces.

MANAGING CATEGORIES:

View all categories:
  python3 main.py view

View specific category:
  python3 main.py view --category "Groceries"

Edit a category assignment:
  python3 main.py edit --search "walmart"

Bulk recategorize:
  python3 main.py bulk-edit --pattern "amazon" --category "Shopping"

TIPS:
  • Use consistent naming (e.g., always "Groceries/Food", not "Groceries")
  • Group related expenses (e.g., "Utilities/Bills" for all utility companies)
  • Be specific enough to be useful but broad enough to avoid too many categories
  • Review your categories periodically with 'view' command

================================================================================
""",

    "csv-format": """
================================================================================
CSV FORMAT GUIDE
================================================================================

F.U.C.K. can process CSV files from most banks. Here's what you need to know:

REQUIRED COLUMNS:
  1. Date - Transaction date (various formats supported)
  2. Address/Description - Merchant or transaction description
  3. Amount - Transaction amount (positive or negative)

OPTIONAL COLUMNS:
  4. Name - Account holder name
  5. Type - Transaction type (debit, credit, etc.)
  6. Description - Additional details

SUPPORTED DATE FORMATS:
  • YYYY-MM-DD (2024-01-15)
  • MM/DD/YYYY (01/15/2024)
  • DD/MM/YYYY (15/01/2024)
  • Month DD, YYYY (January 15, 2024)

COMMON BANK FORMATS:

Chase:
  Transaction Date, Post Date, Description, Category, Type, Amount, Memo

Bank of America:
  Date, Description, Amount, Running Bal.

Wells Fargo:
  Date, Amount, *, *, Description

Capital One:
  Transaction Date, Posted Date, Card No., Description, Category, Debit, Credit

TIPS:
  • Remove header rows that aren't column names
  • Ensure amounts are numeric (remove $ symbols if present)
  • Check date format is consistent
  • CSV should be UTF-8 encoded

EXAMPLE CSV:
  Date,Description,Amount
  2024-01-15,Walmart Store #123,-87.45
  2024-01-16,Direct Deposit - Employer,2500.00
  2024-01-17,Electric Company,-125.30

To test your CSV format:
  python3 main.py process --no-review your-file.csv

This will process without saving, letting you verify the format is correct.

================================================================================
""",

    "security": """
================================================================================
SECURITY GUIDE
================================================================================

F.U.C.K. takes your financial privacy seriously. Here's how your data is protected:

ENCRYPTION:
  • All bank addresses are hashed with SHA-256
  • Hashes are encrypted with Fernet (AES-128)
  • Transaction IDs use HMAC-SHA256 for secure deduplication
  • Category totals are stored in plain text (no sensitive info)

KEYS AND SALT:
You need two secrets:

1. GLOBAL SALT (FUCK_GLOBAL_SALT)
   - 16 bytes (32 hex characters)
   - Used for hashing addresses
   - Example: export FUCK_GLOBAL_SALT=0123456789abcdef0123456789abcdef

2. ENCRYPTION KEY (FUCK_ENCRYPTION_KEY)
   - 44-character Fernet key
   - Used for encrypting hashes
   - Example: export FUCK_ENCRYPTION_KEY=vQ2h7Kx9Lm3Pn5Rt8Wx0Yz2Bb4Dd6Ff8=

GENERATING NEW KEYS:
If you don't have keys, F.U.C.K. will generate them on first run:
  python3 main.py process your-file.csv

You'll see output like:
  Generated new salt. Save this command:
  export FUCK_GLOBAL_SALT=...

  Generated new encryption key. Save this command:
  export FUCK_ENCRYPTION_KEY=...

SAVE THESE IMMEDIATELY! Without them, you cannot access your data.

BEST PRACTICES:
  ✓ Store keys in a password manager
  ✓ Add to your .bashrc or .zshrc for permanent use
  ✓ Never commit keys to git repositories
  ✓ Use different keys for different datasets
  ✓ Back up your keys securely

STORAGE LOCATION:
  • Encrypted data stored in: ./storage/hash_table.enc
  • No plain-text financial data is ever written to disk
  • Data is encrypted before saving, decrypted on load

THREAT MODEL:
  • Protects against: Casual snooping, accidental exposure, stolen backups
  • Does NOT protect against: Keyloggers, compromised system, coerced decryption
  • Your keys are the only way to access your data - guard them carefully!

For maximum security:
  1. Use disk encryption (FileVault, BitLocker, LUKS)
  2. Run F.U.C.K. in an encrypted container
  3. Clear shell history after entering keys
  4. Use environment variables, not command-line arguments

================================================================================
""",
}


def get_help_topic(topic: Optional[str] = None) -> str:
    """
    Get help content for a specific topic or show available topics.

    Args:
        topic: The help topic to display, or None for topic list

    Returns:
        Help content string
    """
    if topic is None:
        return get_help_overview()

    topic_lower = topic.lower()

    if topic_lower in HELP_TOPICS:
        return HELP_TOPICS[topic_lower]
    else:
        return get_unknown_topic_message(topic)


def get_help_overview() -> str:
    """
    Get overview of available help topics.

    Returns:
        Help overview string
    """
    return """
================================================================================
F.U.C.K. HELP SYSTEM
================================================================================

Fund Utilization and Categorization Kit - Personal Finance Tracker

Available help topics:

  setup       - First-time setup guide and getting started
  categories  - How to manage and organize spending categories
  csv-format  - Understanding CSV file formats and requirements
  security    - Security features and encryption details

USAGE:
  python3 main.py help <topic>

  Example: python3 main.py help setup

QUICK START:
  1. Run the setup wizard: python3 main.py init
  2. Process your first CSV: python3 main.py process transactions.csv
  3. View your data: python3 main.py view

COMMON COMMANDS:
  process <file>     - Import and categorize transactions from CSV
  view               - Display category totals
  edit               - Fix categorization mistakes
  report             - Generate spending insights and reports
  bulk-edit          - Recategorize multiple addresses at once

For detailed help on any command:
  python3 main.py <command> --help

For interactive setup:
  python3 main.py init

================================================================================
"""


def get_unknown_topic_message(topic: str) -> str:
    """
    Get message for unknown help topic.

    Args:
        topic: The unknown topic requested

    Returns:
        Error message with available topics
    """
    available = ", ".join(HELP_TOPICS.keys())
    return f"""
================================================================================
UNKNOWN HELP TOPIC: {topic}
================================================================================

Available topics: {available}

Try:
  python3 main.py help setup       - For first-time setup
  python3 main.py help             - For all topics

================================================================================
"""


def get_welcome_message() -> str:
    """
    Get welcome message for setup wizard.

    Returns:
        Welcome message string
    """
    return """
================================================================================
F.U.C.K. INTERACTIVE SETUP WIZARD
================================================================================

Welcome to F.U.C.K. (Fund Utilization and Categorization Kit)!

This wizard will help you get started with tracking your finances.

We'll walk through:
  1. Understanding security requirements
  2. Setting up encryption keys
  3. Preparing your CSV file
  4. Choosing your category structure
  5. Processing your first transactions

This should take about 5-10 minutes.

Press Enter to continue or Ctrl+C to exit...
"""


def get_security_wizard_section() -> str:
    """
    Get security section of setup wizard.

    Returns:
        Security wizard content
    """
    return """
================================================================================
STEP 1: SECURITY SETUP
================================================================================

F.U.C.K. encrypts your financial data to protect your privacy.

You need two environment variables:
  1. FUCK_GLOBAL_SALT - For hashing bank addresses
  2. FUCK_ENCRYPTION_KEY - For encrypting the hash table

If you don't have these yet, F.U.C.K. will generate them automatically
when you process your first CSV file.

IMPORTANT: You must save these values! Without them, you cannot access
your data in future sessions.

Do you already have encryption keys set up? (y/n): """


def get_csv_wizard_section() -> str:
    """
    Get CSV preparation section of setup wizard.

    Returns:
        CSV wizard content
    """
    return """
================================================================================
STEP 2: CSV FILE PREPARATION
================================================================================

To use F.U.C.K., you need a CSV export from your bank.

Required columns:
  • Date - Transaction date
  • Description/Address - Merchant or transaction description
  • Amount - Transaction amount

Optional columns:
  • Name, Type, Description (provide additional context)

Most banks allow you to export transactions as CSV:
  • Chase: Activity → Download → CSV
  • Bank of America: Download Transactions → CSV
  • Wells Fargo: Download → CSV

Tips:
  ✓ Include 1-3 months of data for your first import
  ✓ Remove any summary rows (keep only transactions)
  ✓ Keep the header row with column names

Press Enter when you have your CSV file ready...
"""


def get_category_wizard_section() -> str:
    """
    Get category structure section of setup wizard.

    Returns:
        Category wizard content
    """
    return """
================================================================================
STEP 3: CATEGORY STRUCTURE
================================================================================

F.U.C.K. will ask you to categorize each new merchant/address.

Recommended category structure:

  EXPENSES:
    • Groceries/Food
    • Dining Out
    • Utilities/Bills
    • Rent/Mortgage
    • Transportation
    • Healthcare
    • Entertainment
    • Shopping
    • Subscriptions

  INCOME:
    • Salary/Wages
    • Freelance/Side Income
    • Investments

  OTHER:
    • Transfers
    • Savings
    • Uncategorized

You can:
  • Use our suggested categories
  • Create your own categories
  • Mix both approaches

Categories can be edited later with the 'edit' command.

Press Enter to continue...
"""


def get_completion_wizard_section() -> str:
    """
    Get completion section of setup wizard.

    Returns:
        Completion wizard content
    """
    return """
================================================================================
SETUP COMPLETE!
================================================================================

You're ready to start using F.U.C.K.

Next steps:

1. PROCESS YOUR FIRST CSV:
   python3 main.py process your-transactions.csv

2. VIEW YOUR DATA:
   python3 main.py view

3. GENERATE REPORTS:
   python3 main.py report --stats

4. EXPLORE FEATURES:
   - Edit categorization: python3 main.py edit --search "merchant"
   - Filter categories: python3 main.py view --category "Groceries"
   - Bulk operations: python3 main.py bulk-edit --pattern "store" --category "Shopping"

For detailed help:
  python3 main.py help <topic>

Available topics: setup, categories, csv-format, security

Happy budgeting! 💰

================================================================================
"""


# Suggested categories for new users
SUGGESTED_CATEGORIES = [
    "Groceries/Food",
    "Dining Out",
    "Utilities/Bills",
    "Rent/Mortgage",
    "Transportation",
    "Healthcare",
    "Entertainment",
    "Shopping",
    "Subscriptions",
    "Salary/Wages",
    "Transfers",
    "Savings",
    "Other"
]
