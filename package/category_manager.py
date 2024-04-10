from package.crypto_utils import hash_address, encrypt_address


def get_user_category() -> int:
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
        return user_input
    else:
        print("Invalid input.")
        return get_user_category()  # Recursively prompt until valid input


def categorize_address(address : str, amount : float, hash_table : dict) -> None:
    """
    Modifies the hash_table in place to categorize the given address, adding the amount
    to the total for the category. If the address is new, prompts the user for the category.
    
    Args:
        address (str): The transaction address or description.
        amount (float): The transaction amount.
        hash_table (dict): The hash table storing categories, addresses, and amounts.
    """
    hashed_address = hash_address(address)
    
    if hashed_address not in hash_table:
        print(f"New address detected. {address}")
        category = get_user_category()
        encrypted_address = encrypt_address(address)
        hash_table[hashed_address] = {
            'category': category,
            'addresses': [encrypted_address],
            'total_amount': amount
        }
    else:
        # Update the existing category with the new amount and address
        hash_table[hashed_address]['total_amount'] += amount
        if encrypt_address(address) not in hash_table[hashed_address]['addresses']:
            hash_table[hashed_address]['addresses'].append(encrypt_address(address))
    
    print(f"Transaction categorized under '{hash_table[hashed_address]['category']}' with amount {amount}.")


def test_categorize_address():
    """
    Tests the address categorization function with a mock hash table and a test address. Demonstrates how an address is categorized and stored.
    """
    # Mock a hash table
    hash_table = {}
    
    print("Testing Address Categorization:")
    test_address = "123 Bank Street"
    categorize_address(test_address, hash_table)
    
    # Display the updated hash table
    print("\nUpdated Hash Table:")
    print(hash_table)
