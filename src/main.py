# main.py
from contextlib import asynccontextmanager
from typing import Any, Optional, Sequence

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi_utils.tasks import repeat_every
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import crud
import schemas
from database import Base, engine, get_db
from models import KeyStatus

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    This function manages the startup and periodic tasks in FastAPI.
    """

    # Run the expiration check immediately on startup
    db = next(get_db())
    crud.check_and_expire_keys(db)

    # Schedule the periodic task to run every hour
    @repeat_every(seconds=3600)  # 3600 seconds = 1 hour
    async def scheduled_expiration_check() -> None:
        """
        This task runs every hour to check for keys that need to be expired.
        """
        db = next(get_db())
        crud.check_and_expire_keys(db)

    # Yield to start the application
    yield

app = FastAPI(
    title="Crypto Key Inventory Management API",
    description=(
        "This API provides endpoints for managing cryptographic keys and key types. "
        "It is designed to tracn the inventory of cryptographic "
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
    lifespan=lifespan,
)

@app.exception_handler(IntegrityError)
async def handle_integrity_error(request: Request, exc: IntegrityError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"detail": "Database integrity error. This may be due to duplicate or invalid data."}
    )

# KeyType Operations
@app.get("/key-types/", response_model=Sequence[schemas.KeyTypeSchema], summary="List KeyTypes")
def get_key_types(
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
    Get a list of KeyTypes with optional filtering, sorting, and pagination.

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

@app.get("/key-types/{id}", response_model=schemas.KeyTypeSchema, summary="Get a KeyType by ID")
def get_key_type(id: str, db: Session = Depends(get_db)) -> schemas.KeyTypeSchema:
    """
    Get a specific KeyType by its ID.

    - **id**: The ID of the KeyType to retrieve.
    """
    db_key_type = crud.get_key_type_by_ulid(db, key_type_id=id)
    if db_key_type is None:
        raise HTTPException(status_code=404, detail="KeyType not found")
    return db_key_type


@app.post("/key-types/", response_model=schemas.KeyTypeSchema, summary="Create a new KeyType")
def create_key_type(key_type: schemas.KeyTypeCreate, db: Session = Depends(get_db)) -> schemas.KeyTypeSchema:
    """
    Create a new KeyType with specified details.

    - **key_type**: Details of the KeyType to be created.
    """
    return crud.create_key_type(db=db, key_type=key_type)


@app.delete("/key-types/{id}", response_model=schemas.KeyTypeDeleteSchema, summary="Delete a KeyType")
def delete_key_type(id: str,
                    force: bool = Query(False,
                                                        description="Set to true to force the KeyType and delete associated keys"),
                                                        db: Session = Depends(get_db)) -> schemas.KeyTypeDeleteSchema:
    """
    Mark a KeyType as Deleted. If there are keys with the associated KeyType, thow an error.
    If `force=True`, mark the KeyType and mark all associated keys as deleted.

    - **id**: The ID of the KeyType to delete.
    - **force**: If true, marks the KeyType and deletes associated keys.
    """
    return crud.delete_key_type(db=db, key_type_id=id, force=force)

# Key Operations
@app.get("/keys/", response_model=Sequence[schemas.CryptoKeySchema], summary="List CryptoKeys")
def get_crypto_keys(
    skip: int = Query(0, alias="offset", ge=0, description="The number of records to skip."),
    limit: int = Query(10, le=100, description="The number of records to return, maximum 100."),
    order_by: Optional[str] = Query(
        None, description="Field to order by, prefix with - for descending."),
    key_type_id: Optional[str] = Query(None, description="Filter by key type ID"),
    description: Optional[str] = Query(None, description="Filter by description"),
    generating_entity: Optional[str] = Query(None, description="Filter by generating entity"),
    db: Session = Depends(get_db),
) -> Sequence[schemas.CryptoKeySchema]:
    """
    Get a list of CryptoKeys with optional filtering, sorting, and pagination.

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

@app.get("/keys/{id}", response_model=schemas.CryptoKeySchema, summary="Get a CryptoKey by ID")
def get_crypto_key(id: str, db: Session = Depends(get_db)) -> schemas.CryptoKeySchema:
    """
    Get a specific CryptoKey by its id.

    - **id**: The ID of the CryptoKey to retrieve.
    """
    db_crypto_key: Optional[schemas.CryptoKeySchema] = crud.get_crypto_key(db, id)
    if db_crypto_key is None:
        raise HTTPException(status_code=404, detail="CryptoKey not found")
    return db_crypto_key

@app.post("/keys/", response_model=schemas.CryptoKeyCreate, summary="Create a new CryptoKey")
def create_crypto_key(crypto_key: schemas.CryptoKeyCreate, db: Session = Depends(get_db)) -> schemas.CryptoKeySchema:
    """
    Create a new CryptoKey with specified details.
    Status: Active (Used to encrypt and decrypt data.)

    - **crypto_key**: Details of the CryptoKey to create.
    """
    db_key_type = crud.get_key_type_by_id(
        db, key_type_id=crypto_key.key_type_id)
    if not db_key_type:
        raise HTTPException(status_code=400, detail="Invalid key_type_id")
    return crud.create_crypto_key(db=db, crypto_key=crypto_key)

@app.post("/keys/{id}/suspend", summary="Suspend a CryptoKey")
def suspend_key(id: str, justification: str, db: Session = Depends(get_db)) -> crud.CryptoKeySchema:
    """
    Transition the status of a CryptoKey to "Suspended".
    Status: Suspended (Temporarily disabled. Can be reactivated. Cannot be used to encrypt or decrypt data.)

    - **id**: The ID of the CryptoKey to suspend.
    """
    return crud.update_key_status(db, id, KeyStatus.SUSPENDED, justification)

@app.post("/keys/{id}/revoke", summary="Revoke a CryptoKey")
def revoke_key(id: str, justification: str, db: Session = Depends(get_db)) -> crud.CryptoKeySchema:
    """
    Transition the status of a CryptoKey to "Compromised".
    Status: Compromised (Used only to decrypt data of a compromised key. Cannot be used to encrypt new data.)
    - **id**: The ID of the CryptoKey to revoke.
    """
    return crud.update_key_status(db, id, KeyStatus.COMPROMISED, justification)


@app.post("/keys/{id}/destroy", summary="Destroy a CryptoKey")
def destroy_key(id: str, justification: str, db: Session = Depends(get_db)) -> crud.CryptoKeySchema:
    """
    Transition the status of a CryptoKey to  "Destroyed".
    Status: Destroyed (Historical reference to a key that no longer exists. Cannot be used to encrypt or decrypt data.)

    - **id**: The ID of the CryptoKey to destroy.
    """
    return crud.update_key_status(db, id, KeyStatus.DESTROYED, justification)

# Key History Operations
@app.get("/keys/{id}/history", response_model=list[schemas.KeyHistorySchema], summary="Get CryptoKey history")
def get_key_history(id: str, db: Session = Depends(get_db)) -> list[schemas.CryptoKeySchema]:
    """
    Get the history of state changes for a specific CryptoKey.

    - **id**: The ID of the CryptoKey whose history to retrieve.
    """
    history: list[schemas.CryptoKeySchema] = crud.get_key_history(db, id)
    if not history:
        raise HTTPException(
            status_code=404, detail="No history found for this key")
    return history
