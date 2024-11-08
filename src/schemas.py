# schemas.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CryptoKeyBase(BaseModel):
    key_type: str
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


class CryptoKey(CryptoKeyBase):
    id: int

    class Config:
        from_attributes = True
