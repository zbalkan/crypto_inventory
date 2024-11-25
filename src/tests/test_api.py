import pytest
from fastapi.testclient import TestClient

from ..app import app, get_db

# Override the get_db dependency with the test database session


@pytest.fixture(scope="function")
def override_get_db(test_db):
    """
    Override FastAPI's get_db dependency with the test database session.
    """
    def _override_get_db():
        yield test_db

    return _override_get_db


@pytest.fixture(scope="function")
def client(override_get_db):
    # Override FastAPI's get_db dependency
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_get_key_types(client) -> None:
    # When: Making a GET request to /key-types/
    response = client.get("/key-types/")

    # Then: The response should include the prepopulated KeyType
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test KeyType"


def test_get_crypto_keys(client) -> None:
    # When: Making a GET request to /keys/
    response = client.get("/keys/")

    # Then: The response should include the prepopulated CryptoKey
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["description"] == "Test CryptoKey"
