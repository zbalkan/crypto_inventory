# crud.py
from sqlite3 import IntegrityError
from typing import Optional, Sequence

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from models import CryptoKey, KeyType
from schemas import (CryptoKeyCreate, CryptoKeySchema, KeyTypeCreate,
                     KeyTypeSchema)
from utils import parse_cryptoperiod, validate_cryptoperiod_days


def get_key_types(db: Session, skip: int = 0, limit: int = 10) -> Sequence[KeyTypeSchema]:
    try:
        db_key_types = db.query(KeyType).offset(skip).limit(limit).all()
        return [KeyTypeSchema.model_validate(db_key_type) for db_key_type in db_key_types]
    except SQLAlchemyError as e:
        # Log the error and re-raise it as a user-friendly HTTPException
        print(f"Error fetching key types: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to fetch key types")


def get_key_type(db: Session, key_type_id: int) -> Optional[KeyTypeSchema]:
    # Retrieve a single KeyType model from the database
    db_key_type = db.query(KeyType).filter(KeyType.id == key_type_id).first()
    # Convert to KeyTypeSchema if the model exists
    return KeyTypeSchema.model_validate(db_key_type) if db_key_type else None


def create_key_type(db: Session, key_type: KeyTypeCreate) -> KeyTypeSchema:
    try:
        cryptoperiod_days = parse_cryptoperiod(key_type.cryptoperiod)
        validate_cryptoperiod_days(cryptoperiod_days)  # Business rule validation

        db_key_type = KeyType(
            name=key_type.name,
            description=key_type.description,
            algorithm=key_type.algorithm,
            size_bits=key_type.size_bits,
            generated_by=key_type.generated_by,
            form_factor=key_type.form_factor,
            uniqueness_scope=key_type.uniqueness_scope,
            cryptoperiod_days=cryptoperiod_days
        )
        db.add(db_key_type)
        db.commit()
        db.refresh(db_key_type)
        return KeyTypeSchema.model_validate(db_key_type)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=400, detail="Key type already exists or invalid data")
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail="Failed to create key type")


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
