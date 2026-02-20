from datetime import date
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from appserver.apps.account.models import User
from appserver.apps.calendar.models import TimeSlot, Booking
from appserver.apps.calendar.schemas import BookingOut
from appserver.apps.calendar.enums import AttendanceStatus
from pytest_lazy_fixtures import lf



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


@pytest.mark.usefixtures("charming_host_bookings")
async def test_host_receive_reserv_list_by_page(
    client_with_auth: TestClient,
    host_bookings: list[Booking],
):
    response = client_with_auth.get("/bookings", params={"page":1, "page_size":10})

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == len(host_bookings)


@pytest.mark.parametrize(
    "year, month",
    [(2024, 12), (2025, 1)],
)
@pytest.mark.usefixtures("charming_host_bookings")
async def test_guest_receive_reserv_list_by_month(
    client_with_guest_auth: TestClient,
    host_bookings: list[Booking],
    host_user: User,
    year: int,
    month:int,
):
    params = {
        "year":year,
        "month":month,
    }
    response = client_with_guest_auth.get(f"/calendar/{host_user.username}/bookings", params=params,)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    booking_dates = frozenset([
        booking.when.isoformat()
        for booking in host_bookings
        if booking.when.year == params["year"] and booking.when.month == params["month"]
    ])

    assert not not data
    assert len(data) == len(booking_dates)
    assert all([item["when"] in booking_dates for item in data])


async def test_guest_receive_reserv_list_by_page(
    client_with_guest_auth: TestClient,
    host_bookings: list[Booking],
    charming_host_bookings: list[Booking]
):
    response = client_with_guest_auth.get("/guest-calendar/bookings", params={"page":1, "page_size":50})

    assert response.status_code == status.HTTP_200_OK

    id_set = frozenset([booking.id for booking in host_bookings] + [booking.id for booking in charming_host_bookings])

    data = response.json()
    assert len(data) == len(id_set)
    assert all([item['id'] in id_set for item in data])


