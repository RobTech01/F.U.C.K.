from .crypto import hash_address, encrypt_address, hash_transaction_id, decrypt_address
from . import cli


def generate_transaction_id(date : str, amount: float, hashed_address: str = "") -> str:
    """
    Generates a unique ID for a transaction using its date, amount, and address hash.

    Args:
        date (str): Transaction date.
        amount (float): Transaction amount.
        hashed_address (str): Hashed address for uniqueness (optional, first 8 chars used).

    Returns:
        str: A string representing the transaction ID.
    """
    address_prefix = hashed_address[:8] if hashed_address else ""
    transaction_str = f"{date}-{address_prefix}-{amount}"
    return transaction_str


def find_category_by_address(encrypted_hash : dict, target : str, cipher_suite) -> str:
    """
    Decrypts encrypted addresses to find the category for a given target address.

    Args:
        encrypted_string (dict): Encrypted addresses as keys and categories as values.
        target (str): The consistent text address to find the category for.

    Returns:
        str: The category for the target address, or None if not found.
    """
    for encrypted_key in encrypted_hash.keys():
        decrypted_key = decrypt_address(encrypted_key, cipher_suite)
        if decrypted_key == target:
            return encrypted_hash[encrypted_key]
    return None


def categorize_transaction(transaction : dict, hash_table : dict, cipher_suite, SALT, categories: list = None) -> None:
    """
    Modifies the hash_table in place to categorize the given address, adding the amount
    to the total for the category. If the address is new, prompts the user for the category.

    Args:
        transaction (dict): Transaction data with address, date, amount, etc.
        hash_table (dict): The hash table storing categories, addresses, and amounts.
        cipher_suite: Encryption cipher suite
        SALT: Salt for hashing
        categories (list): List of default categories (optional)
    """
    if categories is None:
        from .config import Config
        categories = Config().default_categories

    if not isinstance(hash_table, dict):
        raise TypeError("hash_table must be a dictionary.")

    if not isinstance(transaction, dict):
        raise TypeError("transaction must be a dictionary.")

    hashed_address = hash_address(transaction['address'], SALT)
    encrypted_hashed_address = encrypt_address(hash_address(transaction['address'], SALT), cipher_suite)
    transaction_id = generate_transaction_id(transaction['date'], transaction['amount'], hashed_address)
    hashed_transaction_id = hash_transaction_id(transaction_id, SALT)

    # Check for duplicate transactions
    if hashed_transaction_id not in hash_table['transaction_ids']:
        print(f"Adding new transaction with ID: {transaction_id}")
        hash_table['transaction_ids'].append(hashed_transaction_id)
    else:
        if not cli.print_duplicate_warning(transaction_id):
            print("Transaction addition cancelled.")
            return
        hash_table['transaction_ids'].append(hashed_transaction_id)

    # Handle the categorization based on the address
    category = find_category_by_address(hash_table['addresses'], hashed_address, cipher_suite)

    if not category:
        print(decrypt_address(encrypted_hashed_address, cipher_suite))
        cli.print_new_address_prompt(transaction)
        category = cli.get_user_category(categories)
        hash_table['addresses'][encrypted_hashed_address] = category

    hash_table['categories'].setdefault(category, 0)
    hash_table['categories'][category] += transaction['amount']

    cli.print_transaction_info(transaction, category, hash_table['categories'][category])
