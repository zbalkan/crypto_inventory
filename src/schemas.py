# schemas.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from models import KeyStatus
from utils import format_cryptoperiod, parse_cryptoperiod


class KeyTypeBase(BaseModel):
    name: str = Field(..., max_length=100, pattern=r"^[A-Za-z0-9\s]+$",
                      description="Name of the key type, alphanumeric and spaces only")
    description: str = Field(..., max_length=250,
                             description="Description of the key type")
    algorithm: str = Field(..., max_length=50,
                           description="Algorithm used (e.g., AES, RSA)")
    size_bits: int = Field(..., ge=64, le=4096,
                           description="Key size in bits, between 64 and 4096")
    generated_by: str = Field(..., max_length=100,
                              description="Entity that generated the key")
    form_factor: str = Field(..., max_length=100,
                             description="Physical or logical form factor of the key")
    uniqueness_scope: str = Field(..., max_length=100,
                                  description="Scope of uniqueness (e.g., device, application)")
    cryptoperiod: str = Field(..., pattern=r"^\d+[dmy]$",
                              description="Cryptoperiod in format like '30d', '6m', '1y'")

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
    cryptoperiod: str = Field(..., description="User-friendly cryptoperiod format")

    @model_validator(mode="after")
    def format_cryptoperiod_output(cls, values):
        if "cryptoperiod" in values:
            values["cryptoperiod"] = format_cryptoperiod(values["cryptoperiod"])
        return values

    class Config:
        from_attributes = True

class UpdateKeyType(BaseModel):
    name: Optional[str] = Field(
        None, max_length=100, pattern=r"^[A-Za-z0-9\s]+$")
    description: Optional[str] = Field(None, max_length=250)
    algorithm: Optional[str] = Field(None, max_length=50)
    size_bits: Optional[int] = Field(None, ge=64, le=4096)
    generated_by: Optional[str] = Field(None, max_length=100)
    form_factor: Optional[str] = Field(None, max_length=100)
    uniqueness_scope: Optional[str] = Field(None, max_length=100)
    cryptoperiod: Optional[str] = Field(None, pattern=r"^\d+[dmy]$")

    class Config:
        from_attributes = True


class CryptoKeyBase(BaseModel):
    key_type_id: int
    description: str = Field(..., max_length=250,
                             description="Description of the crypto key")
    generating_entity: str = Field(..., max_length=100,
                                   description="Entity responsible for generating the key")
    generation_method: str = Field(..., max_length=50,
                                   description="Method of key generation")
    storage_location: str = Field(..., max_length=100,
                                  description="Location where the key is stored")
    encryption_under_lmk: str = Field(..., max_length=50,
                                      description="LMK encryption status")
    form_factor: str = Field(..., max_length=100,
                             description="Form factor (e.g., HSM, software)")
    scope_of_uniqueness: str = Field(..., max_length=100,
                                     description="Scope of uniqueness")
    usage_purpose: str = Field(..., max_length=100,
                               description="Purpose for which the key is used")
    operational_environment: str = Field(..., max_length=100,
                                         description="Operational environment details")
    associated_parties: str = Field(..., max_length=250,
                                    description="Parties associated with this key")
    intended_lifetime: str = Field(..., max_length=50,
                                   description="Intended lifetime (e.g., '5y')")
    status: KeyStatus
    activation_date: Optional[datetime] = Field(None, description="The activation date of the key")
    rotation_or_expiration_date: Optional[datetime] = Field(None, description="The rotation or expiration date of the key")
    access_control_mechanisms: str = Field(
        ..., max_length=250, description="Mechanisms to control access")
    compliance_requirements: str = Field(..., max_length=250,
                                         description="Compliance requirements")
    audit_log_reference: str = Field(..., max_length=100,
                                     description="Reference to audit logs")
    backup_and_recovery_details: str = Field(
        ..., max_length=250, description="Backup and recovery procedures")
    notes: str = Field(..., max_length=500, description="Additional notes")

    @model_validator(mode="after")
    def check_dates(cls, values):
        activation_date = values.get("activation_date")
        rotation_date = values.get("rotation_or_expiration_date")
        if activation_date and rotation_date:
            if activation_date > rotation_date:
                raise ValueError(
                    "Activation date cannot be after rotation/expiration date.")
        return values

class CryptoKeyCreate(CryptoKeyBase):
    pass


class CryptoKeySchema(CryptoKeyBase):
    id: str = Field(alias="key_id")  # Expose `key_id` as `id` in the response
    record_creation_date: datetime = Field(
        ..., description="Date when this record was created for audit purposes")


    class Config:
        from_attributes = True
        populate_by_name = True

class KeyHistorySchema(BaseModel):
    id: str = Field(alias="key_id")  # Expose `key_id` as `id`
    status: KeyStatus
    record_creation_date: str
    description: str
    # Any other fields to show historical snapshots

    class Config:
        from_attributes = True
        populate_by_name = True
