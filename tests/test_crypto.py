"""
Unit tests for crypto.py encryption and hashing functions
"""

import unittest
from cryptography.fernet import Fernet
from package.crypto import (
    hash_address,
    encrypt_address,
    decrypt_address,
    hash_transaction_id
)


class TestHashFunctions(unittest.TestCase):
    """Test hashing functions for addresses and transaction IDs"""

    def setUp(self):
        """Set up test salt for hashing"""
        self.test_salt = b'test_salt_12345678901234567890'

    def test_hash_address_deterministic(self):
        """Test that hashing the same address twice produces the same hash"""
        address = "Walmart Supercenter"
        hash1 = hash_address(address, self.test_salt)
        hash2 = hash_address(address, self.test_salt)

        self.assertEqual(hash1, hash2)
        self.assertIsInstance(hash1, str)
        self.assertEqual(len(hash1), 64)  # SHA-256 produces 64 hex chars

    def test_hash_address_different_inputs(self):
        """Test that different addresses produce different hashes"""
        address1 = "Target Store"
        address2 = "Walmart Store"

        hash1 = hash_address(address1, self.test_salt)
        hash2 = hash_address(address2, self.test_salt)

        self.assertNotEqual(hash1, hash2)

    def test_hash_address_different_salt(self):
        """Test that same address with different salt produces different hash"""
        address = "Best Buy"
        salt1 = b'salt1_12345678901234567890123'
        salt2 = b'salt2_12345678901234567890123'

        hash1 = hash_address(address, salt1)
        hash2 = hash_address(address, salt2)

        self.assertNotEqual(hash1, hash2)

    def test_hash_transaction_id_deterministic(self):
        """Test that hashing the same transaction ID produces the same hash"""
        tx_id = "2024-01-01_100.50_abc123"
        hash1 = hash_transaction_id(tx_id, self.test_salt)
        hash2 = hash_transaction_id(tx_id, self.test_salt)

        self.assertEqual(hash1, hash2)
        self.assertIsInstance(hash1, str)
        self.assertEqual(len(hash1), 64)

    def test_hash_transaction_id_different_inputs(self):
        """Test that different transaction IDs produce different hashes"""
        tx_id1 = "2024-01-01_100.50_abc123"
        tx_id2 = "2024-01-02_200.00_def456"

        hash1 = hash_transaction_id(tx_id1, self.test_salt)
        hash2 = hash_transaction_id(tx_id2, self.test_salt)

        self.assertNotEqual(hash1, hash2)


class TestEncryptionFunctions(unittest.TestCase):
    """Test encryption and decryption functions"""

    def setUp(self):
        """Set up test cipher suite"""
        # Generate a test Fernet key
        self.test_key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.test_key)

    def test_encrypt_decrypt_roundtrip(self):
        """Test that encrypting then decrypting returns original address"""
        original = "Chase Bank Downtown"

        encrypted = encrypt_address(original, self.cipher_suite)
        decrypted = decrypt_address(encrypted, self.cipher_suite)

        self.assertEqual(original, decrypted)

    def test_encrypt_produces_different_output(self):
        """Test that encrypted data doesn't match original"""
        original = "Wells Fargo"
        encrypted = encrypt_address(original, self.cipher_suite)

        self.assertNotEqual(original, encrypted)
        self.assertIsInstance(encrypted, str)

    def test_encrypt_different_addresses(self):
        """Test that different addresses produce different encrypted outputs"""
        address1 = "Bank of America"
        address2 = "Citibank"

        encrypted1 = encrypt_address(address1, self.cipher_suite)
        encrypted2 = encrypt_address(address2, self.cipher_suite)

        self.assertNotEqual(encrypted1, encrypted2)

    def test_decrypt_with_wrong_key_fails(self):
        """Test that decryption with wrong key raises an exception"""
        original = "TD Bank"
        encrypted = encrypt_address(original, self.cipher_suite)

        # Create a different cipher suite with different key
        wrong_key = Fernet.generate_key()
        wrong_cipher = Fernet(wrong_key)

        # Decryption should fail
        with self.assertRaises(Exception):
            decrypt_address(encrypted, wrong_cipher)

    def test_encrypt_empty_string(self):
        """Test that encrypting empty string works"""
        original = ""
        encrypted = encrypt_address(original, self.cipher_suite)
        decrypted = decrypt_address(encrypted, self.cipher_suite)

        self.assertEqual(original, decrypted)

    def test_encrypt_special_characters(self):
        """Test that addresses with special characters are handled correctly"""
        original = "Store #123 @ Main St. & 5th Ave!"
        encrypted = encrypt_address(original, self.cipher_suite)
        decrypted = decrypt_address(encrypted, self.cipher_suite)

        self.assertEqual(original, decrypted)

    def test_encrypt_unicode_characters(self):
        """Test that addresses with unicode characters work"""
        original = "Café René & Søren's Store"
        encrypted = encrypt_address(original, self.cipher_suite)
        decrypted = decrypt_address(encrypted, self.cipher_suite)

        self.assertEqual(original, decrypted)


class TestCryptoIntegration(unittest.TestCase):
    """Test integration between hashing and encryption"""

    def setUp(self):
        """Set up test crypto components"""
        self.test_salt = b'integration_test_salt_1234567'
        self.test_key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.test_key)

    def test_hash_then_encrypt_workflow(self):
        """Test typical workflow: hash for lookup, encrypt for storage"""
        address = "Target Store #542"

        # Hash for use as dictionary key
        hashed = hash_address(address, self.test_salt)

        # Encrypt for secure storage
        encrypted = encrypt_address(address, self.cipher_suite)

        # Verify hash is deterministic (can be used for lookup)
        hashed_again = hash_address(address, self.test_salt)
        self.assertEqual(hashed, hashed_again)

        # Verify encrypted data can be decrypted
        decrypted = decrypt_address(encrypted, self.cipher_suite)
        self.assertEqual(address, decrypted)

    def test_multiple_addresses_workflow(self):
        """Test handling multiple addresses (realistic scenario)"""
        addresses = [
            "Walmart Supercenter",
            "Target",
            "Best Buy",
            "Amazon.com",
            "Whole Foods Market"
        ]

        hash_map = {}
        encrypted_map = {}

        # Process all addresses
        for addr in addresses:
            hashed = hash_address(addr, self.test_salt)
            encrypted = encrypt_address(addr, self.cipher_suite)

            hash_map[hashed] = encrypted
            encrypted_map[addr] = encrypted

        # Verify all hashes are unique
        self.assertEqual(len(hash_map), len(addresses))

        # Verify all can be decrypted correctly
        for addr in addresses:
            encrypted = encrypted_map[addr]
            decrypted = decrypt_address(encrypted, self.cipher_suite)
            self.assertEqual(addr, decrypted)


if __name__ == '__main__':
    unittest.main()
