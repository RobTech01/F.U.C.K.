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


def select_csv_columns(header: List[str]) -> Tuple[int, int, int, int, int, int]:
    """
    Prompts user to select which CSV columns contain which data.

    Args:
        header: List of CSV column headers

    Returns:
        Tuple of (date_col, address_col, amount_col, name_col, type_col, description_col)
    """
    print("\nPlease select the column number for the following data:")
    for index, col_name in enumerate(header):
        print(f"{index + 1}. {col_name}")

    date_col: int = int(input("\nDate column: ")) - 1
    name_col: int = int(input("Name column (Enter to skip): ") or -1) - 1
    address_col: int = int(input("Address column: ")) - 1
    type_col: int = int(input("Transaction type/text column (Enter to skip): ") or -1) - 1
    description_col: int = int(input("Description column (Enter to skip): ") or -1) - 1
    amount_col: int = int(input("Amount column: ")) - 1

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

    Returns:
        Salt as bytes
    """
    salt_input = secure_input("Please paste the global salt here (Enter to skip): ")
    if not salt_input:
        import os
        salt = os.urandom(16)
        print(f"\nSuggested command to set the environment variable:")
        print(f"export FUCK_GLOBAL_SALT={salt.hex()}")
        return salt
    # Convert hex string to bytes
    return bytes.fromhex(salt_input) if isinstance(salt_input, str) else salt_input


def prompt_for_encryption_key():
    """
    Prompts user for the encryption key, or generates a new one.

    Returns:
        Encryption key as bytes
    """
    from cryptography.fernet import Fernet

    key_input = secure_input("Please paste the encryption key here (Enter to skip): ")
    if not key_input:
        key = Fernet.generate_key()
        print(f"\nSuggested command to set the environment variable:")
        print(f"export FUCK_ENCRYPTION_KEY={key.decode()}")
        return key
    # Return as bytes
    return key_input.encode() if isinstance(key_input, str) else key_input


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
