import os
from cryptography.fernet import Fernet
import hashlib

# Ideally, these keys should be securely fetched from a secure storage or environment variables
# on Linux / Unix: export GLOBAL_SALT=your_byte_string_here
# on Windows: set GLOBAL_SALT=your_byte_string_here
SALT = os.environ.get('GLOBAL_SALT', os.urandom(16))
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key())

cipher_suite = Fernet(ENCRYPTION_KEY)

def hash_address(address):
    """Hash a bank address with a global salt."""
    return hashlib.pbkdf2_hmac('sha256', address.encode(), SALT, 100000).hex()

def encrypt_address(address):
    """Encrypt a bank address."""
    return cipher_suite.encrypt(address.encode()).decode()

def decrypt_address(encrypted_address):
    """Decrypt a bank address."""
    return cipher_suite.decrypt(encrypted_address.encode()).decode()


def test_crypto_functions():
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
