import csv
from package.category_manager import categorize_transaction
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


def process_csv_file(filepath : str) -> None:
    hash_table = load_hash_table()
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
            categorize_transaction(transaction, hash_table)
                
                
    save_hash_table(hash_table)
    print("CSV file processed successfully.")



def main():
    filepath = './dummy-data/january.csv'  # Adjust with your actual CSV file path
    process_csv_file(filepath)

if __name__ == "__main__":
    main()
