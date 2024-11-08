# crud.py
from sqlite3 import IntegrityError
from typing import Any, Optional, Sequence, Type

from fastapi import HTTPException
from sqlalchemy import asc, desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from models import CryptoKey, KeyStatus, KeyType
from schemas import (CryptoKeyCreate, CryptoKeySchema, KeyTypeCreate,
                     KeyTypeSchema)
from utils import parse_cryptoperiod, validate_cryptoperiod_days


def apply_filters_and_sorting(
    query, model: Type, filters: Optional[dict] = None, order_by: Optional[str] = None
):
    # Apply filters
    if filters:
        for field, value in filters.items():
            if hasattr(model, field):
                query = query.filter(getattr(model, field) == value)
            else:
                raise HTTPException(
                    status_code=400, detail=f"Invalid filter field: {field}")

    # Apply sorting
    if order_by:
        field_name = order_by.lstrip("-")
        if not hasattr(model, field_name):
            raise HTTPException(
                status_code=400, detail=f"Invalid order_by field: {field_name}")

        order_func = desc if order_by.startswith("-") else asc
        query = query.order_by(order_func(getattr(model, field_name)))

    return query


def get_key_types(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    order_by: Optional[str] = None,
    filters: Optional[dict] = None
) -> Sequence[KeyTypeSchema]:
    query = db.query(KeyType)
    query = apply_filters_and_sorting(query, KeyType, filters, order_by)
    query = query.offset(skip).limit(limit)

    try:
        db_key_types = query.all()
        return [KeyTypeSchema.model_validate(db_key_type) for db_key_type in db_key_types]
    except SQLAlchemyError:
        raise HTTPException(
            status_code=500, detail="Database error while retrieving key types.")

def get_key_type(db: Session, key_type_id: int) -> Optional[KeyTypeSchema]:
    # Retrieve a single KeyType model from the database
    db_key_type = db.query(KeyType).filter(KeyType.id == key_type_id).first()
    # Convert to KeyTypeSchema if the model exists
    return KeyTypeSchema.model_validate(db_key_type) if db_key_type else None


def create_key_type(db: Session, key_type: KeyTypeCreate) -> KeyTypeSchema:
    try:
        cryptoperiod_days = parse_cryptoperiod(key_type.cryptoperiod)

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


def update_key_type(db: Session, key_type_id: int, updates: dict[str, Any]) -> KeyTypeSchema:
    key_type = db.query(KeyType).filter(KeyType.id == key_type_id).first()

    if not key_type:
        raise HTTPException(status_code=404, detail="KeyType not found")

    for field, value in updates.items():
        if field == "cryptoperiod" and value is not None:
            # Convert cryptoperiod to days if provided
            key_type.cryptoperiod_days = parse_cryptoperiod(value)
        elif hasattr(key_type, field):
            setattr(key_type, field, value)

    try:
        db.commit()
        db.refresh(key_type)
        return KeyTypeSchema.model_validate(key_type)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error updating KeyType")


def delete_key_type(db: Session, key_type_id: int) -> KeyTypeSchema:
    key_type = db.query(KeyType).filter(KeyType.id == key_type_id).first()

    if not key_type:
        raise HTTPException(status_code=404, detail="KeyType not found")

    try:
        # Soft delete approach - you could also add an "is_deleted" field for tracking soft deletions
        db.delete(key_type)
        db.commit()
        return KeyTypeSchema.model_validate(key_type)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error deleting KeyType")


def get_crypto_keys(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    order_by: Optional[str] = None,
    filters: Optional[dict] = None
) -> Sequence[CryptoKeySchema]:
    query = db.query(CryptoKey)
    query = apply_filters_and_sorting(query, CryptoKey, filters, order_by)
    query = query.offset(skip).limit(limit)

    try:
        db_crypto_keys = query.all()
        return [CryptoKeySchema.model_validate(db_crypto_key) for db_crypto_key in db_crypto_keys]
    except SQLAlchemyError:
        raise HTTPException(
            status_code=500, detail="Database error while retrieving crypto keys.")

def get_crypto_key(db: Session, key_id: int) -> Optional[CryptoKeySchema]:
    # Retrieve a single CryptoKey model from the database
    db_crypto_key = db.query(CryptoKey).filter(CryptoKey.id == key_id).first()
    # Convert to CryptoKeySchema if the model exists
    return CryptoKeySchema.model_validate(db_crypto_key, strict=True, from_attributes=True) if db_crypto_key else None


def create_crypto_key(db: Session, crypto_key: CryptoKeyCreate) -> CryptoKeySchema:
    # Create a new CryptoKey model using input from the CryptoKeyCreate schema
    db_crypto_key = CryptoKey(**crypto_key.dict())
    db.add(db_crypto_key)
    db.commit()
    db.refresh(db_crypto_key)
    # Convert the database model to CryptoKeySchema for the response
    return CryptoKeySchema.model_validate(db_crypto_key)

def update_key_status(db: Session, key_id: int, new_status: KeyStatus) -> CryptoKeySchema:
    key = db.query(CryptoKey).filter(CryptoKey.id == key_id).first()

    if key is None:
        raise HTTPException(status_code=404, detail="Key not found")

    key.status = new_status
    db.commit()
    db.refresh(key)
    return CryptoKeySchema.model_validate(key)
