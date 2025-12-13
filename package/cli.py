"""
CLI (Command Line Interface) module for F.U.C.K.
All user interaction code centralized here.
"""

from typing import List, Tuple, Dict, Optional
import getpass


def get_user_category(categories: List[str]) -> str:
    """
    Interactively prompts the user to categorize a new bank address.
    The user can select from a list of categories or enter a new category.

    Args:
        categories: List of predefined categories

    Returns:
        str: The chosen or entered category for the bank address.
    """
    print("\nPlease categorize the new bank address:")

    for i, category in enumerate(categories, 1):
        print(f"{i}. {category}")
    print("Select a number OR enter a New Category.")

    user_input = input("> ").strip()
    if user_input.isdigit() and 1 <= int(user_input) <= len(categories):
        return categories[int(user_input) - 1]
    elif user_input:
        return user_input  # Return custom category name
    else:
        print("Invalid input.")
        return get_user_category(categories)  # Recursively prompt until valid input


def _get_column_input(prompt: str, max_value: int, optional: bool = False) -> int:
    """
    Helper to get validated column input from user.

    Args:
        prompt: Prompt to display
        max_value: Maximum valid column number (1-indexed)
        optional: Whether this column is optional

    Returns:
        Column index (0-indexed), or -1 if optional and skipped
    """
    while True:
        try:
            user_input = input(prompt).strip()

            # Handle optional fields
            if optional and not user_input:
                return -1

            # Parse input
            col_num = int(user_input)

            # Validate range
            if col_num < 1 or col_num > max_value:
                print(f"Error: Please enter a number between 1 and {max_value}")
                continue

            return col_num - 1  # Convert to 0-indexed

        except ValueError:
            if optional:
                print(f"Error: Please enter a number between 1 and {max_value}, or press Enter to skip")
            else:
                print(f"Error: Please enter a valid number between 1 and {max_value}")
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            raise


def select_csv_columns(header: List[str]) -> Tuple[int, int, int, int, int, int]:
    """
    Prompts user to select which CSV columns contain which data.
    Validates all input to ensure column numbers are within range.

    Args:
        header: List of CSV column headers

    Returns:
        Tuple of (date_col, address_col, amount_col, name_col, type_col, description_col)

    Raises:
        KeyboardInterrupt: If user cancels the operation
    """
    if not header or len(header) < 3:
        raise ValueError(f"CSV header must have at least 3 columns, got {len(header)}")

    print("\nPlease select the column number for the following data:")
    for index, col_name in enumerate(header):
        print(f"{index + 1}. {col_name}")

    max_col = len(header)

    # Get required columns with validation
    date_col = _get_column_input("\nDate column: ", max_col, optional=False)
    address_col = _get_column_input("Address column: ", max_col, optional=False)
    amount_col = _get_column_input("Amount column: ", max_col, optional=False)

    # Get optional columns with validation
    name_col = _get_column_input("Name column (Enter to skip): ", max_col, optional=True)
    type_col = _get_column_input("Transaction type/text column (Enter to skip): ", max_col, optional=True)
    description_col = _get_column_input("Description column (Enter to skip): ", max_col, optional=True)

    # Validate that required columns are unique
    required_cols = [date_col, address_col, amount_col]
    if len(required_cols) != len(set(required_cols)):
        print("Error: Date, Address, and Amount columns must be different!")
        print("Please try again.\n")
        return select_csv_columns(header)

    return date_col, address_col, amount_col, name_col, type_col, description_col


def confirm_action(prompt: str) -> bool:
    """
    Prompts the user with a yes/no question and returns the user's decision.

    Args:
        prompt: The prompt to display to the user.

    Returns:
        bool: True if the user confirms (yes), False otherwise (no).
    """
    response = input(f"{prompt} (y/n): ").strip().lower()
    return response == 'y'


def secure_input(prompt: str) -> Optional[str]:
    """
    Securely inputs data from the user, hiding it from the terminal.
    Note: getpass doesn't visually hide the input in some IDEs or Jupyter notebooks.

    Args:
        prompt: The prompt to display to the user

    Returns:
        The user's input, or None if there was an error
    """
    try:
        return getpass.getpass(prompt)
    except Exception as e:
        print(f"Error obtaining secure input: {e}")
        return None


