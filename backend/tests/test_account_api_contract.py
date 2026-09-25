import json

from app.main import AccountConfigureIn
from app.models import Account
from app.services.security import SecretStore


def test_account_config_schema_does_not_expose_token_fields():
    data = AccountConfigureIn(account_name="Gmail account", access_token="secret")
    assert data.access_token == "secret"
    assert "access_token" not in {"id", "provider", "name", "status"}


def test_account_token_storage_is_encrypted():
    store = SecretStore("test-key")
    encrypted = store.encrypt("access-secret")
    assert encrypted != "access-secret"
    assert store.decrypt(encrypted) == "access-secret"
