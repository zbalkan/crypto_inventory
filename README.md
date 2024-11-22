# Crypto Key Inventory Management API

The **Crypto Key Inventory Management API** is a RESTful API designed for securely managing cryptographic keys and key types, with functionality adhering to industry standards such as PCI DSS. This API provides endpoints for creating, reading, updating, and deleting cryptographic keys and key types, along with features like key rotation, key status management, and lifecycle tracking.

This is a Proof of Concept, therefore the scurity configuration is ignored.

## Table of Contents

- [Features](#features)
- [Technologies](#technologies)
- [Installation](#installation)
- [Configuration](#configuration)
- [Endpoints](#endpoints)
- [License](#license)

## Features

- **Cryptographic Key Management**: Manage lifecycle and attributes of cryptographic keys, including key creation, rotation, suspension, revocation, and destruction.
- **Key Type Management**: Define and manage types of keys, including attributes such as algorithm, cryptoperiod, size, and more.
- **Audit and Compliance**: Track and log changes to keys for compliance purposes, including maintaining a history of state changes.
- **Periodic Key Expiry Checks**: Automatically expire keys that reach their expiration date.
- **Security and Integrity**: Follow best practices for security in API design and data management.

## Technologies

- **FastAPI**: Framework for building the REST API.
- **SQLAlchemy**: ORM for database interactions.
- **SQLite**: Database used for development (can be switched to other databases in production).
- **Pydantic**: Data validation and serialization.
- **ULID**: Unique identifiers for cryptographic keys and types.
- **Periodic Tasks**: Automatic key expiration checks.

## Installation

0. **Fork the repo**: Optional
1. **Clone the Repository**:

```bash
   git clone https://github.com/your-username/crypto-key-inventory.git
   cd crypto-key-inventory
```

2. **Create a Virtual Environment:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

3. **Install Dependencies:**

```bash
pip install -r requirements.txt
```

4. **Setup Database:** Run the application once to initialize the SQLite database, or set up your preferred database in database.py.

5. Configure development stuo with uvicorn and VS Code by adding this condiguration:

```json
        {
            "name": "Python: uvicorn",
            "type": "debugpy",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "main:app",
                "--app-dir",
                "src",
                "--reload",
            ]
        }
```

## Configuration

The main configuration file is config.py where you can set:

- Database settings (default is SQLite).
- Periodic task intervals.

Ensure the `config.py` aligns with your deployment.

## Endpoints

- Run the application using `uvicorn  --app-dir ./src main:app --reload` command.
- Visit either [Swagger UI](http://127.0.0.1:8000/docs) or [ReDoc](http://127.0.0.1:8000/redoc) for the endpoint documentation.

## Testing

Use `pytest` for testing. In VS Code, you can use the configuration below:

```json
 {
            "name": "Python: pytest",
            "type": "debugpy",
            "request": "launch",
            "module": "pytest",
            "args": [
                "--disable-warnings",
                "-v",
                "./src/tests"
            ],
            "env": {
                "PYTHONPATH": "${workspaceFolder}/src"
            }
        }
```

## License

This project is licensed under the Apache 2.0 License. See the LICENSE file for details.