async def test_user_receive_specific_reserv_data(
    host_bookings: list[Booking],
    client_with_guest_auth: TestClient,
    client_with_smart_guest_auth: TestClient,
):
    response = client_with_smart_guest_auth.get(f"/bookings/{host_bookings[0].id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND

    response = client_with_guest_auth.get(f"/bookings/{host_bookings[0].id}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == host_bookings[0].id


@pytest.mark.parametrize(
    "client, expected_status_code",
    [
        (lf("client_with_guest_auth"), status.HTTP_200_OK),
        (lf("client_with_smart_guest_auth"), status.HTTP_404_NOT_FOUND),
    ],
)
async def test_user_receive_specific_reserv_data_final(
    host_bookings: list[Booking],
    client: TestClient,
    expected_status_code: int,
):
    response = client.get(f"/bookings/{host_bookings[0].id}")

    assert response.status_code == expected_status_code

    data = response.json()
    if expected_status_code == status.HTTP_200_OK:
        assert data["id"] == host_bookings[0].id


@pytest.mark.parametrize(
    "payload",
    [
        {"when": "2025-01-01", "time_slot": lf("time_slot_tuesday")},
        {"when": "2025-01-02", "time_slot": lf("time_slot_monday")},
    ],
)
@pytest.mark.usefixtures("host_user_calendar")
async def test_host_can_change_their_timeslot_that_booked_them(
    payload: dict,
    client_with_auth: TestClient,
    host_bookings: list[Booking],
):
    hooking = host_bookings[0]
    time_slot: TimeSlot = payload["time_slot"]
    payload["time_slot_id"] = time_slot.id
    del payload["time_slot"]

    response = client_with_auth.patch(f"/bookings/{hooking.id}", json=payload)

    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["when"] == payload["when"]
    assert data["time_slot"]["start_time"] == time_slot.start_time.isoformat()
    assert data["time_slot"]["end_time"] == time_slot.end_time.isoformat()
    assert data["time_slot"]["weekdays"] == time_slot.weekdays


@pytest.mark.parametrize(
    "time_slot, expected_status_code",
    [
        (lf("time_slot_friday"), status.HTTP_404_NOT_FOUND),
        (lf("time_slot_tuesday"), status.HTTP_200_OK)
    ],
)
async def test_host_cannot_change_another_hosts_timeslot(
    client_with_auth: TestClient,
    host_bookings: list[Booking],
    time_slot: TimeSlot,
    expected_status_code: int,
):
    response = client_with_auth.patch(
        f"/bookings/{host_bookings[0].id}",
        json={"time_slot_id": time_slot.id},
    )
    assert response.status_code == expected_status_code


@pytest.mark.parametrize(
    "time_slot, expected_status_code",
    [
        (lf("time_slot_friday"), status.HTTP_404_NOT_FOUND),
        (lf("time_slot_tuesday"), status.HTTP_200_OK),
    ],
)
async def test_guest_cannot_change_another_hosts_timeslot(
    client_with_guest_auth: TestClient,
    host_bookings: list[Booking],
    time_slot: TimeSlot,
    expected_status_code: int,
):
    response = client_with_guest_auth.patch(
        f"/guest-bookings/{host_bookings[0].id}",
        json={"time_slot_id": time_slot.id}
    )
    assert response.status_code == expected_status_code


@pytest.mark.parametrize(
    "payload",
    [
        {"topic": "test", "description": "test", "when": "2025-01-01", "time_slot": lf("time_slot_tuesday")},
        {"topic": "test", "description": "test", "when": "2025-01-02", "time_slot": lf("time_slot_monday")},
        {"description": "test", "when": "2025-01-12"}
    ],
)
async def test_guest_can_change_their_booking_info(
    client_with_guest_auth: TestClient,
    host_bookings: list[Booking],
    payload: dict
):
    booking = host_bookings[0]

    # 변경 전 데이터 추출
    before_booking = BookingOut.model_validate(
        booking,
        from_attributes=True
    ).model_dump(mode="json")

    # 변경 가능한 필드 설정
    updatable_fields = set(["topic", "description", "when", "time_slot"])
    exceptable_fields = updatable_fields - set(payload.keys())

    # 타임슬롯 처리
    if time_slot := payload.pop("time_slot", None):
        time_slot: TimeSlot
        payload["time_slot_id"] = time_slot.id
    else:
        time_slot = None
        payload["time_slot_id"] = None

    # 요청 보내기
    response = client_with_guest_auth.patch(
        f"/guest-bookings/{booking.id}",
        json=payload
    )

    # 응답 검증
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # 변경된 필드 검증
    for field, value in payload.items():
        if field == "time_slot_id" and time_slot:
            assert data["time_slot"]["start_time"] == time_slot.start_time.isoformat()
            assert data["time_slot"]["end_time"] == time_slot.end_time.isoformat()
            assert data["time_slot"]["weekdays"] == time_slot.weekdays
        else:
            assert payload[field] == value

    # 변경되지 않는 필드 검증
    for field_name in exceptable_fields:
        if field_name == "time_slot":
            assert before_booking["time_slot"]["start_time"] == data["time_slot"]["start_time"]
            assert before_booking["time_slot"]["end_time"] == data["time_slot"]["end_time"]
            assert before_booking["time_slot"]["weekdays"] == data["time_slot"]["weekdays"]
        else:
            assert before_booking[field_name] == data[field_name]


@pytest.mark.parametrize(
    "attendance_status",
    [
        (AttendanceStatus.SCHEDULED),
        (AttendanceStatus.ATTENDED),
        (AttendanceStatus.NO_SHOW),
        (AttendanceStatus.CANCELLED),
        (AttendanceStatus.SAME_DAY_CANCEL),
        (AttendanceStatus.LATE),
    ],
)
async def test_host_can_change_booking_attendance_status_that_applied_to_them(
    client_with_auth: TestClient,
    host_bookings: list[Booking],
    attendance_status: AttendanceStatus,
):
    payload = {
        "attendance_status": attendance_status
    }
    booking = host_bookings[-1]
    response = client_with_auth.patch(f"/bookings/{booking.id}/status", json=payload)

    assert response.status_code == status.HTTP_200_OK

    response = client_with_auth.get(f"/bookings/{booking.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["attendance_status"] == attendance_status.value
