from ..crud import get_crypto_key_by_id, get_key_type_by_id
from ..models import KeyStatus


def test_get_key_type_by_id(test_db) -> None:
    # Given: A prepopulated database with a KeyType
    key_type_id = "01F8MECHZX3TBDSZ7XRADM79XV"

    # When: Retrieving the KeyType by ID
    result = get_key_type_by_id(test_db, key_type_id)

    # Then: The correct KeyType should be returned
    assert result is not None
    assert result.name == "Test KeyType"
    assert result.algorithm == "AES"


def test_get_crypto_key_by_id(test_db) -> None:
    # Given: A prepopulated database with a CryptoKey
    crypto_key_id = "01F8MECHZX3TBDSZ7XRADM79XV"

    # When: Retrieving the CryptoKey by ID
    result = get_crypto_key_by_id(test_db, crypto_key_id)

    # Then: The correct CryptoKey should be returned
    assert result is not None
    assert result.description == "Test CryptoKey"
    assert result.status == KeyStatus.ACTIVE
