# crud.py
from datetime import datetime, timezone
from sqlite3 import IntegrityError
from typing import Any, Optional, Sequence, Type

from fastapi import HTTPException
from sqlalchemy import asc, desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from models import CryptoKey, KeyStatus, KeyType, KeyTypeStatus
from schemas import CryptoKeyCreate, CryptoKeySchema, KeyTypeCreate, KeyTypeSchema
from utils import parse_cryptoperiod


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

def get_key_type_by_id(db: Session, key_type_id: int) -> Optional[KeyTypeSchema]:
    # Retrieve a single KeyType model from the database
    db_key_type = db.query(KeyType).filter(KeyType.id == key_type_id).first()
    # Convert to KeyTypeSchema if the model exists
    return KeyTypeSchema.model_validate(db_key_type) if db_key_type else None


def get_key_type_by_ulid(db: Session, key_type_id: str) -> Optional[KeyTypeSchema]:
    # Retrieve a single KeyType model from the database
    db_key_type = db.query(KeyType).filter(KeyType.key_id == key_type_id).first()
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


def update_key_type(db: Session, key_type_id: str, updates: dict[str, Any]) -> KeyTypeSchema:
    key_type = db.query(KeyType).filter(KeyType.key_id == key_type_id).first()

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


def delete_key_type(db: Session, key_type_id: str, force: bool = False) -> KeyTypeSchema:
    # Retrieve the KeyType
    key_type = db.query(KeyType).filter(
        KeyType.key_id == key_type_id, KeyType.status == KeyTypeStatus.ACTIVE).first()
    if not key_type:
        raise HTTPException(
            status_code=404, detail="KeyType not found or already disabled.")

    # Check for associated CryptoKeys that are not already marked as deleted
    associated_keys_count = db.query(CryptoKey).filter(
        CryptoKey.key_type_id == key_type_id, CryptoKey.status != KeyStatus.DESTROYED).count()

    # Standard deletion attempt (if force=False and there are associated keys, raise an error)
    if associated_keys_count > 0:
        if not force:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete KeyType with associated CryptoKeys. Use force=True to disable KeyType and soft delete associated keys."
            )
        else:
            # If force=True, perform cascading soft delete
            try:
                # Soft delete KeyType by updating its status to DISABLED
                key_type.status = KeyTypeStatus.DISABLED
                db.commit()

                # Soft delete all associated CryptoKeys by updating their status to DELETED
                db.query(CryptoKey).filter(CryptoKey.key_type_id == key_type.id).update(
                    {"status": KeyStatus.DESTROYED}
                )
                db.commit()
            except SQLAlchemyError as e:
                db.rollback()
                raise HTTPException(
                    status_code=500, detail=f"Error performing cascading soft delete: {str(e)}")
    else:
        # If no associated keys, proceed with a safe deletion
        try:
            # Soft delete KeyType by updating its status to DISABLED
            key_type.status = KeyTypeStatus.DISABLED
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Error deleting KeyType: {str(e)}")

    return KeyTypeSchema.model_validate(key_type)


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

def get_crypto_key(db: Session, key_id: str) -> Optional[CryptoKeySchema]:
    # Retrieve a single CryptoKey model from the database
    db_crypto_key = db.query(CryptoKey).filter(CryptoKey.key_id == key_id).first()
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

def create_key_version(
    db: Session,
    original_key: CryptoKey,
    new_status: KeyStatus
) -> CryptoKeySchema:
    # Create a new version of the CryptoKey record
    new_key_version = CryptoKey(
        key_type_id=original_key.key_type_id,
        description=original_key.description,
        generating_entity=original_key.generating_entity,
        generation_method=original_key.generation_method,
        storage_location=original_key.storage_location,
        encryption_under_lmk=original_key.encryption_under_lmk,
        form_factor=original_key.form_factor,
        scope_of_uniqueness=original_key.scope_of_uniqueness,
        usage_purpose=original_key.usage_purpose,
        operational_environment=original_key.operational_environment,
        associated_parties=original_key.associated_parties,
        intended_lifetime=original_key.intended_lifetime,
        status=new_status,
        rotation_or_expiration_date=original_key.rotation_or_expiration_date,
        access_control_mechanisms=original_key.access_control_mechanisms,
        compliance_requirements=original_key.compliance_requirements,
        audit_log_reference=original_key.audit_log_reference,
        backup_and_recovery_details=original_key.backup_and_recovery_details,
        notes=original_key.notes,
        activation_date=original_key.activation_date,
        # Track the creation date of this record
        record_creation_date=datetime.now(timezone.utc)
    )
    try:
        db.add(new_key_version)
        db.commit()
        db.refresh(new_key_version)
        return CryptoKeySchema.model_validate(new_key_version)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500, detail="Error creating new key version")


def update_key_status(db: Session, key_id: str, new_status: KeyStatus) -> CryptoKeySchema:
    # Find the latest record of the key
    original_key = (
        db.query(CryptoKey)
        .filter(CryptoKey.key_id == key_id)
        .order_by(CryptoKey.record_creation_date.desc())
        .first()
    )
    if not original_key:
        raise HTTPException(status_code=404, detail="Key not found")

    # Create a new record with the updated status
    return create_key_version(db, original_key, new_status)

def get_key_history(db: Session, key_id: str) -> list[CryptoKeySchema]:
    history = (
        db.query(CryptoKey)
        .filter(CryptoKey.key_id == key_id)
        .order_by(CryptoKey.record_creation_date)
        .all()
    )
    return [CryptoKeySchema.model_validate(record) for record in history]


def check_and_expire_keys(db: Session) -> None:
    """
    Checks for CryptoKeys with an expiration date in the past and marks them as expired.
    """
    # Get the current date and time
    now = datetime.now(timezone.utc)

    # Query all active or suspended keys with expiration dates in the past
    keys_to_expire = db.query(CryptoKey).filter(
        (CryptoKey.status.in_([KeyStatus.ACTIVE, KeyStatus.SUSPENDED])) &
        (CryptoKey.rotation_or_expiration_date <= now)
    ).all()

    for key in keys_to_expire:
        key.status = KeyStatus.EXPIRED

    # Commit the status updates to the database
    db.commit()
