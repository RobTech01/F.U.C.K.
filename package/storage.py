from crypto_utils import cipher_suite
import json


path_to_your_hash_table = '../storage/hash_table.enc'
HASH_TABLE_FILE = path_to_your_hash_table


def save_hash_table(hash_table):
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


def load_hash_table():
    """
    Loads and decrypts the hash table from a file. This function reads the encrypted data from
    the specified file, decrypts it using the Fernet cipher suite, and converts the JSON string
    back into a dictionary.
    
    Returns:
        dict: The decrypted hash table. If the file does not exist, returns an empty dictionary.
    """
    try:
        with open(HASH_TABLE_FILE, 'rb') as file:
            encrypted_data = file.read()
        decrypted_data = cipher_suite.decrypt(encrypted_data)
        return json.loads(decrypted_data.decode())
    except FileNotFoundError:
        return {}  # Return an empty hash table if file does not exist


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



if __name__ == "__main__":
    test_secure_storage()