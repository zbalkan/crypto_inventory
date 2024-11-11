# crud.py
from datetime import datetime, timedelta, timezone
from sqlite3 import IntegrityError
from typing import Any, Optional, Sequence, Type

from fastapi import HTTPException
from sqlalchemy import asc, desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from models import ALLOWED_TRANSITIONS, CryptoKey, KeyStatus, KeyType, KeyTypeStatus
from schemas import CryptoKeyCreate, CryptoKeySchema, KeyTypeCreate, KeyTypeDeleteSchema, KeyTypeSchema
from utils import format_cryptoperiod, parse_cryptoperiod


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


def delete_key_type(db: Session, key_type_id: str, force: bool = False) -> KeyTypeDeleteSchema:
    key_type = db.query(KeyType).filter(
        KeyType.key_id == key_type_id, KeyType.status == KeyTypeStatus.ACTIVE).first()
    if not key_type:
        raise HTTPException(
            status_code=404, detail="KeyType not found or already disabled.")

    associated_keys_count = db.query(CryptoKey).filter(
        CryptoKey.key_type_id == key_type.id, CryptoKey.status != KeyStatus.DESTROYED).count()

    if associated_keys_count > 0:
        if not force:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete KeyType with associated CryptoKeys. Use force=True to disable KeyType and soft delete associated keys."
            )
        else:
            try:
                key_type.status = KeyTypeStatus.DISABLED
                db.commit()
                db.query(CryptoKey).filter(CryptoKey.key_type_id == key_type.id).update(
                    {"status": KeyStatus.DESTROYED}
                )
                db.commit()
            except SQLAlchemyError as e:
                db.rollback()
                raise HTTPException(
                    status_code=500, detail=f"Error performing cascading soft delete: {str(e)}")
    else:
        try:
            key_type.status = KeyTypeStatus.DISABLED
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Error deleting KeyType: {str(e)}")

    return KeyTypeDeleteSchema(key_id=key_type.key_id, status=key_type.status) # type: ignore


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
    db_crypto_key = CryptoKey(**crypto_key.model_dump())

    key_type = db.query(KeyType).filter(
        KeyType.id == crypto_key.key_type_id).first()
    if not key_type:
        raise HTTPException(status_code=404, detail="KeyType not found")

    # Calculate expiration date and intended lifetime based on KeyType's cryptoperiod
    activation_date = crypto_key.activation_date or datetime.now(timezone.utc)
    # Assuming cryptoperiod is stored as days in the KeyType
    cryptoperiod_days = key_type.cryptoperiod_days
    expiration_date = activation_date + timedelta(days=cryptoperiod_days)
    # Convert days to a readable format for lifetime
    intended_lifetime = format_cryptoperiod(cryptoperiod_days)

    db_crypto_key = CryptoKey(
        key_type_id=crypto_key.key_type_id,
        description=crypto_key.description,
        generating_entity=crypto_key.generating_entity,
        generation_method=crypto_key.generation_method,
        storage_location=crypto_key.storage_location,
        encryption_under_lmk=crypto_key.encryption_under_lmk,
        form_factor=crypto_key.form_factor,
        scope_of_uniqueness=crypto_key.scope_of_uniqueness,
        usage_purpose=crypto_key.usage_purpose,
        operational_environment=crypto_key.operational_environment,
        associated_parties=crypto_key.associated_parties,
        intended_lifetime=intended_lifetime,
        activation_date=activation_date,
        expiration_date=expiration_date,
        status=KeyStatus.ACTIVE,  # Default status on creation
        access_control_mechanisms=crypto_key.access_control_mechanisms,
        compliance_requirements=crypto_key.compliance_requirements,
        audit_log_reference=crypto_key.audit_log_reference,
        backup_and_recovery_details=crypto_key.backup_and_recovery_details,
        notes=crypto_key.notes,
        justification=crypto_key.usage_purpose,  # Default justification on creation
    )

    try:
        # Add and commit the new CryptoKey to the database
        db.add(db_crypto_key)
        db.commit()
        db.refresh(db_crypto_key)
        return CryptoKeySchema.model_validate(db_crypto_key)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create crypto key: {str(e)}")

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
        expiration_date=original_key.expiration_date,
        access_control_mechanisms=original_key.access_control_mechanisms,
        compliance_requirements=original_key.compliance_requirements,
        audit_log_reference=original_key.audit_log_reference,
        backup_and_recovery_details=original_key.backup_and_recovery_details,
        notes=original_key.notes,
        activation_date=original_key.activation_date,
        # Track the creation date of this record
        timestamp=datetime.now(timezone.utc)
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


def is_transition_valid(current_status: KeyStatus, new_status: KeyStatus) -> bool:
    """
    Check if the transition from current_status to new_status is valid.
    """
    return new_status in ALLOWED_TRANSITIONS[current_status]

def update_key_status(db: Session, key_id: str, new_status: KeyStatus, justification: str) -> CryptoKeySchema:
    # Find the latest record of the key
    original_key = (
        db.query(CryptoKey)
        .filter(CryptoKey.key_id == key_id)
        .order_by(CryptoKey.timestamp.desc())
        .first()
    )
    if not original_key:
        raise HTTPException(status_code=404, detail="Key not found")

     # Validate transition
    if not is_transition_valid(original_key.status, new_status):
        raise HTTPException(
            status_code=400,
            detail=f"Transition from {original_key.status.value} to {new_status.value} is not allowed."
        )

    if new_status != KeyStatus.EXPIRED and not justification:
        raise HTTPException(
            status_code=400,
            detail=f"Justification is required for this status change."
        )

    # Create a new record with the updated status
    return create_key_version(db, original_key, new_status)

def check_and_expire_keys(db: Session) -> None:
    """
    Checks for CryptoKeys with an expiration date in the past and marks them as expired.
    """
    # Get the current date and time
    now = datetime.now(timezone.utc)

    # Query all active or suspended keys with expiration dates in the past
    keys_to_expire = db.query(CryptoKey).filter(
        (CryptoKey.status.in_([KeyStatus.ACTIVE, KeyStatus.SUSPENDED])) &
        (CryptoKey.expiration_date <= now)
    ).all()

    for key in keys_to_expire:
        key.status = KeyStatus.EXPIRED
        key.justification = "Automatically expired due to expiration date"


    # Commit the status updates to the database
    db.commit()


def get_key_history(db: Session, key_id: str) -> list[CryptoKeySchema]:
    history = (
        db.query(CryptoKey)
        .filter(CryptoKey.key_id == key_id)
        .order_by(CryptoKey.timestamp)
        .all()
    )
    return [CryptoKeySchema.model_validate(record) for record in history]
