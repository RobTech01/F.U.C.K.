import json


path_to_your_hash_table = './storage/hash_table.enc'
HASH_TABLE_FILE : str = path_to_your_hash_table


def initialize_hash_table() -> dict:
    """Initializes the hash table with necessary structure."""
    return {"transaction_ids": [], "categories": {}, "addresses": {}}


def save_hash_table(hash_table : dict, cipher_suite) -> None:
    """
    Encrypts and saves the hash table to a file. This function converts the hash table
    dictionary into a JSON string, encrypts it using the Fernet cipher suite, and writes
    the encrypted data to the specified file.
    
    Args:
        hash_table (dict): The hash table to be saved, containing hashed addresses, 
                           their categories, and encrypted forms.
    """
    encrypted_data = cipher_suite.encrypt(json.dumps(hash_table).encode())

    with open(HASH_TABLE_FILE, 'wb') as file:
        file.write(encrypted_data)


def load_hash_table(cipher_suite) -> dict:
    """
    Loads and decrypts the hash table from a file. This function reads the encrypted data from
    the specified file, decrypts it using the Fernet cipher suite, and converts the JSON string
    back into a dictionary.
    
    Returns:
        dict: The decrypted hash table. If the file does not exist, returns an initialized dictionary.
    """
    try:
        with open(HASH_TABLE_FILE, 'rb') as file:
            encrypted_data = file.read()
        print("Loading saved data..")
        decrypted_data = cipher_suite.decrypt(encrypted_data)
        return json.loads(decrypted_data.decode())
    except FileNotFoundError:
        return initialize_hash_table()  # Init an empty hash table if file does not exist


def print_hash_table(hash_table: dict) -> None:
    """
    Prints the contents of the hash table in a structured format.

    Args:
        hash_table (dict): The hash table to be printed, containing
                           'transaction_ids', 'categories', and 'addresses'.
    """
    print("\nHash Table Contents:")

    print("\nTransaction IDs:")
    for transaction_id in hash_table['transaction_ids']:
        print(f"- {transaction_id}")

    print("\nCategories and Totals:")
    for category, total in hash_table['categories'].items():
        print(f"- {category}: {total}")

    print("\nAddresses and Categories:")
    for address, category in hash_table['addresses'].items():
        print(f"- {address}: {category}")

    print()

def get_categories_and_totals(hash_table: dict) -> dict:
    print(hash_table["categories"])
    return hash_table["categories"]


def filter_categories(
    hash_table: dict,
    category_filter: str = None,
    min_amount: float = None,
    max_amount: float = None
) -> dict:
    """
    Filter categories based on criteria.

    Args:
        hash_table: Hash table containing categories
        category_filter: Category name substring (case-insensitive)
        min_amount: Minimum category total
        max_amount: Maximum category total

    Returns:
        Filtered dictionary of categories and their totals
    """
    categories = hash_table.get('categories', {})
    filtered = {}

    for category, total in categories.items():
        # Filter by category name
        if category_filter and category_filter.lower() not in category.lower():
            continue

        # Filter by minimum amount
        if min_amount is not None and total < min_amount:
            continue

        # Filter by maximum amount
        if max_amount is not None and total > max_amount:
            continue

        filtered[category] = total

    return filtered


def test_secure_storage():
    """
    Tests the functionality of secure storage by mocking a hash table, saving it,
    and then loading it back. This function demonstrates the encryption and decryption
    process, along with the integrity of the data through the save and load operations.
    """
    dummy_hash_table = {
        'test_hash_1': {'category': 'Utilities', 'address': 'encrypted_address_1'},
        'test_hash_2': {'Prints messages to the console indicating the categorization status of the address.': 'Groceries', 'address': 'encrypted_address_2'}
    }
    
    print("Testing Secure Storage:")
    
    print("Saving hash table...")
    save_hash_table(dummy_hash_table)
    
    print("Loading hash table...")
    loaded_hash_table = load_hash_table()
    
    print("Loaded Hash Table:")
    print(loaded_hash_table)