# main.py
from typing import Any, Optional, Sequence

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import crud
import schemas
from database import Base, engine, get_db
from models import KeyStatus

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Crypto Key Management API",
    description=(
        "This API provides endpoints for managing cryptographic keys and key types. "
        "It is designed to facilitate secure storage and management of cryptographic "
        "material, following industry standards such as PCI DSS. Key features include "
        "CRUD operations for managing key types, algorithms, cryptoperiods, and "
        "encryption configurations."
    ),
    version="1.0.0",
    terms_of_service="https://www.example.com/terms/",
    contact={
        "name": "API Support",
        "url": "https://www.example.com/support",
        "email": "support@example.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)

@app.exception_handler(IntegrityError)
async def handle_integrity_error(request: Request, exc: IntegrityError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"detail": "Database integrity error. This may be due to duplicate or invalid data."}
    )

# KeyType Operations
@app.post("/keyTypes/", response_model=schemas.KeyTypeSchema, summary="Create a new KeyType")
def create_key_type(key_type: schemas.KeyTypeCreate, db: Session = Depends(get_db)) -> schemas.KeyTypeSchema:
    """
    Create a new KeyType with specified details.

    - **key_type**: Details of the KeyType to be created.
    """
    return crud.create_key_type(db=db, key_type=key_type)


@app.get("/keyTypes/", response_model=Sequence[schemas.KeyTypeSchema], summary="List KeyTypes with optional filtering")
def read_key_types(
    skip: int = Query(0, alias="offset", ge=0, description="The number of records to skip."),
    limit: int = Query(10, le=100, description="The number of records to return, maximum 100."),
    order_by: Optional[str] = Query(
        None, description="Field to order by, prefix with - for descending."),
    name: Optional[str] = Query(None, description="Filter by name"),
    algorithm: Optional[str] = Query(None, description="Filter by algorithm"),
    size_bits: Optional[int] = Query(None, description="Filter by key size in bits"),
    db: Session = Depends(get_db),
) -> Sequence[schemas.KeyTypeSchema]:
    """
    Retrieve a list of KeyTypes with optional filtering, sorting, and pagination.

    - **offset**: The number of items to skip.
    - **limit**: The number of items to return.
    - **order_by**: Field to sort by, with "-" for descending order.
    - **name**: Filter by KeyType name.
    - **algorithm**: Filter by algorithm type.
    - **size_bits**: Filter by key size in bits.
    """
    filters: dict[str, Any] = {}
    if name is not None:
        filters["name"] = name
    if algorithm is not None:
        filters["algorithm"] = algorithm
    if size_bits is not None:
        filters["size_bits"] = size_bits

    result: Sequence[crud.KeyTypeSchema] = crud.get_key_types(
        db=db,
        skip=skip,
        limit=limit,
        order_by=order_by,
        filters=filters
    )

    return result

@app.get("/keyTypes/{keyTypeId}", response_model=schemas.KeyTypeSchema, summary="Retrieve a KeyType by ID")
def read_key_type(keyTypeId: int, db: Session = Depends(get_db)) -> schemas.KeyTypeSchema:
    """
    Retrieve a specific KeyType by its ID.

    - **keyTypeId**: The ID of the KeyType to retrieve.
    """
    db_key_type = crud.get_key_type(db, key_type_id=keyTypeId)
    if db_key_type is None:
        raise HTTPException(status_code=404, detail="KeyType not found")
    return db_key_type


@app.patch("/keyTypes/{keyTypeId}", response_model=schemas.KeyTypeSchema, summary="Update a KeyType by ID")
def update_key_type(
    keyTypeId: int,
    key_type_updates: schemas.UpdateKeyType,
    db: Session = Depends(get_db)
) -> schemas.KeyTypeSchema:
    """
    Update specific fields of a KeyType by its ID.

    - **keyTypeId**: The ID of the KeyType to update.
    - **key_type_updates**: The fields to update with new values.
    """
    updates = key_type_updates.dict(exclude_unset=True)
    return crud.update_key_type(db=db, key_type_id=keyTypeId, updates=updates)


@app.delete("/keyTypes/{keyTypeId}", response_model=schemas.KeyTypeSchema, summary="Delete or disable a KeyType")
def delete_key_type(keyTypeId: int, force: bool = Query(False, description="Set to true to disable the KeyType and delete associated keys"), db: Session = Depends(get_db)) -> schemas.KeyTypeSchema:
    """
    Mark a KeyType as Deleted. If there are keys with the associated KeyType, thow an error.
    If `force=True`, mark the KeyType and mark all associated keys as deleted.

    - **keyTypeId**: The ID of the KeyType to delete.
    - **force**: If true, marks the KeyType and deletes associated keys.
    """
    return crud.delete_key_type(db=db, key_type_id=keyTypeId, force=force)

