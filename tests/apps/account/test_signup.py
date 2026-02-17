from sqlalchemy.ext.asyncio import AsyncSession
from appserver.apps.account.endpoints import signup    # (1)
from appserver.apps.account.models import User
from appserver.apps.account.exceptions import DuplicatedUsernameError, DuplicatedEmailError
from fastapi.testclient import TestClient
import pytest
from pydantic import ValidationError

async def test_if_all_pass_create_account(client: TestClient, db_session: AsyncSession):    # (2)
    payload = {
        "username": "test",
        "email": "test@example.com",
        "display_name": "test",
        "password": "test테스트1234",
    }

    result = await signup(payload, db_session)  # (3)

    response = client.get(f"/account/users/{payload['username']}")

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == payload["username"]
    assert data["email"] == payload["email"]
    assert data["display_name"] == payload["display_name"]
    assert data["is_host"] is False


@pytest.mark.parametrize(
    "username",
    [
        "01234567890123456789012345678901234567890123456789",
        12345678,
        "x"
    ]
)

async def test_if_username_not_valid_raise_error(
    client: TestClient,
    db_session: AsyncSession,
    username: str
):
    payload = {
        "username": username,
        "email": "test@example.com",
        "display_name": "test",
        "password": "test테스트1234",
    }

    with pytest.raises(ValidationError) as exc:
        await signup(payload, db_session)


async def test_if_accuntid_was_duplicated_raise_error(db_session: AsyncSession):
    payload = {
        "username": "test",
        "email": "test@example.com",
        "display_name": "test",
        "password": "test테스트1234",
    }
    await signup(payload, db_session)   # (1)

    payload["email"] = "test2@example.com"  # (4)
    with pytest.raises(DuplicatedUsernameError) as exc: # (3)
            await signup(payload, db_session)


async def test_if_email_was_duplicated_raise_error(db_session: AsyncSession):
    payload = {
        "username": "test",
        "email": "test@example.com",
        "display_name": "test",
        "password": "test테스트1234",
    }
    await signup(payload, db_session)

    payload["username"] = "test2"
    with pytest.raises(DuplicatedEmailError):
        await signup(payload, db_session)


async def test_if_no_dpname_random_8word(db_session: AsyncSession):
    payload = {
        "username": "test",
        "email": "test@example.com",
        "password": "test테스트1234",
    }

    user = await signup(payload, db_session)
    assert isinstance(user.display_name, str)
    assert len(user.display_name) == 8

