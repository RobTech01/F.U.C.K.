from package.storage import load_hash_table, print_hash_table, get_categories_and_totals
from package.crypto_utils import initialize_crypto

cipher_suite, SALT = initialize_crypto()
hash_table = load_hash_table(cipher_suite)

dummy = load_hash_table(cipher_suite)

get_categories_and_totals(dummy)