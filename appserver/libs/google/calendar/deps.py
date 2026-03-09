import os
from typing import Annotated
from fastapi import Depends

from .services import GoogleCalendarService


def get_google_calendar_service(google_calendar_id: str | None = None) -> GoogleCalendarService | None:
    google_calendar_id = google_calendar_id or os.getenv("GOOGLE_CALENDAR_ID")
    if google_calendar_id is None:
        return None

    return GoogleCalendarService(google_calendar_id)


GoogleCalendarServiceDep = Annotated[GoogleCalendarService | None, Depends(get_google_calendar_service)]