
# Fund Utilization and Categorization Kit (F.U.C.K.)

## Overview

The Fund Utilization and Categorization Kit (F.U.C.K.) is a locally run financial tracker for personal finance management. It processes downloadable .csv formatted bank statements from online banking platforms, categorizing transactions and remembering specific addresses for future reference. The main goal is to not having to do it manually in a spreadsheet.
## Features

- **Local Database**: Utilizes a hashed, and encrypted local database to match known addresses to their respective categories.
- **Transaction Categorization**: Automatically categorizes transactions from .csv bank statements based on previously encountered addresses, or asks for clarification for new addresses.
- **Roadmap**: Future updates aim to introduce spending visualization, report cards, and extended categorized & "blended" data storage for long-term financial monitoring.

## Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/yourgithubusername/FUCK.git
cd FUCK
pip install -r requirements.txt
```

## Requirements

Ensure you have Python 3.6+ installed on your system. Dependencies are listed in the `requirements.txt` file, which includes necessary libraries such as `cryptography` for encryption and `hashlib` for hashing functionalities.

## Usage

Currently only hashing and decrypting functionalities are fully implemented. Future updates will expand on the capabilities.

## Configuration

Your bank might order the .csv headers differently.. adjust the relevant indices accordingly in main.py

For security reasons, you must set up environment variables for the encryption key and salt for hashing:

- **Linux/Unix**: `export FUCK_GLOBAL_SALT=your_salt_here` and `export FUCK_ENCRYPTION_KEY=your_encryption_key_here`
- **Windows**: `set FUCK_GLOBAL_SALT=your_salt_here` and `set FUCK_ENCRYPTION_KEY=your_encryption_key_here`

## Contribution

Feel free to reach out through GitHub.

## License

This project is licensed under the GNU General Public License v3.0. A copy of the license can be found in the LICENSE file within the project repository.
