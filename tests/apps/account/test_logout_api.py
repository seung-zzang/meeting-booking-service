from fastapi.testclient import TestClient
from fastapi import status
from appserver.apps.account.constants import AUTH_TOKEN_COOKIE_NAME
from appserver.apps.account.models import User


async def test_if_logout_token_must_be_remove(client_with_auth: TestClient):
    response = client_with_auth.delete("/account/logout")
    assert response.status_code == status.HTTP_200_OK

    assert response.cookies.get(AUTH_TOKEN_COOKIE_NAME) is None