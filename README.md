
# Fun Utilization and Categorization Kit (F.U.C.K.)

## Overview

The Fun Utilization and Categorization Kit (F.U.C.K.) is a locally run financial tracker designed to simplify personal finance management. It processes downloadable .csv formatted bank statements from online banking platforms, categorizing transactions and remembering specific addresses for future reference. The main goal is to offer a secure, private way to track spending without sharing sensitive financial data with third-party services.

## Features

- **Local Database**: Utilizes a secured, hashed, and encrypted local database to match known addresses to their respective categories, ensuring your financial data remains private and secure.
- **Transaction Categorization**: Automatically categorizes transactions from .csv bank statements based on previously encountered addresses.
- **Data Security**: Implements advanced cryptographic techniques for data security, including hashing and encryption.
- **Roadmap**: Future updates aim to introduce spending visualization, report cards, and extended data storage for comprehensive financial monitoring and review.

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

Currently, the project is in its early stages, focusing on hashing and decrypting functionalities. Future updates will expand on usage scenarios and capabilities.

## Configuration

For security reasons, you must set up environment variables for the encryption key and salt for hashing:

- **Linux/Unix**: `export GLOBAL_SALT=your_salt_here` and `export ENCRYPTION_KEY=your_encryption_key_here`
- **Windows**: `set GLOBAL_SALT=your_salt_here` and `set ENCRYPTION_KEY=your_encryption_key_here`

## Contribution

While this is a personal project, feedback and suggestions are welcome. Please feel free to reach out through GitHub.

## License

This project is licensed under the GNU General Public License v3.0. A copy of the license can be found in the LICENSE file within the project repository.
