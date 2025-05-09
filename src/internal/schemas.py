# schemas.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, SerializationInfo, field_serializer, field_validator, model_validator

from .models import KeyStatus, KeyTypeStatus
from .utils import format_cryptoperiod, parse_cryptoperiod, validate_cryptoperiod_days


class KeyTypeBaseSchema(BaseModel):

    model_config = ConfigDict(use_enum_values=True,
                              from_attributes=True,
                              populate_by_name=True)

    name: str = Field(...,
                      max_length=100,
                      pattern=r"^[A-Za-z0-9\s]+$",
                      description="Name of the key type, alphanumeric and spaces only",
                      examples=[
                          "LMK", "BKAM", "BKEM", "CVK", "TMK", "PVK", "IBM PVK", "ZAK",
                          "ZMK", "ZPK", "EMV-ARK", "EMV-AWK", "MK-SMI", "MK-SMC", "MK-IDN",
                          "MK-DAC", "MK-AC", "RSA"
                      ])
    description: str = Field(...,
                             max_length=250,
                             description="Description of the key type",
                             examples=[
                                 "Local Master Key - stored in HSM, other keys are encrypted under LMK",
                                 "Transport key - MAC key", "PIN Verification Key, used for creating PIN verification data (PVV)",
                                 "Zone Master Key - used for exchanging other cryptographic keys (with banks)"
                             ])
    algorithm: str = Field(...,
                           max_length=50,
                           description="Algorithm used (e.g., AES, RSA)",
                           examples=["3DES", "AES", "RSA"])
    size_bits: int = Field(...,
                           ge=64,
                           le=4096,
                           description="Key size in bits, between 64 and 4096",
                           examples=[112, 128, 256, 1024, 2048, 4096])
    generated_by: str = Field(...,
                              max_length=100,
                              description="Entity that generated the key",
                              examples=["Payment Processor", "Acquirer", "Issuer"])
    form_factor: str = Field(...,
                             max_length=100,
                             description="Physical or logical form factor of the key",
                             examples=[
                                 "Loaded onto HSM in component form using smartcards",
                                 "Generated by HSM. Stored in database. Encrypted under LMK",
                                 "Loaded onto HSM in component form using paper-based components for card brand"
                             ])
    uniqueness_scope: str = Field(...,
                                  max_length=100,
                                  description="Scope of uniqueness (e.g., device, application)",
                                  examples=["Unique per logical configuration", "Unique per client", "Unique per device"])
    cryptoperiod: str = Field(...,
                              pattern=r"^\d+[dmy]$",
                              description="Cryptoperiod in format like '30d', '6m', '1y'",
                              examples=["1y", "6m", "30d"])

class KeyTypeCreateSchema(KeyTypeBaseSchema):

    @model_validator(mode="before")
    def parse_cryptoperiod_input(cls, values):
        if isinstance(values, dict):
            d = values
        else:
            d = values.__dict__
        cryptoperiod = d.get("cryptoperiod")
        if cryptoperiod:
            days = parse_cryptoperiod(cryptoperiod)
            validate_cryptoperiod_days(days)
        return values

class KeyTypeSchema(KeyTypeBaseSchema):

    model_config = ConfigDict(use_enum_values=True,
                              from_attributes=True,
                              populate_by_name=True)

    key_type_corr_id: str = Field(...,
                        description="ULID key identifier",
                        examples=["01F8MECHZX3TBDSZ7XRADM79XV"]
                        )
    cryptoperiod: str = Field(...,
                              description="User-friendly cryptoperiod format",
                              examples=["1y", "6m", "30d"])

    @model_validator(mode="before")
    def format_cryptoperiod_output(cls, values):
        if isinstance(values, dict):
            d = values
        else:
            d = values.__dict__

        if "cryptoperiod_days" in d:
            d['cryptoperiod'] = format_cryptoperiod(
                d['cryptoperiod_days'])
        return values


