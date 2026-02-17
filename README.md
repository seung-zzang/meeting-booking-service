# Meeting Booking Service

FastAPI 기반의 **약속/미팅 예약 서비스 API**입니다.  
호스트와 게스트 개념을 분리하여,  
호스트는 자신의 시간 슬롯을 공개하고  
게스트는 해당 슬롯에 약속을 예약할 수 있습니다.

---

## 🧩 Features

- 사용자 인증 (JWT + Cookie 기반)
- 호스트 / 게스트 권한 분리
- 호스트 캘린더 조회
  - 본인 조회 시: 상세 정보 제공
  - 타인 조회 시: 공개 정보만 제공
- Time Slot 기반 약속 예약 구조
- Async SQLAlchemy + SQLModel 사용
- pytest 기반 API 테스트 코드 포함

---

## 🛠 Tech Stack

- **Backend**: FastAPI
- **Language**: Python 3.13
- **ORM**: SQLModel, SQLAlchemy (Async)
- **Database**: SQLite (local), in-memory DB (tests)
- **Auth**: JWT (HttpOnly Cookie)
- **Migration**: Alembic
- **Test**: pytest, FastAPI TestClient
- **Version Control**: Git, GitHub