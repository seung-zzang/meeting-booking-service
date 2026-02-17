import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from appserver.apps.account.models import User
from appserver.apps.calendar.models import Calendar
from appserver.apps.calendar.schemas import CalendarDetailOut, CalendarOut
from appserver.apps.calendar.endpoints import host_calendar_detail
from appserver.apps.calendar.exceptions import HostNotFoundError, CalendarNotFoundError

# 반복 제거
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
    guest_user: User,
    db_session: AsyncSession,
    ):
    
    users ={
        "host_user": host_user,  # 사용자가 호스트 자신
        "guest_user": guest_user,   # 사용자가 호스트 자신이 아님
        None: None,                 # 로그인 안 한 사용자
    }

    user = users[user_key]
    # user = None   # 삭제
    # expected_type = CalendarOut   # 삭제

    result = await host_calendar_detail(host_user.username, user, db_session)

    assert isinstance(result, expected_type)
    result_keys = frozenset(result.model_dump().keys())
    expected_keys = frozenset(expected_type.model_fields.keys())
    assert result_keys == expected_keys

    assert result.topics == host_user_calendar.topics
    assert result.description == host_user_calendar.description
    if isinstance(result, CalendarDetailOut):
        assert result.google_calendar_id == host_user_calendar.google_calendar_id

    # 삭제
    # user = guest_user
    # expected_type = CalendarOut

    # result = await host_calendar_detail(host_user.username, user, db_session)

    # assert isinstance(result, expected_type)
    # result_keys = frozenset(result.model_dump().keys())
    # expected_keys = frozenset(expected_type.model_fields.keys())
    # assert result_keys == expected_keys

    # assert result.topics == host_user_calendar.topics
    # assert result.description == host_user_calendar.description


    # user = host_user
    # expected_type = CalendarDetailOut

    # result = await host_calendar_detail(host_user.username, user, db_session)

    # assert isinstance(result, expected_type)
    # result_keys = frozenset(result.model_dump().keys())
    # expected_keys = frozenset(expected_type.model_fields.keys())
    # assert result_keys == expected_keys

    # assert result.topics == host_user_calendar.topics
    # assert result.description == host_user_calendar.description   


async def test_if_not_exist_user_search_calendar_info(db_session: AsyncSession,) -> None:
    with pytest.raises(HostNotFoundError):
        await host_calendar_detail("not_exist_user", None, db_session)

async def test_if_not_host_search_calendar_info(guest_user: User, db_session: AsyncSession) -> None:
    with pytest.raises(CalendarNotFoundError):
        await host_calendar_detail(guest_user.username, None, db_session)



