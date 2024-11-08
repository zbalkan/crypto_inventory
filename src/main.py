# main.py
from typing import Sequence

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import crud
import schemas
from database import Base, engine, get_db
from utils import format_cryptoperiod

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

@app.post("/keyTypes/", response_model=schemas.KeyTypeSchema)
def create_key_type(key_type: schemas.KeyTypeCreate, db: Session = Depends(get_db)) -> schemas.KeyTypeSchema:
    return crud.create_key_type(db=db, key_type=key_type)


@app.get("/keyTypes/", response_model=Sequence[schemas.KeyTypeSchema])
def read_key_types(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)) -> Sequence[schemas.KeyTypeSchema]:
    key_types = crud.get_key_types(db, skip=skip, limit=limit)
    # Format cryptoperiods for each returned KeyTypeSchema instance
    for key_type in key_types:
        key_type.cryptoperiod = format_cryptoperiod(key_type.cryptoperiod_days)
    return key_types


@app.get("/keyTypes/{key_type_id}", response_model=schemas.KeyTypeSchema)
def read_key_type(key_type_id: int, db: Session = Depends(get_db)) -> schemas.KeyTypeSchema:
    db_key_type = crud.get_key_type(db, key_type_id=key_type_id)
    if db_key_type is None:
        raise HTTPException(status_code=404, detail="KeyType not found")
    return db_key_type


@app.post("/keys/", response_model=schemas.CryptoKeySchema)
def create_crypto_key(crypto_key: schemas.CryptoKeyCreate, db: Session = Depends(get_db)) -> schemas.CryptoKeySchema:
    db_key_type = crud.get_key_type(db, key_type_id=crypto_key.key_type_id)
    if not db_key_type:
        raise HTTPException(status_code=400, detail="Invalid key_type_id")
    return crud.create_crypto_key(db=db, crypto_key=crypto_key)


@app.get("/keys/", response_model=Sequence[schemas.CryptoKeySchema])
def read_crypto_keys(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)) -> Sequence[schemas.CryptoKeySchema]:
    return crud.get_crypto_keys(db, skip=skip, limit=limit)


@app.get("/keys/{key_id}", response_model=schemas.CryptoKeySchema)
def read_crypto_key(key_id: int, db: Session = Depends(get_db)) -> schemas.CryptoKeySchema:
    db_crypto_key = crud.get_crypto_key(db, key_id=key_id)
    if db_crypto_key is None:
        raise HTTPException(status_code=404, detail="CryptoKey not found")
    return db_crypto_key
