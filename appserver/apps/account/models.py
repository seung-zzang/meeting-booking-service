from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship, Text, JSON, func, String, Column
from pydantic import EmailStr, model_validator
from pydantic import AwareDatetime
from sqlalchemy import UniqueConstraint
from sqlalchemy_utc import UtcDateTime
from typing import TYPE_CHECKING
import random, string

if TYPE_CHECKING:
    from appserver.apps.calendar.models import Calendar
    from appserver.apps.calendar.models import Booking


class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_email"),
    )

    id: int = Field(default=None, primary_key=True)
    username: str = Field(unique=True, min_length=4, max_length=40, description="사용자 계정 ID")
    email: EmailStr = Field(unique=True, max_length=128, description="사용자 이메일")
    display_name: str = Field(min_length=4,max_length=40, description="사용자 표시 이름")
    hashed_password: str = Field(min_length=8,max_length=128, description="사용자 비밀번호")
    is_host: bool = Field(default=False, description="사용자가 호스트인지 여부")

    # 반대로 User를 가리키는 OAuthAccount를 가져오려면
    oauth_accounts: list["OAuthAccount"] = Relationship(back_populates="user")

    calendar: "Calendar" = Relationship(
        back_populates="host",
        sa_relationship_kwargs={"uselist":False, "single_parent":True, "lazy": "joined"},
    )

    bookings: list["Booking"] = Relationship(back_populates="guest")
    
    # created/updated_at 수정
    created_at: AwareDatetime = Field(
        default=None,
        nullable=False,
        sa_type=UtcDateTime,
        sa_column_kwargs={
            "server_default": func.now(),
        },
    )

    updated_at: AwareDatetime = Field(
        default=None,
        nullable=False,
        sa_type=UtcDateTime,
        sa_column_kwargs={
            "server_default": func.now(),
            "onupdate": lambda: datetime.now(timezone.utc),
        },
    )



class OAuthAccount(SQLModel, table=True):
    __tablename__ = "oauth_accounts"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "provider_account_id",
            name="uq_provider_provider_account__id",
        ),
    )

    id: int = Field(default=None, primary_key=True)

    provider: str = Field(max_length=10, description="OAuth 제공자")
    provider_account_id: str = Field(max_length=128, description="OAuth 제공자 계정 ID")

    # OAuthAccount에서 User에 접근
    user_id: int = Field(foreign_key="users.id")
    # user: User = Relationship()
    
    # 반대로 User를 가리키는 OAuthAccount도 가져오려면
    user: "User" = Relationship(back_populates="oauth_accounts")

    created_at: AwareDatetime = Field(
        default=None,
        nullable=False,
        sa_type=UtcDateTime,
        sa_column_kwargs={
            "server_default": func.now(),
        },
    )

    updated_at: AwareDatetime = Field(
        default=None,
        nullable=False,
        sa_type=UtcDateTime,
        sa_column_kwargs={
            "server_default": func.now(),
            "onupdate": lambda: datetime.now(timezone.utc),
        },
    )

# # ORM의 관게 접근을 사용하지 않는 경우
# stmt = select(OAuthAccount).where(OAuthAccount.id == 299792458)
# result =session.execute(stmt)
# oauth_user = result.scalar_one()

# stmt = select(User).where(User.id == oauth_user.user_id)
# result =session.execute(stmt)
# user = result.scalar_one()
# oauth_user.user = user


# ORM의 관계 접근을 사용하는 경우
# stmt = select(OAuthAccount).where(OAuthAccount.id == 299792458)
# result = session.execute(stmt)
# oauth_user = result.scalar_one()

# user = oauth_user.user



 