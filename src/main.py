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

# Key type operations
@app.post("/keyTypes/", response_model=schemas.KeyTypeSchema)
def create_key_type(key_type: schemas.KeyTypeCreate, db: Session = Depends(get_db)) -> schemas.KeyTypeSchema:
    return crud.create_key_type(db=db, key_type=key_type)


@app.get("/keyTypes/", response_model=Sequence[schemas.KeyTypeSchema])
def read_key_types(
    skip: int = Query(0, alias="offset", ge=0),
    limit: int = Query(10, le=100),
    order_by: Optional[str] = Query(
        None, description="Field to order by, prefix with - for descending"),
    name: Optional[str] = None,
    algorithm: Optional[str] = None,
    size_bits: Optional[int] = None,
    db: Session = Depends(get_db),
) -> Sequence[schemas.KeyTypeSchema]:
    # Construct filters dictionary
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


@app.get("/keyTypes/{keyTypeId}", response_model=schemas.KeyTypeSchema)
def read_key_type(keyTypeId: int, db: Session = Depends(get_db)) -> schemas.KeyTypeSchema:
    db_key_type = crud.get_key_type(db, key_type_id=keyTypeId)
    if db_key_type is None:
        raise HTTPException(status_code=404, detail="KeyType not found")
    return db_key_type


@app.patch("/keyTypes/{keyTypeId}", response_model=schemas.KeyTypeSchema)
def update_key_type(
    keyTypeId: int,
    key_type_updates: schemas.UpdateKeyType,
    db: Session = Depends(get_db)
) -> schemas.KeyTypeSchema:
    updates = key_type_updates.dict(exclude_unset=True)
    return crud.update_key_type(db=db, key_type_id=keyTypeId, updates=updates)

# Delete KeyType (soft delete)
@app.delete("/keyTypes/{keyTypeId}", response_model=schemas.KeyTypeSchema)
def delete_key_type(keyTypeId: int, force: bool = Query(False), db: Session = Depends(get_db)) -> schemas.KeyTypeSchema:
    """
    Delete a KeyType. If `force=True`, disable the KeyType and mark all associated keys as deleted.
    """
    return crud.delete_key_type(db=db, key_type_id=keyTypeId, force=force)

# Key operations
@app.post("/keys/", response_model=schemas.CryptoKeySchema)
def create_crypto_key(crypto_key: schemas.CryptoKeyCreate, db: Session = Depends(get_db)) -> schemas.CryptoKeySchema:
    db_key_type = crud.get_key_type(db, key_type_id=crypto_key.key_type_id)
    if not db_key_type:
        raise HTTPException(status_code=400, detail="Invalid key_type_id")
    return crud.create_crypto_key(db=db, crypto_key=crypto_key)


@app.get("/keys/", response_model=Sequence[schemas.CryptoKeySchema])
def read_crypto_keys(
    skip: int = Query(0, alias="offset", ge=0),
    limit: int = Query(10, le=100),
    order_by: Optional[str] = Query(
        None, description="Field to order by, prefix with - for descending"),
    key_type_id: Optional[int] = None,
    description: Optional[str] = None,
    generating_entity: Optional[str] = None,
    db: Session = Depends(get_db),
) -> Sequence[schemas.CryptoKeySchema]:
    # Construct filters dictionary
    filters:dict[str, Any] = {}
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


@app.get("/keys/{key_id}", response_model=schemas.CryptoKeySchema)
def read_crypto_key(key_id: str, db: Session = Depends(get_db)) -> schemas.CryptoKeySchema:
    db_crypto_key: Optional[schemas.CryptoKeySchema] = crud.get_crypto_key(
        db, key_id=key_id)
    if db_crypto_key is None:
        raise HTTPException(status_code=404, detail="CryptoKey not found")
    return db_crypto_key

# Endpoint to transition key to "Current"


@app.post("/keys/{key_id}/activate")
def activate_key(key_id: str, db: Session = Depends(get_db)):
    key: crud.CryptoKeySchema = crud.update_key_status(
        db, key_id, KeyStatus.CURRENT)
    return key

# Endpoint to transition key to "Retired"


@app.post("/keys/{key_id}/retire")
def retire_key(key_id: str, db: Session = Depends(get_db)):
    key: crud.CryptoKeySchema = crud.update_key_status(
        db, key_id, KeyStatus.RETIRED)
    return key

# Endpoint to transition key to "Expired"


@app.post("/keys/{key_id}/expire")
def expire_key(key_id: str, db: Session = Depends(get_db)):
    key: crud.CryptoKeySchema = crud.update_key_status(
        db, key_id, KeyStatus.EXPIRED)
    return key

# Endpoint to transition key to "Deleted"


@app.post("/keys/{key_id}/delete")
def delete_key(key_id: str, db: Session = Depends(get_db)) -> crud.CryptoKeySchema:
    key: crud.CryptoKeySchema = crud.update_key_status(db, key_id, KeyStatus.DELETED)
    return key


@app.get("/keys/{key_id}/history", response_model=list[schemas.KeyHistorySchema])
def get_key_history(key_id: str, db: Session = Depends(get_db)) -> list[schemas.CryptoKeySchema]:
    history: list[schemas.CryptoKeySchema] = crud.get_key_history(
        db, key_id=key_id)
    if not history:
        raise HTTPException(
            status_code=404, detail="No history found for this key")
    return history
