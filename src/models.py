# models.py
import datetime

from sqlalchemy import Column, DateTime, Integer, String

from database import Base


class CryptoKey(Base):
    __tablename__ = "crypto_keys"

    id = Column(Integer, primary_key=True, index=True)
    key_type = Column(String, index=True)
    description = Column(String)
    generating_entity = Column(String)
    generation_method = Column(String)
    storage_location = Column(String)
    encryption_under_lmk = Column(String)
    form_factor = Column(String)
    scope_of_uniqueness = Column(String)
    usage_purpose = Column(String)
    operational_environment = Column(String)
    associated_parties = Column(String)
    activation_date = Column(DateTime, default=datetime.datetime.utcnow)
    intended_lifetime = Column(String)
    status = Column(String)
    rotation_or_expiration_date = Column(DateTime, nullable=True)
    access_control_mechanisms = Column(String)
    compliance_requirements = Column(String)
    audit_log_reference = Column(String)
    backup_and_recovery_details = Column(String)
    notes = Column(String)