class KeyTypeDeleteSchema(BaseModel):

    model_config = ConfigDict(use_enum_values=True,
                              from_attributes=True,
                              populate_by_name=True)

    key_type_corr_id: str = Field(...,
                        description="ULID key identifier of the deleted KeyType")
    status: KeyTypeStatus = Field(
        ..., description="Status of the KeyType after deletion (e.g., Disabled)",
        examples=["Disabled"])

class CryptoKeyBaseSchema(BaseModel):

    model_config = ConfigDict(use_enum_values=True,
                              from_attributes=True,
                              populate_by_name=True)


    key_type_corr_id: str = Field(..., description="ULID of the associated KeyType")


    description: str = Field(
        ...,
        max_length=250,
        description="Description of the crypto key",
        examples=[
            "AES encryption key for payment transactions",
            "3DES key for cardholder verification data",
            "Transport key - MAC key for secure message authentication"
        ]
    )
    activation_date: Optional[datetime] = Field(
        None,
        description="The activation date of the key. Defaults to current date if not provided."
    )
    generating_entity: str = Field(
        ...,
        max_length=100,
        description="Entity responsible for generating the key",
        examples=["Payment Processor", "Issuer"]
    )
    generation_method: str = Field(
        ...,
        max_length=50,
        description="Method of key generation"
    )
    storage_location: str = Field(
        ...,
        max_length=100,
        description="Location where the key is stored"
    )
    encryption_under_lmk: str = Field(
        ...,
        max_length=50,
        description="LMK encryption status"
    )
    form_factor: str = Field(
        ...,
        max_length=100,
        description="Form factor (e.g., HSM, software)"
    )
    scope_of_uniqueness: str = Field(
        ...,
        max_length=100,
        description="Scope of uniqueness"
    )
    usage_purpose: str = Field(
        ...,
        max_length=100,
        description="Purpose for which the key is used"
    )
    operational_environment: str = Field(
        ...,
        max_length=100,
        description="Operational environment details"
    )
    associated_parties: str = Field(
        ...,
        max_length=250,
        description="Parties associated with this key"
    )
    access_control_mechanisms: str = Field(
        ...,
        max_length=250,
        description="Mechanisms to control access"
    )
    compliance_requirements: str = Field(
        ...,
        max_length=250,
        description="Compliance requirements"
    )
    audit_log_reference: str = Field(
        ...,
        max_length=100,
        description="Reference to audit logs"
    )
    backup_and_recovery_details: str = Field(
        ...,
        max_length=250,
        description="Backup and recovery procedures"
    )
    notes: str = Field(
        ...,
        max_length=500,
        description="Additional notes"
    )

    @field_serializer("activation_date", when_used="json")
    def serialize_activation_date(self, activation_date: datetime, info: SerializationInfo) -> str:
        return activation_date.isoformat()

    @model_validator(mode="after") # type: ignore
    def check_dates(cls, values: "CryptoKeyBaseSchema"):
        d = values.model_dump()

        activation_date = d.get("activation_date")
        rotation_date = d.get("expiration_date")
        if activation_date and rotation_date:
            if activation_date > rotation_date:
                raise ValueError(
                    "Activation date cannot be after expiration date.")
        return values

