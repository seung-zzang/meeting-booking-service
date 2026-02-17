from fastapi import status
from fastapi.testclient import TestClient
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from appserver.apps.account.models import User
from appserver.apps.calendar.models import Calendar
from appserver.apps.calendar.schemas import CalendarDetailOut, CalendarOut
from appserver.apps.calendar.endpoints import host_calendar_detail
from appserver.apps.calendar.exceptions import HostNotFoundError, CalendarNotFoundError
from appserver.libs.collections.sort import deduplicate_and_sort


@pytest.mark.parametrize("user_key, expected_type", [
    ("host_user", CalendarDetailOut),
    ("guest_user", CalendarOut),
    (None, CalendarOut),
])
async def test_use_host_username_calendar_info(
    user_key: str | None,   # 추가
    expected_type: type[CalendarOut | CalendarDetailOut],   # 추가
    host_user: User,
    host_user_calendar: Calendar,
    client: TestClient,
    client_with_auth: TestClient
    ) -> CalendarOut | CalendarDetailOut:
    
    clients ={
        "host_user": client_with_auth,  # 사용자가 호스트 자신
        "guest_user": client,   # 사용자가 호스트 자신이 아님
        None: client,                 # 로그인 안 한 사용자
    }

    user_client = clients[user_key]

    response = user_client.get(f"/calendar/{host_user.username}")
    result = response.json()
    assert response.status_code == status.HTTP_200_OK

    expected_obj = expected_type.model_validate(result)

    assert expected_obj.topics == host_user_calendar.topics
    assert expected_obj.description == host_user_calendar.description
    if isinstance(expected_obj, CalendarDetailOut):
        assert expected_obj.google_calendar_id == host_user_calendar.google_calendar_id


async def test_not_exist_user_try_search_calendar_info_raise404(client: TestClient,) -> None:
    response = client.get("/calendar/not_exist_user")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_if_not_host_search_calendar_info_raise404(guest_user: User, client: TestClient) -> None:
    response = client.get(f"/calendar/{guest_user.username}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_host_can_create_cal_with_right_info(host_user: User, client_with_auth: TestClient) -> None:
    google_calendar_id = "valid_google_calendar_id@group.calendar.google.com"
    payload = {
        "topics": ["topic2", "topic1", "topic2"],
        "description": "description",
        "google_calendar_id": google_calendar_id,
    }

    response = client_with_auth.post("/calendar", json=payload)

    assert response.status_code == status.HTTP_201_CREATED

    result = response.json()
    assert result["host_id"] == host_user.id
    assert result["topics"] == ["topic2", "topic1"]
    assert result["description"] == payload["description"]
    assert result["google_calendar_id"] == payload["google_calendar_id"]


async def test_if_cal_exist_try_to_add_cal_raise_422(client_with_auth: TestClient,) -> None:
    google_calendar_id = "valid_google_calendar_id@group.calendar.google.com"

    payload = {
        "topics": ["topic2", "topic1", "topic2"],
        "description": "description",
        "google_calendar_id": google_calendar_id,
    }

    response = client_with_auth.post("/calendar", json=payload)
    assert response.status_code == status.HTTP_201_CREATED

    response = client_with_auth.post("/calendar", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_if_guest_try_to_create_cl_raise_422(client_with_guest_auth: TestClient) -> None:
    google_calendar_id = "valid_google_calendar_id@group.calendar.google.com"

    payload ={
        "topics": ["topic2", "topic1", "topic2"],
        "description": "description",
        "google_calendar_id": google_calendar_id,
    }

    response = client_with_guest_auth.post("/calendar", json=payload)
    assert response.status_code == status.HTTP_403_FORBIDDEN


UPDATABLE_FIELDS = frozenset(["topics", "description", "google_calendar_id"])

@pytest.mark.parametrize("payload", [
    {"topics": ["topic2", "topic1", "topic2"]},
    {"description": "문자열 길이가 10자 이상인 설명입니다."},
    {"google_calendar_id": "invalid_google_calendar_id@group.calendar.google.com"},
])
async def test_user_change_list_change_remains_stay(
    client_with_auth: TestClient,
    host_user_calendar: Calendar,
    payload: dict,
) -> None:
    before_data = host_user_calendar.model_dump()

    response = client_with_auth.patch("/calendar", json=payload)
    assert response.status_code == status.HTTP_200_OK

    response = client_with_auth.get(f"/calendar/{host_user_calendar.host.username}")
    data = response.json()

    # 변경된 항목은 변경된 값으로 변경되어야 한다
    for key, value in payload.items():
        if key == "topics":
            assert data[key] == deduplicate_and_sort(value)
        else:
            assert data[key] == value

    # 변경되지 않은 항목은 기존 값을 유지한다
    for key in UPDATABLE_FIELDS - frozenset(payload.keys()):
        assert data[key] == before_data[key]

