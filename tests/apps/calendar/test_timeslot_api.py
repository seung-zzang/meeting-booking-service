from datetime import time
import pytest
from fastapi import status
from fastapi.testclient import TestClient
import calendar

@pytest.mark.usefixtures("host_user_calendar")
async def test_host_user_can_create_timeslot_with_valid_info(client_with_auth: TestClient,):
    payload = {
        "start_time": time(10, 0).isoformat(),
        "end_time": time(11, 0).isoformat(),
        "weekdays": [calendar.MONDAY, calendar.TUESDAY, calendar.WEDNESDAY],
    }

    response = client_with_auth.post("/time-slots", json=payload,)

    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.usefixtures("host_user_calendar")
async def test_if_try_to_create_timeslot_not_valid_info_raise422(client_with_auth: TestClient):
    payload = {
        "start_time": time(11, 0).isoformat(),
        "end_time": time(10, 0).isoformat(),
        "weekdays": [calendar.MONDAY, calendar.TUESDAY, calendar.WEDNESDAY],
    }

    response = client_with_auth.post("/time-slots", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize("weekdays", [
    [-1, 0, 1, 2, 3, 4, 5, 6],
    [1, 2, 3, 4, 5, 6, 7],
])
@pytest.mark.usefixtures("host_user_calendar")  # 데코레이터는 함수에서 가까운 곳 -> 먼 곳 순서로 실행됨
async def test_weekdays_start_mon_to_sun_start_from_0(
    client_with_auth: TestClient,
    weekdays: list[int],
):
    payload = {
        "start_time": time(10, 0).isoformat(),
        "end_time": time(11, 0).isoformat(),
        "weekdays": weekdays,
    }

    response = client_with_auth.post("/time-slots", json=payload)
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize("start_time, end_time, weekdays, expected_status_code", [
    # 겹치지 않는 경우
    (time(9, 0), time(10, 0), [calendar.MONDAY], status.HTTP_201_CREATED),
    (time(11, 0), time(12, 0), [calendar.MONDAY], status.HTTP_201_CREATED),
    (time(10, 0), time(11, 0), [calendar.THURSDAY], status.HTTP_201_CREATED),

    # 겹치는 경우(같은 요일)
    (time(10, 30), time(11, 30), [calendar.MONDAY], status.HTTP_422_UNPROCESSABLE_ENTITY),
    (time(9, 30), time(10, 30), [calendar.MONDAY], status.HTTP_422_UNPROCESSABLE_ENTITY),
    (time(10, 0), time(11, 0), [calendar.MONDAY], status.HTTP_422_UNPROCESSABLE_ENTITY),

    # 겹치지 않는 경우(다른 요일)
    (time(10, 0), time(11, 0), [calendar.THURSDAY], status.HTTP_201_CREATED),
    (time(10, 0), time(11, 0), [calendar.FRIDAY], status.HTTP_201_CREATED),
])
@pytest.mark.usefixtures("host_user_calendar")
async def test_if_duplicated_time_exist_raise422(
    client_with_auth: TestClient,
    start_time: time,
    end_time: time,
    weekdays: list[int],
    expected_status_code: int,
):
    # 첫 번째 타임슬롯 생성
    payload = {
        "start_time": time(10, 0).isoformat(),
        "end_time": time(11, 0).isoformat(),
        "weekdays": [calendar.MONDAY, calendar.TUESDAY, calendar.WEDNESDAY],
    }
    response = client_with_auth.post("/time-slots", json=payload)
    assert response.status_code == status.HTTP_201_CREATED

    # 두 번째 타임슬롯 생성
    payload = {
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "weekdays": weekdays,
    }
    response = client_with_auth.post("/time-slots", json=payload)
    assert response.status_code == expected_status_code