def prompt_for_salt() -> bytes:
    """
    Prompts user for the global salt, or generates a new one.
    Validates that the input is a valid hex string.

    Returns:
        Salt as bytes
    """
    import os

    while True:
        salt_input = secure_input("Please paste the global salt here (Enter to skip): ")

        # Generate new salt if user skips
        if not salt_input:
            salt = os.urandom(16)
            print(f"\nGenerated new salt. Save this command:")
            print(f"export FUCK_GLOBAL_SALT={salt.hex()}")
            return salt

        # Validate hex string
        try:
            salt_bytes = bytes.fromhex(salt_input.strip())
            if len(salt_bytes) != 16:
                print(f"Error: Salt must be exactly 16 bytes (32 hex characters), got {len(salt_bytes)} bytes")
                continue
            return salt_bytes
        except ValueError:
            print("Error: Invalid hex string. Salt must be a 32-character hexadecimal string.")
            print("Example: 0123456789abcdef0123456789abcdef")


def prompt_for_encryption_key():
    """
    Prompts user for the encryption key, or generates a new one.
    Validates that the input is a valid Fernet key.

    Returns:
        Encryption key as bytes
    """
    from cryptography.fernet import Fernet

    while True:
        key_input = secure_input("Please paste the encryption key here (Enter to skip): ")

        # Generate new key if user skips
        if not key_input:
            key = Fernet.generate_key()
            print(f"\nGenerated new encryption key. Save this command:")
            print(f"export FUCK_ENCRYPTION_KEY={key.decode()}")
            return key

        # Validate Fernet key format
        try:
            key_bytes = key_input.encode() if isinstance(key_input, str) else key_input
            # Try to create a Fernet instance to validate the key
            Fernet(key_bytes)
            return key_bytes
        except Exception as e:
            print(f"Error: Invalid encryption key format: {e}")
            print("The key must be a valid Fernet key (44 characters, base64-encoded)")
            if confirm_action("Generate a new key instead?"):
                key = Fernet.generate_key()
                print(f"\nGenerated new encryption key. Save this command:")
                print(f"export FUCK_ENCRYPTION_KEY={key.decode()}")
                return key


def print_transaction_info(transaction: Dict, category: str, new_total: float) -> None:
    """
    Prints information about a categorized transaction.

    Args:
        transaction: Transaction dictionary
        category: The category assigned
        new_total: New total for this category
    """
    print(f"Transaction categorized under '{category}' with amount {transaction['amount']}. "
          f"New total for '{category}': {new_total}")


def print_duplicate_warning(transaction_id: str) -> bool:
    """
    Prints a duplicate transaction warning and asks user what to do.

    Args:
        transaction_id: The ID of the duplicate transaction

    Returns:
        True if user wants to add anyway, False otherwise
    """
    print(f"Potential duplicate transaction detected with ID: {transaction_id}")
    return confirm_action("Do you want to add this transaction anyway?")


def print_new_address_prompt(transaction: Dict) -> None:
    """
    Prints information about a new address detected.

    Args:
        transaction: Transaction dictionary with address, name, type, description, amount
    """
    print(f"New address detected: {transaction.get('name', '')} "
          f"{transaction.get('type', '')} {transaction.get('description', '')} "
          f"{transaction['amount']}")


def print_progress(current: int, total: int, description: str = "Processing") -> None:
    """
    Prints progress information.

    Args:
        current: Current item number
        total: Total items
        description: What is being processed
    """
    percentage = (current / total * 100) if total > 0 else 0
    print(f"{description}: {current}/{total} ({percentage:.1f}%)")


def print_summary(transactions_processed: int, new_transactions: int, duplicates_skipped: int) -> None:
    """
    Prints a summary of CSV processing.

    Args:
        transactions_processed: Total transactions in CSV
        new_transactions: New transactions added
        duplicates_skipped: Duplicates that were skipped
    """
    print("\n" + "="*50)
    print("PROCESSING SUMMARY")
    print("="*50)
    print(f"Total transactions in CSV: {transactions_processed}")
    print(f"New transactions added:    {new_transactions}")
    print(f"Duplicates skipped:        {duplicates_skipped}")
    print("="*50)
