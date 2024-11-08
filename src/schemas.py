# schemas.py
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from models import KeyStatus
from utils import parse_cryptoperiod


class KeyTypeBase(BaseModel):
    name: str
    description: str
    algorithm: str
    size_bits: int
    generated_by: str  # E.g., Acquirer, Vendor, etc.
    form_factor: str  # E.g., # Components, Encrypted, etc.
    uniqueness_scope: str  # Device, Acquirer, Vendor, etc.
    cryptoperiod: str  # Accept a user-friendly format like "30d", "6m", "1y"

    @field_validator("cryptoperiod")
    @classmethod
    def validate_cryptoperiod(cls, v: str) -> str:
        """Validate and parse cryptoperiod to ensure correct format."""
        parse_cryptoperiod(v)  # This will raise a ValueError if invalid
        return v


class KeyTypeCreate(KeyTypeBase):
    pass


class KeyTypeSchema(KeyTypeBase):
    id: int
    cryptoperiod_days: int

    class Config:
        from_attributes = True

class UpdateKeyType(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    algorithm: Optional[str] = None
    size_bits: Optional[int] = None
    generated_by: Optional[str] = None
    form_factor: Optional[str] = None
    uniqueness_scope: Optional[str] = None
    cryptoperiod: Optional[str] = None

    class Config:
        from_attributes = True


class CryptoKeyBase(BaseModel):
    key_type_id: int
    description: str
    generating_entity: str
    generation_method: str
    storage_location: str
    encryption_under_lmk: str
    form_factor: str
    scope_of_uniqueness: str
    usage_purpose: str
    operational_environment: str
    associated_parties: str
    intended_lifetime: str
    status: KeyStatus
    rotation_or_expiration_date: Optional[str] = None
    access_control_mechanisms: str
    compliance_requirements: str
    audit_log_reference: str
    backup_and_recovery_details: str
    notes: str


class CryptoKeyCreate(CryptoKeyBase):
    pass


class CryptoKeySchema(CryptoKeyBase):
    id: int
    activation_date: str
    record_creation_date: str = Field(
        ..., description="Date when this record was created for audit purposes")

    class Config:
        from_attributes = True


class KeyHistorySchema(BaseModel):
    id: int
    key_type_id: int
    status: KeyStatus
    record_creation_date: str
    description: str
    # Any other fields to show historical snapshots

    class Config:
        from_attributes = True
