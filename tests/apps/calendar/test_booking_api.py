from datetime import date
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from appserver.apps.account.models import User
from appserver.apps.calendar.models import TimeSlot


@pytest.mark.usefixtures("host_user_calendar")
async def test_if_with_valid_reserv_request_create_reserv_response201(
    time_slot_tuesday: TimeSlot,
    host_user: User,
    client_with_auth: TestClient,
):
    target_date = date(2024, 12, 3)
    payload = {
        "when": target_date.isoformat(),
        "topic": "test",
        "description": "test",
        "time_slot_id": time_slot_tuesday.id,
    }

    response = client_with_auth.post(f"/bookings/{host_user.username}", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()

    assert data["when"] == target_date.isoformat()
    assert data["topic"] == "test"
    assert data["description"] == "test"
    assert data["time_slot"]["start_time"] == time_slot_tuesday.start_time.isoformat()
    assert data["time_slot"]["end_time"] == time_slot_tuesday.end_time.isoformat()
    assert data["time_slot"]["weekdays"] == time_slot_tuesday.weekdays


async def test_if_try_to_create_reserv_to_not_host_raise404(
    cute_guest_user: User,
    client_with_auth: TestClient,
    time_slot_tuesday: TimeSlot
):
    target_date = date(2024, 12, 3)
    payload = {
        "when": target_date.isoformat(),
        "topic": "test",
        "description": "test",
        "time_slot_id": time_slot_tuesday.id,
    }
    response = client_with_auth.post(f"/bookings/{cute_guest_user.username}", json=payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.parametrize(
    "time_slot_id_add, target_date",
    [
        (100, date(2024, 12, 3)),
        (0, date(2024, 12, 4)),
        (0, date(2024, 12, 5)),
    ],
)
@pytest.mark.usefixtures("host_user_calendar")
async def test_if_create_reserv_no_exist_time_raise404(
    host_user: User,
    client_with_guest_auth: TestClient,
    time_slot_tuesday: TimeSlot,
    time_slot_id_add: int,
    target_date: date,
):
    payload = {
        "when": target_date.isoformat(),
        "topic": "test",
        "description": "test",
        "time_slot_id": time_slot_tuesday.id + time_slot_id_add,
    }

    response = client_with_guest_auth.post(f"/bookings/{host_user.username}", json=payload)

    assert response.status_code == status.HTTP_404_NOT_FOUND
