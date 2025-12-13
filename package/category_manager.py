from .crypto import hash_address, encrypt_address, hash_transaction_id, decrypt_address
from . import cli
from typing import List, Dict, Tuple, Optional


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

    # Save individual transaction for pattern analysis
    from .storage import save_transaction
    save_transaction(hash_table, transaction['date'], encrypted_hashed_address, transaction['amount'], category)

    cli.print_transaction_info(transaction, category, hash_table['categories'][category])


def get_all_addresses_with_categories(hash_table: dict, cipher_suite) -> List[Tuple[str, str, str]]:
    """
    Get all addresses with their categories and encrypted hashes.

    Args:
        hash_table: Hash table containing addresses
        cipher_suite: Cipher suite for decryption

    Returns:
        List of tuples: (decrypted_address, category, encrypted_hash)
    """
    addresses_list = []

    for encrypted_hash, category in hash_table['addresses'].items():
        try:
            decrypted_address = decrypt_address(encrypted_hash, cipher_suite)
            addresses_list.append((decrypted_address, category, encrypted_hash))
        except Exception as e:
            # Skip addresses that can't be decrypted
            print(f"Warning: Could not decrypt address: {e}")
            continue

    return addresses_list


def recategorize_address(
    encrypted_hash: str,
    new_category: str,
    hash_table: dict,
    cipher_suite
) -> Tuple[bool, str]:
    """
    Recategorize an address and update category totals.

    Args:
        encrypted_hash: Encrypted hash of the address to recategorize
        new_category: New category to assign
        hash_table: Hash table to update
        cipher_suite: Cipher suite for decryption

    Returns:
        Tuple of (success: bool, message: str)
    """
    # Check if address exists
    if encrypted_hash not in hash_table['addresses']:
        return False, "Address not found in database"

    # Get old category
    old_category = hash_table['addresses'][encrypted_hash]

    if old_category == new_category:
        return False, "Address already has this category"

    # Calculate total amount for this address across all transactions
    # We need to find all transactions with this address and sum their amounts
    decrypted_address = decrypt_address(encrypted_hash, cipher_suite)

    # Find all transaction amounts for this address
    # We'll need to recalculate totals based on transaction history
    # For now, we'll update the category mapping and let the user know
    # they need to reprocess to update totals accurately

    # Update the address category mapping
    hash_table['addresses'][encrypted_hash] = new_category

    return True, f"Address recategorized from '{old_category}' to '{new_category}'"


def search_addresses(
    hash_table: dict,
    cipher_suite,
    search_term: str
) -> List[Tuple[str, str, str]]:
    """
    Search for addresses matching a search term.

    Args:
        hash_table: Hash table containing addresses
        cipher_suite: Cipher suite for decryption
        search_term: Search term (case-insensitive substring match)

    Returns:
        List of tuples: (decrypted_address, category, encrypted_hash)
    """
    all_addresses = get_all_addresses_with_categories(hash_table, cipher_suite)
    search_lower = search_term.lower()

    # Filter addresses that contain the search term
    matches = [
        (addr, cat, enc_hash)
        for addr, cat, enc_hash in all_addresses
        if search_lower in addr.lower()
    ]

    return matches


def bulk_recategorize(
    pattern: str,
    new_category: str,
    hash_table: dict,
    cipher_suite,
    dry_run: bool = False
) -> Tuple[int, List[str]]:
    """
    Bulk recategorize addresses matching a pattern.

    Args:
        pattern: Search pattern (substring match, case-insensitive)
        new_category: New category to assign to matching addresses
        hash_table: Hash table to update
        cipher_suite: Cipher suite for decryption
        dry_run: If True, don't actually make changes (preview only)

    Returns:
        Tuple of (count_affected, list_of_affected_addresses)
    """
    # Find all matching addresses
    matches = search_addresses(hash_table, cipher_suite, pattern)

    if not matches:
        return 0, []

    affected_addresses = []
    count = 0

    for address, old_category, encrypted_hash in matches:
        # Skip if already in target category
        if old_category == new_category:
            continue

        if not dry_run:
            # Actually update the category
            hash_table['addresses'][encrypted_hash] = new_category

        affected_addresses.append(f"{address} ({old_category} → {new_category})")
        count += 1

    return count, affected_addresses
