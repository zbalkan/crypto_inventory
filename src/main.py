# main.py
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

import crud
import schemas
from database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.post("/crypto_keys/", response_model=schemas.CryptoKey)
def create_crypto_key(crypto_key: schemas.CryptoKeyCreate, db: Session = Depends(get_db)) -> crud.CryptoKey:
    return crud.create_crypto_key(db=db, crypto_key=crypto_key)

@app.get("/crypto_keys/", response_model=list[schemas.CryptoKey])
def read_crypto_keys(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)) -> list[crud.CryptoKey]:
    return crud.get_crypto_keys(db, skip=skip, limit=limit)

@app.get("/crypto_keys/{key_id}", response_model=schemas.CryptoKey)
def read_crypto_key(key_id: int, db: Session = Depends(get_db)) -> crud.CryptoKey:
    db_crypto_key = crud.get_crypto_key(db, key_id=key_id)
    if db_crypto_key is None:
        raise HTTPException(status_code=404, detail="Crypto key not found")
    return db_crypto_key

@app.put("/crypto_keys/{key_id}", response_model=schemas.CryptoKey)
def update_crypto_key(key_id: int, crypto_key: schemas.CryptoKeyCreate, db: Session = Depends(get_db)) -> crud.CryptoKey:
    db_crypto_key = crud.update_crypto_key(db=db, key_id=key_id, crypto_key=crypto_key)
    if db_crypto_key is None:
        raise HTTPException(status_code=404, detail="Crypto key not found")
    return db_crypto_key

@app.delete("/crypto_keys/{key_id}", response_model=schemas.CryptoKey)
def delete_crypto_key(key_id: int, db: Session = Depends(get_db)) -> crud.CryptoKey:
    db_crypto_key = crud.delete_crypto_key(db=db, key_id=key_id)
    if db_crypto_key is None:
        raise HTTPException(status_code=404, detail="Crypto key not found")
    return db_crypto_key
