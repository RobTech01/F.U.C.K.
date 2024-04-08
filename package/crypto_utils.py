import os
from cryptography.fernet import Fernet
import hashlib

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


SALT = os.environ.get('GLOBAL_SALT', os.urandom(16))
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key())

cipher_suite = Fernet(ENCRYPTION_KEY)

def hash_address(address):
    """
    Hashes a bank address using a globally defined salt. This function uses PBKDF2_HMAC with
    SHA-256 hash function to create a secure hash of the input address.
    
    Args:
        address (str): The bank address to be hashed.
    
    Returns:
        str: The hexadecimal representation of the hashed address.
    """    
    return hashlib.pbkdf2_hmac('sha256', address.encode(), SALT, 100000).hex()

def encrypt_address(address):
    """
    Encrypts a bank address using the Fernet symmetric encryption, relying on a pre-defined
    global encryption key.
    
    Args:
        address (str): The bank address to be encrypted.
    
    Returns:
        str: The encrypted address, encoded in Base64.
    """
    return cipher_suite.encrypt(address.encode()).decode()

def decrypt_address(encrypted_address):
    """
    Decrypts a previously encrypted bank address, using the same global encryption key.
    
    Args:
        encrypted_address (str): The encrypted address in Base64 encoding to be decrypted.
    
    Returns:
        str: The original bank address after decryption.
    """
    return cipher_suite.decrypt(encrypted_address.encode()).decode()


def test_crypto_functions():
    """
    Decrypts a previously encrypted bank address, using the same global encryption key.
    
    Args:
        encrypted_address (str): The encrypted address in Base64 encoding to be decrypted.
    
    Returns:
        str: The original bank address after decryption.
    """
    test_address = "123 Bank Street"
    print("Testing Encryption & Decryption:")
    encrypted = encrypt_address(test_address)
    print(f"Encrypted: {encrypted}")
    decrypted = decrypt_address(encrypted)
    print(f"Decrypted: {decrypted}")

    print("\nTesting Hashing:")
    hashed = hash_address(test_address)
    print(f"Hashed: {hashed}")

if __name__ == "__main__":
    test_crypto_functions()
