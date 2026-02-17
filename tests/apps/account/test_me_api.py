from fastapi import status
from fastapi.testclient import TestClient
from appserver.apps.account.models import User
from appserver.apps.account.utils import decode_token, create_access_token
from datetime import datetime, timedelta, timezone

def test_search_my_info(client_with_auth: TestClient, host_user: User):
    response = client_with_auth.get("/account/@me")

    data = response.json()
    assert response.status_code == status.HTTP_200_OK

    response_keys = frozenset(data.keys())
    expected_keys = frozenset(["username","display_name", "is_host", "email", "created_at", "updated_at"])
    assert response_keys == expected_keys


def test_if_not_have_token_raise_suspicious_error(client: TestClient):
    response = client.get("/account/@me")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_invalid_token_raise_authenication_error(client_with_auth):
    client_with_auth._cookies["auth_token"] = "invalid_token"
    response = client_with_auth.get("/account/@me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_expired_token_search_my_info(client_with_auth: TestClient):
    token = client_with_auth.cookies.get("auth_token", domain="", path="/")
    decoded = decode_token(token)
    jwt = create_access_token(decoded, timedelta(hours=-1))
    client_with_auth.cookies["auth_token"] = jwt

    response = client_with_auth.get("/account/@me")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_user_not_exist_search_my_info(client_with_auth: TestClient):
    token = client_with_auth.cookies.get("auth_token", domain="", path="/")
    decoded = decode_token(token)
    decoded["sub"] = "invalid_user_id"
    jwt = create_access_token(decoded)
    client_with_auth.cookies["auth_token"] = jwt

    response = client_with_auth.get("/account/@me")
    assert response.status_code == status.HTTP_404_NOT_FOUND