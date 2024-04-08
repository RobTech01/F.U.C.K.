from crypto_utils import hash_address, encrypt_address

def get_user_category():
    """Prompt the user to specify a category for a new bank address."""
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
    """Categorize a new bank address if it's not already in the hash table."""
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