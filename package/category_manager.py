from package.crypto_utils import hash_address, encrypt_address, hash_transaction_id, decrypt_address


def get_user_category() -> str:
    """
    Interactively prompts the user to categorize a new bank address. 
    The user can select from a predefined list of categories or enter a new category.

    Returns:
  Returns       str: The chosen or entered category for the bank address.
    """

    print("\nPlease categorize the new bank address:")

    categories = [
        'Groceries/Food',
        'Utilities/Bills',
        'Rent/Mortgage',
        'Salary',
        'Savings',
        'Stable Investments',
        'High-Risk Investments',
        'Arbitrage/Resale Profits'
        'Retirement',
        'Entertainment/Leisure',
        'Health & Wellness',
        'Education',
        'Miscellaneous/Other'
    ]

    for i, category in enumerate(categories, 1):
        print(f"{i}. {category}")
    print("Select a number OR enter a New Category.")

    user_input = input("> ").strip()
    if user_input.isdigit() and 1 <= int(user_input) <= len(categories):
        return categories[int(user_input) - 1]
    elif user_input:
        return categories[user_input]
    else:
        print("Invalid input.")
        return get_user_category()  # Recursively prompt until valid input


def generate_transaction_id(date : str, amount: float) -> str:
    """
    Generates a ID for a transaction using its date, address, and amount.
    
    Args:
        transaction (dict): Transaction data.
    
    Returns:
        str: A string representing the transaction ID.
    """
    transaction_str = f"{date}-{amount}"
    return transaction_str


def user_confirm_action(prompt: str) -> bool:
    """
    Prompts the user with a yes/no question and returns the user's decision.
    
    Args:
        prompt (str): The prompt to display to the user.
    
    Returns:
        bool: True if the user confirms (yes), False otherwise (no).
    """
    response = input(f"{prompt} (y/n): ").strip().lower()
    return response == 'y'


def find_category_by_address(encrypted_hash : dict, target : str) -> str:
    """
    Decrypts encrypted addresses to find the category for a given target address.

    Args:
        encrypted_string (dict): Encrypted addresses as keys and categories as values.
        target (str): The consistent text address to find the category for.

    Returns:
        str: The category for the target address, or None if not found.
    """
    for encrypted_key in encrypted_hash.keys():
        decrypted_key = decrypt_address(encrypted_key)
        if decrypted_key == target:
            return encrypted_hash[encrypted_key]
    return None



def categorize_transaction(transaction : dict, hash_table : dict) -> None:
    """
    Modifies the hash_table in place to categorize the given address, adding the amount
    to the total for the category. If the address is new, prompts the user for the category.
    
    Args:
        address (str): The transaction address or description.
        amount (float): The transaction amount.
        hash_table (dict): The hash table storing categories, addresses, and amounts.
    """
    
    if not isinstance(hash_table, dict):
        raise TypeError("hash_table must be a dictionary.")
    
    if not isinstance(transaction, dict):
        raise TypeError("transaction must be a dictionary.")
    
    hashed_address = hash_address(transaction['address'])
    encrypted_hashed_address = encrypt_address(hash_address(transaction['address']))
    transaction_id = generate_transaction_id(transaction['date'], transaction['amount'])
    hashed_transaction_id = hash_transaction_id(transaction_id)

    # Check for duplicate transactions
    if hashed_transaction_id not in hash_table['transaction_ids']:
        print(f"Adding new transaction with ID: {transaction_id}")
        hash_table['transaction_ids'].append(hashed_transaction_id)
    else:
        print(f"Potential duplicate transaction detected with ID: {transaction_id}")
        user_decision = input("Do you want to add this transaction anyway? (y/n): ").strip().lower()
        if user_decision != 'y':
            print("Transaction addition cancelled.")
            return
    
    # Handle the categorization based on the address
    category = find_category_by_address(hash_table['addresses'], hashed_address)

    if not category:
        print(decrypt_address(encrypted_hashed_address))
        print(f"New address detected: {transaction['name']} {transaction['type']} {transaction['description']} {transaction['amount']}")
        category = get_user_category()
        hash_table['addresses'][encrypted_hashed_address] = category
    
    hash_table['categories'].setdefault(category, 0)
    hash_table['categories'][category] += transaction['amount']

    print(f"Transaction categorized under '{category}' with amount {transaction['amount']}. New total for '{category}': {hash_table['categories'][category]}")



def test_categorize_address():
    """
    Tests the address categorization function with a mock hash table and a test address. Demonstrates how an address is categorized and stored.
    """
    # Mock a hash table
    hash_table = {}
    
    print("Testing Address Categorization:")
    test_address = "123 Bank Street"
    categorize_address(test_address, hash_table)  #implement new test
    
    # Display the updated hash table
    print("\nUpdated Hash Table:")
    print(hash_table)
