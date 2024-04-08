from crypto_utils import hash_address, encrypt_address

def get_user_category():
    """
    Interactively prompts the user to categorize a new bank address. 
    The user can select from a predefined list of categories or enter a new category.

    Returns:
        str: The chosen or entered category for the bank address.
    """
    print("\nPlease categorize the new bank address:")
    categories = ['Groceries', 'Utilities', 'Rent', 'Entertainment', 'Other']
    for i, category in enumerate(categories, 1):
        print(f"{i}. {category}")
    print("Select a number or enter a new category.")

    user_input = input("> ").strip()
    if user_input.isdigit() and 1 <= int(user_input) <= len(categories):
        return categories[int(user_input) - 1]
    elif user_input:
        return user_input
    else:
        print("Invalid input.")
        return get_user_category()  # Recursively prompt until valid input

def categorize_address(address, hash_table):
    """
    Categorizes a new bank address by either identifying it as already categorized or prompting the user to categorize it. 
    Utilizes hashing for address identification and encryption for secure storage of addresses.

    Args:
        address (str): The bank address to categorize.
        hash_table (dict): A hash table where each entry maps a hashed address to its category and encrypted form.

    Side Effects:
        Prints messages to the console indicating the categorization status of the address.
        Updates the hash_table with a new entry if the address is newly categorized.
    """
    hashed_address = hash_address(address)
    
    if hashed_address in hash_table:
        print("Address already categorized.")
    else:
        print(f"New address detected. {address}")
        category = get_user_category()
        encrypted_address = encrypt_address(address)
        hash_table[hashed_address] = {'category': category, 'address': encrypted_address}
        print(f"Address categorized under '{category}'.")

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

if __name__ == "__main__":
    test_categorize_address()