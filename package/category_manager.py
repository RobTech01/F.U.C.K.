from package.crypto_utils import hash_address, encrypt_address, hash_transaction_id


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
        raise TypeError("hash_table must be a dictionary.")
    
    # Assuming helper functions `encrypt_address`, `hash_address`, and `generate_transaction_id` are defined correctly
    encrypted_hashed_address = encrypt_address(hash_address(transaction['address']))

    # Generate and hash the transaction ID
    transaction_id = generate_transaction_id(transaction['date'], transaction['amount'])
    hashed_transaction_id = hash_transaction_id(transaction_id)  # Ensure this function returns a hash string

    if hashed_transaction_id in hash_table['transaction_ids']:
        print(f"Potential duplicate transaction detected with ID: {transaction_id}")
        user_decision = input("Do you want to add this transaction anyway? (y/n): ").strip().lower()
        if user_decision != 'y':
            print("Transaction addition cancelled.")
            return
        
    print(f"adding new transaction with ID: {transaction_id}")


    # If the address is new or duplicate transaction is confirmed to be added
    if encrypted_hashed_address not in hash_table['addresses']:
        # Prompt for new category if the address is not recognized
        print(f"New address detected: {transaction['address']}")
        category = get_user_category()
        hash_table['addresses'][encrypted_hashed_address] = category
        hash_table['categories'].setdefault(category, 0)
    else:
        # Retrieve existing category for the address
        category = hash_table['addresses'][encrypted_hashed_address]

    # Update category total and transaction IDs
    hash_table['categories'][category] += transaction['amount']
    hash_table['transaction_ids'].add(hashed_transaction_id)  # Track this transaction ID to prevent future duplicates

    print(f"Transaction categorized under '{category}' with amount {transaction['amount']}.")


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
