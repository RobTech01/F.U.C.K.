import os
from cryptography.fernet import Fernet
import hashlib
from pathlib import Path
from . import cli

# This script demonstrates how to securely hash and encrypt data, specifically bank addresses,
# using a global salt and encryption key. These keys should ideally be stored and fetched from
# a secure location or environment variables for enhanced security.
#
# Environment Variable Setup:
# 1. Create a .env file in the project root with:
#    FUCK_GLOBAL_SALT=your_32_char_hex_string
#    FUCK_ENCRYPTION_KEY=your_44_char_fernet_key
#
# 2. Or use system environment variables:
#    - Linux/Unix: export FUCK_GLOBAL_SALT=... && export FUCK_ENCRYPTION_KEY=...
#    - Windows: set FUCK_GLOBAL_SALT=... && set FUCK_ENCRYPTION_KEY=...


def load_env_file():
    """
    Load environment variables from .env file if it exists.
    Provides simple .env file support without external dependencies.
    """
    env_file = Path('.env')
    if not env_file.exists():
        return

    try:
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                # Parse KEY=VALUE format
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    # Set environment variable only if not already set
                    if key not in os.environ:
                        os.environ[key] = value
    except Exception as e:
        print(f"Warning: Could not load .env file: {e}")


def initialize_crypto() -> list[Fernet, str]:
    """
    Initializes the cryptographic components by loading or prompting for the encryption key and salt.
    Loads from .env file first, then environment variables, then prompts user.

    Returns:
        Tuple[Fernet, bytes]: A cipher suite object and the salt
    """
    # Load .env file if it exists
    load_env_file()

    # Load or prompt for the global salt
    SALT = os.environ.get('FUCK_GLOBAL_SALT')
    if not SALT:
        SALT = cli.prompt_for_salt()
    else:
        try:
            SALT = bytes.fromhex(SALT)
        except ValueError:
            print("Warning: Invalid FUCK_GLOBAL_SALT in environment, generating new salt")
            SALT = cli.prompt_for_salt()

    # Load or prompt for the encryption key
    ENCRYPTION_KEY = os.environ.get('FUCK_ENCRYPTION_KEY')
    if not ENCRYPTION_KEY:
        ENCRYPTION_KEY = cli.prompt_for_encryption_key()
    else:
        try:
            ENCRYPTION_KEY = ENCRYPTION_KEY.encode()
            # Validate it's a proper Fernet key
            Fernet(ENCRYPTION_KEY)
        except Exception:
            print("Warning: Invalid FUCK_ENCRYPTION_KEY in environment, generating new key")
            ENCRYPTION_KEY = cli.prompt_for_encryption_key()

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