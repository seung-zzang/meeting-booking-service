import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from appserver.apps.account.endpoints import user_detail
from appserver.app import app
from appserver.apps.account.models import User
from appserver.apps.calendar.models import Calendar
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession
from appserver.db import create_async_engine, create_session


async def test_user_detail_for_real_user(client: TestClient, db_session: AsyncSession):
    user = User(
        username="test",
        password="test",
        email="test@example.com",
        display_name="test",
        is_host=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.flush()


    # test_user_detail_by_http와 test_user_detail_by_http_not_found 테스트 합쳐서 간소화
    # client = TestClient(app)

    response = client.get(f"/account/users/{user.username}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == user.username
    assert data["email"] == user.email
    assert data["display_name"] == user.display_name

    response = client.get("/account/users/not_found")
    assert response.status_code == status.HTTP_404_NOT_FOUND



