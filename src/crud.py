# crud.py
from typing import Optional

from sqlalchemy.orm import Session

from models import CryptoKey
from schemas import CryptoKeyCreate


def get_crypto_keys(db: Session, skip: int = 0, limit: int = 10) -> list[CryptoKey]:
    return db.query(CryptoKey).offset(skip).limit(limit).all() # type: ignore

def get_crypto_key(db: Session, key_id: int) -> Optional[CryptoKey]:
    return db.query(CryptoKey).filter(CryptoKey.id == key_id).first()

def create_crypto_key(db: Session, crypto_key: CryptoKeyCreate) -> CryptoKey:
    db_crypto_key = CryptoKey(**crypto_key.model_dump())
    db.add(db_crypto_key)
    db.commit()
    db.refresh(db_crypto_key)
    return db_crypto_key


def update_crypto_key(db: Session, key_id: int, crypto_key: CryptoKeyCreate) -> Optional[CryptoKey]:
    db_key = db.query(CryptoKey).filter(CryptoKey.id == key_id).first()
    if db_key:
        for key, value in crypto_key.model_dump().items():
            setattr(db_key, key, value)
        db.commit()
        db.refresh(db_key)
    return db_key

def delete_crypto_key(db: Session, key_id: int):
    db_key = db.query(CryptoKey).filter(CryptoKey.id == key_id).first()
    if db_key:
        db.delete(db_key)
        db.commit()
    return db_key
