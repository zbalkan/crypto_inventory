# crud.py
from typing import Optional, Sequence

from sqlalchemy.orm import Session

from models import CryptoKey, KeyType
from schemas import (CryptoKeyCreate, CryptoKeySchema, KeyTypeCreate,
                     KeyTypeSchema)
from utils import parse_cryptoperiod


def get_key_types(db: Session, skip: int = 0, limit: int = 10) -> Sequence[KeyTypeSchema]:
    # Query the database to retrieve KeyType models
    db_key_types = db.query(KeyType).offset(skip).limit(limit).all()
    # Convert each KeyType model to KeyTypeSchema using model_validate
    return [KeyTypeSchema.model_validate(db_key_type) for db_key_type in db_key_types]


def get_key_type(db: Session, key_type_id: int) -> Optional[KeyTypeSchema]:
    # Retrieve a single KeyType model from the database
    db_key_type = db.query(KeyType).filter(KeyType.id == key_type_id).first()
    # Convert to KeyTypeSchema if the model exists
    return KeyTypeSchema.model_validate(db_key_type) if db_key_type else None


def create_key_type(db: Session, key_type: KeyTypeCreate) -> KeyTypeSchema:
    # Create a new KeyType model using input from the KeyTypeCreate schema
    db_key_type = KeyType(
        name=key_type.name,
        description=key_type.description,
        cryptoperiod_days=parse_cryptoperiod(key_type.cryptoperiod)
    )
    db.add(db_key_type)
    db.commit()
    db.refresh(db_key_type)
    # Convert the database model to KeyTypeSchema for the response
    return KeyTypeSchema.model_validate(db_key_type)


def get_crypto_keys(db: Session, skip: int = 0, limit: int = 10) -> Sequence[CryptoKeySchema]:
    # Query the database to retrieve CryptoKey models
    db_crypto_keys = db.query(CryptoKey).offset(skip).limit(limit).all()
    # Convert each CryptoKey model to CryptoKeySchema
    return [CryptoKeySchema.model_validate(db_crypto_key) for db_crypto_key in db_crypto_keys]


def get_crypto_key(db: Session, key_id: int) -> Optional[CryptoKeySchema]:
    # Retrieve a single CryptoKey model from the database
    db_crypto_key = db.query(CryptoKey).filter(CryptoKey.id == key_id).first()
    # Convert to CryptoKeySchema if the model exists
    return CryptoKeySchema.model_validate(db_crypto_key) if db_crypto_key else None


def create_crypto_key(db: Session, crypto_key: CryptoKeyCreate) -> CryptoKeySchema:
    # Create a new CryptoKey model using input from the CryptoKeyCreate schema
    db_crypto_key = CryptoKey(**crypto_key.dict())
    db.add(db_crypto_key)
    db.commit()
    db.refresh(db_crypto_key)
    # Convert the database model to CryptoKeySchema for the response
    return CryptoKeySchema.model_validate(db_crypto_key)
