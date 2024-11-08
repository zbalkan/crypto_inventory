# schemas.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

from utils import format_cryptoperiod, parse_cryptoperiod


class KeyTypeBase(BaseModel):
    name: str
    description: str
    cryptoperiod: str  # Accept a user-friendly format like "6m" or "1y"

    @field_validator("cryptoperiod")
    @classmethod
    def validate_cryptoperiod(cls, v: str) -> str:
        """Validate and parse cryptoperiod to ensure correct format."""
        parse_cryptoperiod(v)  # This will raise a ValueError if invalid
        return v


class KeyTypeCreate(KeyTypeBase):
    pass


class KeyTypeSchema(KeyTypeBase):  # Renamed to avoid conflict
    id: int

    @property
    def cryptoperiod_days(self) -> int:
        """Converts the human-readable cryptoperiod to days."""
        return parse_cryptoperiod(self.cryptoperiod)

    class Config:
        from_attributes = True  # Use `from_attributes` instead of `orm_mode`


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
    activation_date: Optional[datetime] = None
    intended_lifetime: str
    status: str
    rotation_or_expiration_date: Optional[datetime] = None
    access_control_mechanisms: str
    compliance_requirements: str
    audit_log_reference: str
    backup_and_recovery_details: str
    notes: str


class CryptoKeyCreate(CryptoKeyBase):
    pass


class CryptoKeySchema(CryptoKeyBase):  # Renamed to avoid conflict
    id: int

    class Config:
        from_attributes = True  # Use `from_attributes` instead of `orm_mode`
