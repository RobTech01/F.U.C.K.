import csv
import argparse
from package.category_manager import categorize_transaction
from package.crypto_utils import initialize_crypto
from package.storage import load_hash_table, save_hash_table, print_hash_table
from typing import Tuple, List


def select_csv_columns(header : List[str]) -> Tuple[int, int, int, int, int, int]:

    print("Please select the column number for the following data:")
    for index, col_name in enumerate(header):
        print(f"{index + 1}. {col_name}")
    date_col : int = int(input("\nDate column: ")) - 1
    name_col : int = int(input("Name column (Enter to skip): ") or -1) - 1
    address_col : int = int(input("Address column: ")) - 1
    type_col : int = int(input("Transaction type/text column (Enter to skip): ") or -1) - 1
    description_col : int = int(input("Description column (Enter to skip): ") or -1) - 1
    amount_col : int = int(input("Amount column: ")) - 1

    return date_col, address_col, amount_col, name_col, type_col, description_col


def user_confirm_action(prompt: str) -> bool:
    """
    Prompts the user with a yes/no question and returns the user's decision.
    
    Args:
        prompt (str): The prompt to display to the user.
    
    Returns:
        bool: True if the user confirms (yes), False otherwise (no).
    """
    response = input(f"{prompt} (y/n): ").strip().lower()
    return response == 'y'


def process_csv_file(filepath : str, hash_table : dict, cipher_suite, SALT) -> None:
    #print_hash_table(hash_table)
    with open(filepath, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        header = next(reader)
        date_col, address_col, amount_col, name_col, type_col, description_col = select_csv_columns(header)

        for row in reader:
            date = row[date_col]
            address = row[address_col]
            amount = float(row[amount_col])
            name = row[name_col] if description_col >= 0 else ""
            type = row[type_col] if description_col >= 0 else ""
            description = row[description_col] if description_col >= 0 else ""
               
            transaction = {'date' : date, 'address': address, 'amount': amount, 'name': name, "type": type, "description":description}
            categorize_transaction(transaction, hash_table, cipher_suite, SALT)


def main(csv_file_path: str):
    cipher_suite, SALT = initialize_crypto()
    hash_table = load_hash_table(cipher_suite)
    print("Table loaded successfully.")

    process_csv_file(csv_file_path, hash_table, cipher_suite, SALT)
    print("CSV file processed successfully.")

    save_hash_table(hash_table, cipher_suite)
    print("File saved successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a new data file and categorize transactions.")
    parser.add_argument("csv_file_path", type=str, default = '../dummy-data/january.csv')

    args = parser.parse_args()

    main(args.csv_file_path)
