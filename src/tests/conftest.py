import tempfile
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..database import Base
from ..models import CryptoKey, KeyStatus, KeyType


@pytest.fixture(scope="session")
def test_db():
    """
    Set up a file-based SQLite database for testing that persists throughout the test session.
    """
    # Create a temporary file for the SQLite database
    temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    engine = create_engine(f"sqlite:///{temp_db.name}")
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine)

    # Create tables
    Base.metadata.create_all(bind=engine)

    # Initialize session
    db = TestingSessionLocal()

    # Prepopulate the database with test data
    key_type = KeyType(
        key_type_corr_id="01F8MECHZX3TBDSZ7XRADM79XV",
        name="Test KeyType",
        description="A test key type",
        algorithm="AES",
        size_bits=256,
        generated_by="Test Generator",
        form_factor="HSM",
        uniqueness_scope="Test Scope",
        cryptoperiod_days=365,
    )
    crypto_key = CryptoKey(
        key_corr_id="01F8MECHZX3TBDSZ7XRADM79XV",
        key_type_corr_id="01F8MECHZX3TBDSZ7XRADM79XV",
        description="Test CryptoKey",
        generating_entity="Test Entity",
        generation_method="HSM",
        storage_location="Test Location",
        encryption_under_lmk="-",
        form_factor="HSM",
        scope_of_uniqueness="Test Scope",
        usage_purpose="Test Purpose",
        operational_environment="Test Env",
        associated_parties="Test Parties",
        activation_date=datetime.now(timezone.utc),
        intended_lifetime="1y",
        expiration_date=datetime.now(timezone.utc) + timedelta(days=365),
        status=KeyStatus.ACTIVE,
        access_control_mechanisms="Test Mechanisms",
        compliance_requirements="Test Compliance",
        audit_log_reference="Test Log",
        backup_and_recovery_details="Test Backup",
        notes="Test Notes",
        justification="Test Justification",
        timestamp=datetime.now(timezone.utc),
    )
    db.add(key_type)
    db.add(crypto_key)
    db.commit()

    yield db

    # Teardown: Drop tables and close the engine
    db.close()
    Base.metadata.drop_all(bind=engine)
    temp_db.close()
