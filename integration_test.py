#!/usr/bin/env python3
"""
Integration test - validates the full pipeline without user interaction
"""

import sys
import tempfile
import os
from pathlib import Path

# Test imports
print("Testing imports...")
try:
    from package import initialize_crypto, load_hash_table, save_hash_table
    from package.core import validate_csv_file, sanitize_transaction, validate_transaction
    from package.config import Config, get_bank_identifier
    print("✓ All imports successful")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test CSV validation
print("\nTesting CSV validation...")
is_valid, error = validate_csv_file('dummy-data/january.csv')
if is_valid:
    print("✓ CSV validation passed")
else:
    print(f"✗ CSV validation failed: {error}")
    sys.exit(1)

# Test transaction sanitization and validation
print("\nTesting transaction processing...")
test_transaction = {
    'date': '2024-01-01',
    'address': 'Test Store',
    'amount': 100.50,
    'name': 'Test Name',
    'type': 'Purchase',
    'description': 'Test purchase'
}

sanitized = sanitize_transaction(test_transaction)
is_valid, error = validate_transaction(sanitized)
if is_valid:
    print("✓ Transaction validation passed")
else:
    print(f"✗ Transaction validation failed: {error}")
    sys.exit(1)

# Test malicious input detection
print("\nTesting security validation...")
malicious_transaction = {
    'date': '2024-01-01',
    'address': "'; DROP TABLE users; --",
    'amount': 100
}
is_valid, error = validate_transaction(malicious_transaction)
if not is_valid and "Suspicious" in error:
    print("✓ SQL injection detected and blocked")
else:
    print("✗ Security validation failed - malicious input not detected!")
    sys.exit(1)

# Test config system
print("\nTesting configuration system...")
with tempfile.TemporaryDirectory() as tmpdir:
    config_file = os.path.join(tmpdir, 'test_config.json')
    config = Config(config_file=config_file)

    # Test bank identifier
    headers = ['Date', 'Amount', 'Description']
    bank_id = get_bank_identifier(headers)

    # Test saving mapping
    mapping = {'date': 0, 'amount': 1, 'description': 2}
    config.save_column_mapping(bank_id, mapping)

    # Test loading mapping
    loaded = config.get_column_mapping(bank_id)
    if loaded == mapping:
        print("✓ Config save/load works")
    else:
        print(f"✗ Config test failed: {loaded} != {mapping}")
        sys.exit(1)

print("\n" + "="*50)
print("✓ ALL INTEGRATION TESTS PASSED")
print("="*50)
print("\nThe system is ready for use!")
print("Note: Full end-to-end testing requires interactive mode")
print("      (crypto key setup, column selection, categorization)")