class CryptoKeyCreateSchema(BaseModel):

    model_config = ConfigDict(use_enum_values=True,
                              from_attributes=True,
                              populate_by_name=True)

    key_type_corr_id: str = Field(..., description="ULID of the associated KeyType")

    description: str = Field(
        ...,
        max_length=250,
        description="Description of the crypto key",
        examples=[
            "AES encryption key for payment transactions",
            "3DES key for cardholder verification data",
            "Transport key - MAC key for secure message authentication"
        ]
    )
    activation_date: Optional[datetime] = Field(
        None,
        description="The activation date of the key. Defaults to current date if not provided."
    )
    generating_entity: str = Field(
        ...,
        max_length=100,
        description="Entity responsible for generating the key",
        examples=["Payment Processor", "Issuer"]
    )
    generation_method: str = Field(
        ...,
        max_length=50,
        description="Method of key generation"
    )
    storage_location: str = Field(
        ...,
        max_length=100,
        description="Location where the key is stored"
    )
    encryption_under_lmk: str = Field(
        ...,
        max_length=50,
        description="LMK encryption status"
    )
    form_factor: str = Field(
        ...,
        max_length=100,
        description="Form factor (e.g., HSM, software)"
    )
    scope_of_uniqueness: str = Field(
        ...,
        max_length=100,
        description="Scope of uniqueness"
    )
    usage_purpose: str = Field(
        ...,
        max_length=100,
        description="Purpose for which the key is used"
    )
    operational_environment: str = Field(
        ...,
        max_length=100,
        description="Operational environment details"
    )
    associated_parties: str = Field(
        ...,
        max_length=250,
        description="Parties associated with this key"
    )
    access_control_mechanisms: str = Field(
        ...,
        max_length=250,
        description="Mechanisms to control access"
    )
    compliance_requirements: str = Field(
        ...,
        max_length=250,
        description="Compliance requirements"
    )
    audit_log_reference: str = Field(
        ...,
        max_length=100,
        description="Reference to audit logs"
    )
    backup_and_recovery_details: str = Field(
        ...,
        max_length=250,
        description="Backup and recovery procedures"
    )
    notes: str = Field(
        ...,
        max_length=500,
        description="Additional notes"
    )

    @field_serializer("activation_date", when_used="json")
    def serialize_activation_date(self, activation_date: datetime, info: SerializationInfo) -> str:
        return activation_date.isoformat()

class CryptoKeyUpdateSchema(BaseModel):

    model_config = ConfigDict(use_enum_values=True,
                              from_attributes=True,
                              populate_by_name=True)

    justification: Optional[str] = Field(None,
                                         description="Reason for status change",
                                         examples=["For new transaction encryption requirements"])

    @field_validator("justification", mode="before")
    def check_justification(cls, value, values):
        if values.get("status") != KeyStatus.EXPIRED and not value:
            raise ValueError(
                "Justification is required for status changes except for expiration.")
        return value

class CryptoKeySchema(CryptoKeyBaseSchema):

    key_type_corr_id: str = Field(..., description="ULID of the associated KeyType")


    key_corr_id: str = Field(...,
                        description="ULID unique identifier for the CryptoKey")
    status: KeyStatus = Field(
        ..., description="Current status of the key, defaults to 'Active' on creation")
    expiration_date: Optional[datetime] = Field(
        None, description="The rotation or expiration date of the key")
    intended_lifetime: str = Field(
        ..., description="Calculated lifetime based on KeyType's cryptoperiod", examples=["1y", "6m", "30d"])
    timestamp: datetime = Field(
        ..., description="Date when this record was created for audit purposes")

    # Inherits from CryptoKeyBase and includes additional fields for responses

    @field_serializer("timestamp", when_used="json")
    def serialize_timestamp(self, timestamp: datetime, info: SerializationInfo) -> str:
        return timestamp.isoformat()

    @field_serializer("expiration_date", when_used="json")
    def serialize_expiration_date(self, expiration_date: datetime, info: SerializationInfo) -> str:
        return expiration_date.isoformat()


class KeyHistorySchema(BaseModel):

    model_config = ConfigDict(use_enum_values=True,
                              from_attributes=True,
                              populate_by_name=True)

    id: str = Field(alias="key_corr_id")  # Expose `key_corr_id` as `id`
    status: KeyStatus
    timestamp: datetime
    description: str
    # Any other fields to show historical snapshots

    @field_serializer("timestamp", when_used="json")
    def serialize_timestamp(self, timestamp: datetime, info: SerializationInfo) -> str:
        return timestamp.isoformat()