# Key Operations
@app.post("/keys/", response_model=schemas.CryptoKeySchema, summary="Create a new CryptoKey")
def create_crypto_key(crypto_key: schemas.CryptoKeyCreate, db: Session = Depends(get_db)) -> schemas.CryptoKeySchema:
    """
    Create a new CryptoKey with specified details.

    - **crypto_key**: Details of the CryptoKey to create.
    """
    db_key_type = crud.get_key_type(db, key_type_id=crypto_key.key_type_id)
    if not db_key_type:
        raise HTTPException(status_code=400, detail="Invalid key_type_id")
    return crud.create_crypto_key(db=db, crypto_key=crypto_key)


@app.get("/keys/", response_model=Sequence[schemas.CryptoKeySchema], summary="List CryptoKeys with optional filtering")
def read_crypto_keys(
    skip: int = Query(0, alias="offset", ge=0, description="The number of records to skip."),
    limit: int = Query(10, le=100, description="The number of records to return, maximum 100."),
    order_by: Optional[str] = Query(
        None, description="Field to order by, prefix with - for descending."),
    key_type_id: Optional[int] = Query(None, description="Filter by key type ID"),
    description: Optional[str] = Query(None, description="Filter by description"),
    generating_entity: Optional[str] = Query(None, description="Filter by generating entity"),
    db: Session = Depends(get_db),
) -> Sequence[schemas.CryptoKeySchema]:
    """
    Retrieve a list of CryptoKeys with optional filtering, sorting, and pagination.

    - **offset**: The number of items to skip.
    - **limit**: The number of items to return.
    - **order_by**: Field to sort by, with "-" for descending order.
    - **key_type_id**: Filter by KeyType ID.
    - **description**: Filter by description.
    - **generating_entity**: Filter by generating entity.
    """
    filters: dict[str, Any] = {}
    if key_type_id is not None:
        filters["key_type_id"] = key_type_id
    if description is not None:
        filters["description"] = description
    if generating_entity is not None:
        filters["generating_entity"] = generating_entity

    result: Sequence[crud.CryptoKeySchema] = crud.get_crypto_keys(
        db=db,
        skip=skip,
        limit=limit,
        order_by=order_by,
        filters=filters
    )

    return result

@app.get("/keys/{key_id}", response_model=schemas.CryptoKeySchema, summary="Retrieve a CryptoKey by ID")
def read_crypto_key(key_id: str, db: Session = Depends(get_db)) -> schemas.CryptoKeySchema:
    """
    Retrieve a specific CryptoKey by its key_id.

    - **key_id**: The ID of the CryptoKey to retrieve.
    """
    db_crypto_key: Optional[schemas.CryptoKeySchema] = crud.get_crypto_key(
        db, key_id=key_id)
    if db_crypto_key is None:
        raise HTTPException(status_code=404, detail="CryptoKey not found")
    return db_crypto_key

# Key Status Transition Endpoints
@app.post("/keys/{key_id}/activate", summary="Activate a CryptoKey")
def activate_key(key_id: str, db: Session = Depends(get_db)):
    """
    Transition the status of a CryptoKey to "Current".

    - **key_id**: The ID of the CryptoKey to activate.
    """
    return crud.update_key_status(db, key_id, KeyStatus.CURRENT)


@app.post("/keys/{key_id}/retire", summary="Retire a CryptoKey")
def retire_key(key_id: str, db: Session = Depends(get_db)):
    """
    Transition the status of a CryptoKey to "Retired".

    - **key_id**: The ID of the CryptoKey to retire.
    """
    return crud.update_key_status(db, key_id, KeyStatus.RETIRED)


@app.post("/keys/{key_id}/expire", summary="Expire a CryptoKey")
def expire_key(key_id: str, db: Session = Depends(get_db)):
    """
    Transition the status of a CryptoKey to "Expired".

    - **key_id**: The ID of the CryptoKey to expire.
    """
    return crud.update_key_status(db, key_id, KeyStatus.EXPIRED)


@app.post("/keys/{key_id}/delete", summary="Delete a CryptoKey")
def delete_key(key_id: str, db: Session = Depends(get_db)) -> crud.CryptoKeySchema:
    """
    Soft delete a CryptoKey by marking its status as "Deleted".

    - **key_id**: The ID of the CryptoKey to delete.
    """
    return crud.update_key_status(db, key_id, KeyStatus.DELETED)


@app.get("/keys/{key_id}/history", response_model=list[schemas.KeyHistorySchema], summary="Retrieve CryptoKey history")
def get_key_history(key_id: str, db: Session = Depends(get_db)) -> list[schemas.CryptoKeySchema]:
    """
    Retrieve the history of state changes for a specific CryptoKey.

    - **key_id**: The ID of the CryptoKey whose history to retrieve.
    """
    history: list[schemas.CryptoKeySchema] = crud.get_key_history(
        db, key_id=key_id)
    if not history:
        raise HTTPException(
            status_code=404, detail="No history found for this key")
    return history
