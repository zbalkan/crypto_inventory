# models.py
from datetime import datetime, timezone
from enum import Enum

import ulid
from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, relationship

from database import Base


class KeyTypeStatus(Enum):
    ACTIVE = "Active"
    DISABLED = "Disabled"


class KeyType(Base):
    __tablename__ = "key_types"


    id: Mapped[int] = Column(Integer, primary_key=True,
                         index=True)  # type: ignore
    key_id = Column(String, default=lambda: str(ulid.new()), unique=True, index=True)  # type: ignore
    name: Mapped[str] = Column(String, unique=True, index=True)  # type: ignore
    description: Mapped[str] = Column(String)  # type: ignore
    algorithm: Mapped[str] = Column(String)  # type: ignore
    size_bits: Mapped[int] = Column(Integer)  # type: ignore
    # E.g., Acquirer, Vendor, etc.
    generated_by: Mapped[str] = Column(String)  # type: ignore
    # E.g., # Components, Encrypted
    form_factor: Mapped[str] = Column(String)  # type: ignore
    # Device, Acquirer, Vendor, etc.
    uniqueness_scope: Mapped[str] = Column(String)  # type: ignore
    # Store cryptoperiod in days
    cryptoperiod_days: Mapped[int] = Column(Integer)  # type: ignore
    # Relationship with CryptoKey
    crypto_keys: Mapped[list["CryptoKey"]] = relationship(
        "CryptoKey", back_populates="key_type")  # type: ignore
    # Status field for soft deletion
    status: Mapped[KeyTypeStatus] = Column(SQLAlchemyEnum(KeyTypeStatus),
                                           default=KeyTypeStatus.ACTIVE)  # type: ignore

    crypto_keys = relationship("CryptoKey", back_populates="key_type")


class KeyStatus(Enum):
    """
    Active: Used to encrypt and decrypt data.
    Expired: Used only to decrypt data. Cannot be used to encrypt new data.
    Suspended: Temporarily disabled. Can be reactivated. Cannot be used to encrypt or decrypt data.
    Compromised: Used only to decrypt data of a compromised key. Cannot be used to encrypt new data.
    Destroyed: Historical reference to a key that no longer exists. Cannot be used to encrypt or decrypt data.
    """
    ACTIVE = "Active"
    EXPIRED = "Expired"
    COMPROMISED = "Compromised"
    SUSPENDED = "Suspended"
    DESTROYED = "Destroyed"


class CryptoKey(Base):
    __tablename__ = "crypto_keys"

    id: Mapped[int] = Column(Integer, primary_key=True,
                             index=True)  # type: ignore
    key_id = Column(String, unique=True, default=lambda: str(
        ulid.new()), index=True)  # ULID as unique identifier

    key_type_id: Mapped[int] = Column(
        Integer, ForeignKey("key_types.id"))  # type: ignore
    description: Mapped[str] = Column(String)  # type: ignore
    generating_entity: Mapped[str] = Column(String)  # type: ignore
    generation_method: Mapped[str] = Column(String)  # type: ignore
    storage_location: Mapped[str] = Column(String)  # type: ignore
    encryption_under_lmk: Mapped[str] = Column(String)  # type: ignore
    form_factor: Mapped[str] = Column(String)  # type: ignore
    scope_of_uniqueness: Mapped[str] = Column(String)  # type: ignore
    usage_purpose: Mapped[str] = Column(String)  # type: ignore
    operational_environment: Mapped[str] = Column(String)  # type: ignore
    associated_parties: Mapped[str] = Column(String)  # type: ignore
    activation_date: Mapped[datetime] = Column(
        DateTime, default=lambda: datetime.now(timezone.utc))  # type: ignore
    intended_lifetime: Mapped[str] = Column(String)  # type: ignore
    status: Mapped[KeyStatus] = Column(SQLAlchemyEnum(
        KeyStatus), default=KeyStatus.ACTIVE)  # type: ignore
    rotation_or_expiration_date: Mapped[datetime | None] = Column(
        DateTime, nullable=True)  # type: ignore
    access_control_mechanisms: Mapped[str] = Column(String)  # type: ignore
    compliance_requirements: Mapped[str] = Column(String)  # type: ignore
    audit_log_reference: Mapped[str] = Column(String)  # type: ignore
    backup_and_recovery_details: Mapped[str] = Column(String)  # type: ignore
    notes: Mapped[str] = Column(String)  # type: ignore
    justification: Mapped[str] = Column(String, nullable=False)  # type: ignore

    # Relationship with KeyType
    key_type: Mapped["KeyType"] = relationship(
        "KeyType", back_populates="crypto_keys")  # type: ignore


ALLOWED_TRANSITIONS = {
    KeyStatus.ACTIVE: {KeyStatus.SUSPENDED, KeyStatus.COMPROMISED, KeyStatus.EXPIRED},
    KeyStatus.SUSPENDED: {KeyStatus.ACTIVE, KeyStatus.EXPIRED, KeyStatus.DESTROYED},
    KeyStatus.COMPROMISED: {KeyStatus.DESTROYED},
    KeyStatus.EXPIRED: {KeyStatus.DESTROYED},
    KeyStatus.DESTROYED: set()  # No transitions allowed from Destroyed
}
