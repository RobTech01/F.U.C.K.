from crypto_utils import cipher_suite
import json


path_to_your_hash_table = '../storage/hash_table.enc'
HASH_TABLE_FILE = path_to_your_hash_table

def save_hash_table(hash_table):
    """Encrypt and save the hash table."""
    encrypted_data = cipher_suite.encrypt(json.dumps(hash_table).encode())
    with open(HASH_TABLE_FILE, 'wb') as file:
        file.write(encrypted_data)

def load_hash_table():
    """Load and decrypt the hash table."""
    try:
        with open(HASH_TABLE_FILE, 'rb') as file:
            encrypted_data = file.read()
        decrypted_data = cipher_suite.decrypt(encrypted_data)
        return json.loads(decrypted_data.decode())
    except FileNotFoundError:
        return {}  # Return an empty hash table if file does not exist


def test_secure_storage():
    # Mock a hash table with some data
    dummy_hash_table = {
        'test_hash_1': {'category': 'Utilities', 'address': 'encrypted_address_1'},
        'test_hash_2': {'category': 'Groceries', 'address': 'encrypted_address_2'}
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