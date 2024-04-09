import csv
from package.category_manager import categorize_address
from package.storage import load_hash_table, save_hash_table

def select_csv_columns(header):
    print("Please select the column number for the following data:")
    for index, col_name in enumerate(header):
        print(f"{index + 1}. {col_name}")
    address_col = int(input("\nAddress column: ")) - 1
    amount_col = int(input("Amount column: ")) - 1
    name_col = int(input("Name column (Enter to skip): ") or -1) - 1
    type_col = int(input("Transaction type/text column (Enter to skip): ") or -1) - 1
    description_col = int(input("Description column (Enter to skip): ") or -1) - 1



    return address_col, amount_col, name_col, type_col, description_col

def process_csv_file(filepath):
    hash_table = load_hash_table()
    try:
        with open(filepath, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            header = next(reader)
            address_col, amount_col, name_col, type_col, description_col = select_csv_columns(header)

            for row in reader:
                address = row[address_col]
                amount = row[amount_col]
                name = row[name_col] if description_col >= 0 else ""
                type = row[type_col] if description_col >= 0 else ""
                description = row[description_col] if description_col >= 0 else ""
                # Assume categorize_address now also handles amount (this part requires updating your logic)
                categorize_address(f"{address} {amount} {name} {type} {description}", amount, hash_table)
                
                
        save_hash_table(hash_table)
        print("CSV file processed successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    filepath = './dummy-data/january.csv'  # Adjust with your actual CSV file path
    process_csv_file(filepath)

if __name__ == "__main__":
    main()
