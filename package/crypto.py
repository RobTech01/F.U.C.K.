import os
from cryptography.fernet import Fernet
import hashlib
import getpass  

# This script demonstrates how to securely hash and encrypt data, specifically bank addresses,
# using a global salt and encryption key. These keys should ideally be stored and fetched from
# a secure location or environment variables for enhanced security.
# 
# Environment Variable Setup Example:
# - Linux/Unix: Use the command `export GLOBAL_SALT=your_byte_string_here` and
#   `export ENCRYPTION_KEY=your_encryption_key_here` to set these variables.
# - Windows: Use `set GLOBAL_SALT=your_byte_string_here` and 
#   `set ENCRYPTION_KEY=your_encryption_key_here` in the command prompt.
#
# Note: `os.urandom(16)` generates a 16-byte random value which is suitable for cryptographic use
# as a fallback for both the salt and the encryption key. However, it's recommended to have consistent
# values especially for the salt to ensure hash consistency across application runs.

def secure_input(prompt) -> None:
    """
    Securely inputs data from the user, hiding it from the terminal.
    Note: getpass doesn't visually hide the input in some IDEs or Jupyter notebooks.
    """
    try:
        return getpass.getpass(prompt)
    except Exception as e:
        print(f"Error obtaining secure input: {e}")
        return None


def initialize_crypto() -> list[Fernet, str]:
    """
    Initializes the cryptographic components by loading or prompting for the encryption key and salt.
    Returns a Fernet cipher suite configured with the encryption key.

    Returns:
        Fernet: A cipher suite object initialized with the encryption key.
    """
    # Load or prompt for the global salt
    SALT = os.environ.get('FUCK_GLOBAL_SALT')
    if not SALT:
        SALT = secure_input("Please paste the global salt here (Enter to skip): ")
        if not SALT:
            SALT = os.urandom(16)
            print(f"\nSuggested command to set the environment variable:\nexport FUCK_GLOBAL_SALT={SALT.hex()}")

    # Load or prompt for the encryption key
    ENCRYPTION_KEY = os.environ.get('FUCK_ENCRYPTION_KEY')
    if not ENCRYPTION_KEY:
        ENCRYPTION_KEY = secure_input("Please paste the encryption key here (Enter to skip): ")
        if not ENCRYPTION_KEY:
            ENCRYPTION_KEY = Fernet.generate_key()
            print(f"\nSuggested command to set the environment variable:\nexport FUCK_ENCRYPTION_KEY={ENCRYPTION_KEY.decode()}")

    # Ensure the types are correct for cryptographic operations
    SALT = bytes.fromhex(SALT) if isinstance(SALT, str) else SALT
    ENCRYPTION_KEY = ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY

    # Initialize and return the cipher suite
    return Fernet(ENCRYPTION_KEY), SALT


def hash_address(address : str, SALT) -> str:
    """
    Hashes a bank address using a globally defined salt. This function uses PBKDF2_HMAC with
    SHA-256 hash function to create a secure hash of the input address.
    
    Args:
        address (str): The bank address to be hashed.
    
    Returns:
        str: The hexadecimal representation of the hashed address.
    """    
    return hashlib.pbkdf2_hmac('sha256', address.encode(), SALT, 100000).hex()


def encrypt_address(address : str, cipher_suite) -> str:
    """
    Encrypts a bank address using the Fernet symmetric encryption, relying on a pre-defined
    global encryption key.
    
    Args:
        address (str): The bank address to be encrypted.
    
    Returns:
        str: The encrypted address, encoded in Base64.
    """
    return cipher_suite.encrypt(address.encode()).decode()


def decrypt_address(encrypted_address : str, cipher_suite) -> str:
    """
    Decrypts a previously encrypted bank address, using the same global encryption key.
    
    Args:
        encrypted_address (str): The encrypted address in Base64 encoding to be decrypted.
    
    Returns:
        str: The original bank address after decryption.
    """
    return cipher_suite.decrypt(encrypted_address.encode()).decode()


def hash_transaction_id(transaction_id: str, SALT) -> str:
    """
    Generates a unique hash for a transaction using low-sensitivity data.
    
    Args:
        transaction (dict): Transaction data, containing keys like 'date', 'amount'.
    
    Returns:
        str: A hexadecimal string representing the hashed transaction details.
    """
    hashed_details = hashlib.pbkdf2_hmac('sha256', transaction_id.encode(), SALT, 100000).hex()
    return hashed_details



def test_crypto_functions():
    """Prints messages to the console indicating the categorization status of the address.
        str: The original bank address after decryption.
    """
    test_address = "123 Bank Street"
    print("Testing Encryption & Decryption:")
    encrypted = encrypt_address(test_address)
    print(f"Encrypted: {encrypted}")
    decrypted = decrypt_address(encrypted)
    print(f"Decrypted: {decrypted}")

    print("\nTesting Hashing:")
    hashed = hash_address(test_address, SALT)
    print(f"Hashed: {hashed}")