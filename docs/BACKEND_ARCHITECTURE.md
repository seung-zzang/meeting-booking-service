# Puddingcamp 백엔드 아키텍처 상세 문서

프론트엔드를 제외한 **데이터 모델링 → API → 라이브러리 → 배포**까지 전체 백엔드를 파일·함수·데이터 관계·기능 단위로 설명합니다.

---

## 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [진입점과 앱 구성](#2-진입점과-앱-구성)
3. [데이터베이스 계층](#3-데이터베이스-계층)
4. [데이터 모델 상세](#4-데이터-모델-상세)
5. [마이그레이션 (Alembic)](#5-마이그레이션-alembic)
6. [계정(Account) 앱](#6-계정account-앱)
7. [캘린더(Calendar) 앱](#7-캘린더calendar-앱)
8. [공용 라이브러리 (libs)](#8-공용-라이브러리-libs)
9. [관리자 (SQLAdmin)](#9-관리자-sqladmin)
10. [배포 (CI/CD)](#10-배포-cicd)

---

## 1. 프로젝트 개요

- **역할**: 호스트-게스트 미팅 예약 서비스 (캘린더·타임슬롯·부킹·Google Calendar 연동).
- **스택**: FastAPI, SQLModel(SQLAlchemy), Alembic, JWT+쿠키 인증, SQLAdmin, Sentry.
- **DB**: 로컬 기본값 `sqlite+aiosqlite`, 운영은 `RDS PostgreSQL` (`DATABASE_URL` / `RDS_DATABASE_URL`).
- **실행**: `uvicorn appserver.app:app` (또는 FastAPI CLI). Dockerfile은 저장소에 없음.

---

## 2. 진입점과 앱 구성

### 2.1 `appserver/app.py`

- **FastAPI 앱 생성** 후:
  - **라우터 등록**: `account_router` (prefix `/account`), `calendar_router` (prefix 없음).
  - **정적 마운트**: `/static` → `static/`, `/uploads` → `uploads/`.
  - **미들웨어**: CORS만 사용. `allow_origins=["*"]`, `allow_credentials=True`, 모든 메서드/헤더 허용.
- **헬스체크**: `GET /health` → `{"status": "ok"}`.
- **SQLAdmin**: `Admin(..., base_url="/seungzzang/admin/", authentication_backend=AdminAuthentication("secret-key"))` 로 초기화 후 `include_admin_views(admin)` 호출.
- **Sentry**: `init_sentry(os.getenv("SENTRY_DSN", "기본 DSN"))` — 실패 트랜잭션은 403, 5xx, GET/POST/DELETE/PUT/PATCH 캡처.

### 2.2 `appserver/db.py`

- **DSN**: `os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./local.db")`.
- **create_engine(dsn)**: `create_async_engine(dsn, echo=False)` 반환.
- **create_session(engine)**: `async_sessionmaker(..., expire_on_commit=False, autoflush=False, class_=AsyncSession)`.
- **전역**: `engine = create_engine()`, `async_session_factory = create_session(engine)`.
- **use_session()**: `async_session_factory()` 컨텍스트 매니저로 세션 yield.
- **DbSessionDep**: `Annotated[AsyncSession, Depends(use_session)]` — 라우트에서 주입용.

---

## 3. 데이터베이스 계층

- **접속**: `appserver/db.py`의 `DSN` 한 곳에서만 설정. Alembic은 `appserver.db.DSN`을 사용.
- **비동기**: 모든 DB 접근은 `AsyncSession` + async/await.
- **타임존**: `sqlalchemy_utc.UtcDateTime` + `server_default=func.now()`, `onupdate` 에서 UTC 기준 갱신.

---

## 4. 데이터 모델 상세

### 4.1 계정 앱 — `appserver/apps/account/models.py`

#### User (테이블: `users`)

| 필드 | 타입 | 설명 |
|------|------|------|
| id | int, PK | 자동 증가 |
| username | str, 4~40, unique | 로그인/계정 ID |
| email | EmailStr, 128, unique (uq_email) | 이메일 |
| display_name | str, 4~40 | 표시 이름 |
| hashed_password | str, 8~128 | Argon2/Bcrypt 해시 |
| is_host | bool, default False | 호스트 여부 (캘린더 소유 가능) |
| status | AccountStatus (String) | active / withdrawal / suspended / deleted |
| created_at, updated_at | UtcDateTime | 생성/수정 시각 |

- **관계**:
  - `oauth_accounts`: 1:N → `OAuthAccount` (lazy noload).
  - `calendar`: 1:1 → `Calendar` (host 쪽, lazy joined, single_parent).
  - `bookings`: 1:N → `Booking` (guest 쪽, lazy noload).
- **하이브리드 속성**:
  - `is_active`: `status in [ACTIVE]` (인스턴스/식 표현 둘 다).
  - `is_deleted`: `status == DELETED` (동일).

#### OAuthAccount (테이블: `oauth_accounts`)

| 필드 | 타입 | 설명 |
|------|------|------|
| id | int, PK | |
| provider | str, 10 | OAuth 제공자 |
| provider_account_id | str, 128 | 제공자 측 계정 ID |
| user_id | int, FK → users.id | 소유 User |
| created_at, updated_at | UtcDateTime | |

- **유니크**: `(provider, provider_account_id)` — `uq_provider_provider_account_id`.
- **관계**: `user` → `User` (lazy noload).

#### AccountStatus (enum) — `apps/account/enums.py`

- `ACTIVE`, `WITHDRAWAL`, `SUSPENDED`, `DELETED`.

---

### 4.2 캘린더 앱 — `appserver/apps/calendar/models.py`

#### Calendar (테이블: `calendars`)

| 필드 | 타입 | 설명 |
|------|------|------|
| id | int, PK | |
| topics | list[str], JSON/JSONB | 게스트와 나눌 주제 목록. PostgreSQL은 JSONB |
| description | Text | 게스트용 설명 |
| google_calendar_id | str, 1024 | Google Calendar ID |
| host_id | int, FK → users.id, unique | 호스트 1인당 캘린더 1개 |
| created_at, updated_at | UtcDateTime | |

- **관계**: `host` → User (joined), `time_slots` → TimeSlot (noload).

#### TimeSlot (테이블: `time_slots`)

| 필드 | 타입 | 설명 |
|------|------|------|
| id | int, PK | |
| start_time, end_time | time | 해당 요일 내 시간 구간 |
| weekdays | list[int], JSON/JSONB | 0=월 … 6=일, 예약 가능 요일 |
| calendar_id | int, FK → calendars.id | 소속 캘린더 |
| created_at, updated_at | UtcDateTime | |

- **관계**: `calendar` → Calendar (joined), `bookings` → Booking (noload).

#### Booking (테이블: `bookings`)

| 필드 | 타입 | 설명 |
|------|------|------|
| id | int, PK | |
| when | date | 예약 날짜 |
| topic | str | 주제 |
| description | Text | 설명 |
| attendance_status | AttendanceStatus (String) | SCHEDULED / ATTENDED / NO_SHOW / CANCELLED / SAME_DAY_CANCEL / LATE |
| time_slot_id | int, FK → time_slots.id | 시간대 |
| guest_id | int, FK → users.id | 게스트(예약자) |
| google_event_id | str, 64, nullable | Google Calendar 이벤트 ID (연동 시) |
| created_at, updated_at | UtcDateTime | |

- **관계**: `time_slot` → TimeSlot (joined), `guest` → User (joined), `files` → BookingFile (joined).
- **computed_field**: `host` → `self.time_slot.calendar.host` (호스트 User).

#### BookingFile (테이블: `booking_files`)

| 필드 | 타입 | 설명 |
|------|------|------|
| id | int, PK | |
| booking_id | int, FK → bookings.id | 소속 예약 |
| file | FileType(FileSystemStorage("uploads/bookings")) | 실제 파일 저장 |

- **관계**: `booking` → Booking (noload).

#### AttendanceStatus (enum) — `apps/calendar/enums.py`

- `SCHEDULED`, `ATTENDED`, `NO_SHOW`, `CANCELLED`, `SAME_DAY_CANCEL`, `LATE` (StrEnum, auto 값).

---

### 4.3 엔티티 관계 요약

```
User 1 ──< OAuthAccount
User 1 ──1 Calendar (host)
User 1 ──< Booking (guest)
Calendar 1 ──< TimeSlot
TimeSlot 1 ──< Booking
Booking 1 ──< BookingFile
```

- 호스트: `User.is_host=True` 이고 `Calendar` 1개 소유. 해당 캘린더의 `TimeSlot`으로 예약 받음.
- 게스트: `Booking`으로 특정 호스트의 `TimeSlot`에 예약. 필요 시 `BookingFile` 첨부.

---

## 5. 마이그레이션 (Alembic)

### 5.1 설정 — `alembic.ini`

- `script_location = alembic`, `prepend_sys_path = .`. DB URL은 ini가 아니라 `env.py`에서 `appserver.db.DSN` 사용.

### 5.2 env.py

- **타겟 메타데이터**: `SQLModel.metadata`.
- **모델 임포트**: `appserver.apps.account.models`, `appserver.apps.calendar.models` (autogenerate 반영).
- **온라인 마이그레이션**: `configuration["sqlalchemy.url"] = DSN` 설정 후 `async_engine_from_config`로 엔진 생성, `run_sync(do_run_migrations)` 로 동기 방식으로 마이그레이션 실행.

### 5.3 마이그레이션 체인

| Revision | 파일 | 내용 |
|----------|------|------|
| bf8351584432 | auto_generate_migration | users, calendars, oauth_accounts, time_slots, bookings 초기 테이블. users에는 password 컬럼(이후 hashed_password로 변경). |
| ceb387862674 | bookingfile_model | booking_files 테이블 생성, bookings.attendance_status 추가, users.password → hashed_password 변경 |
| 7184714be38b | add_account_status | users.status 추가, default ACTIVE |
| 78e0d09a8756 | google_event_id | bookings.google_event_id nullable 컬럼 추가 |

- 적용: `alembic upgrade head`. 배포 시 서버에서 이 명령으로 스키마 동기화.

---

## 6. 계정(Account) 앱

### 6.1 라우터 prefix

- `/account`.

### 6.2 엔드포인트 — `apps/account/endpoints.py`

| 메서드 | 경로 | 인증 | 동작 |
|--------|------|------|------|
| GET | /account/users/{username} | 없음 | username으로 User 조회, 없으면 404. |
| POST | /account/signup | 없음 | SignupPayload 검증 → username 중복 체크 → User 생성(비밀번호 해시) → IntegrityError 시 이메일 중복 422. |
| POST | /account/login | 없음 | LoginPayload → User 조회 → 비밀번호 검증 → JWT 생성 → 쿠키 `auth_token` 설정 + JSON { access_token, token_type, user }. |
| GET | /account/@me | 필수 | CurrentUserDep → 로그인 사용자 상세 (UserDetailOut). |
| PATCH | /account/@me | 필수 | UpdateUserPayload로 사용자 정보 일부 수정 (DB update). |
| DELETE | /account/logout | 필수 | 쿠키 삭제 후 200. |
| DELETE | /account/unregister | 필수 | 해당 User 행 delete. |
| GET | /account/hosts | 필수 | is_active & is_host 인 User 목록 (UserOut). |

### 6.3 인증 의존성 — `apps/account/deps.py`

- **get_user(auth_token, db_session)**  
  - 토큰 없으면 None.  
  - `decode_token` 실패 시 InvalidTokenError.  
  - exp와 현재 시각 비교해 만료 시 ExpiredTokenError.  
  - `decoded["sub"]`로 User 조회 후 반환.
- **get_current_user(request, db_session)**  
  - 토큰 소스: `request.cookies.get("auth_token") or request.headers.get("Authorization")`.  
  - Authorization이면 `"Bearer <token>"` 형태로 가정하고 `split(" ")` 후 마지막 요소를 토큰으로 사용.  
  - User 없으면 UserNotFoundError.
- **CurrentUserDep**: `Annotated[User, Depends(get_current_user)]`.
- **get_current_user_optional**: 쿠키만 사용, 없으면 None 반환. **CurrentUserOptionalDep**.

(참고: 토큰이 전혀 없을 때 `raw_auth_token.split(" ")` 호출 시 None.split으로 예외가 날 수 있음. 호출 경로는 인증 필수 라우트이므로 보통 토큰이 있지만, 경계 케이스에서는 방어 코드 고려 가능.)

### 6.4 유틸 — `apps/account/utils.py`

- **hash_password**: pwdlib (Argon2, Bcrypt) 로 해시.
- **verify_password**: 평문 vs 해시 검증.
- **create_access_token**: payload에 exp 넣고 HS256 JWT. 기본 만료 30분.
- **decode_token**: JWT 디코드 (검증만, DB 조회 없음).

### 6.5 스키마 — `apps/account/schemas.py`

- **SignupPayload**: username, email, display_name, password, password_again. validator로 비밀번호 일치, display_name 없으면 랜덤 8자.
- **LoginPayload**: username, password.
- **UserOut**: username, display_name, is_host.
- **UserDetailOut**: UserOut + email, created_at, updated_at.
- **UpdateUserPayload**: display_name, email, password, password_again (선택). validator로 최소 1필드, 비밀번호 일치. hashed_password는 computed로 hash_password 적용.

### 6.6 예외 — `apps/account/exceptions.py`

- DuplicatedUsernameError, DuplicatedEmailError (422), UserNotFoundError (404), PasswordMismatchError (401), InvalidTokenError, ExpiredTokenError (401), AuthNotProvidedError (401).

### 6.7 상수 — `apps/account/constants.py`

- `AUTH_TOKEN_COOKIE_NAME = "auth_token"`.

---

## 7. 캘린더(Calendar) 앱

### 7.1 라우터 prefix

- 없음 (루트에 매핑).

### 7.2 엔드포인트 — `apps/calendar/endpoints.py`

- **호스트 캘린더**
  - **GET /calendar/{host_username}**: 호스트 조회 → 캘린더 조회. 본인이면 CalendarDetailOut(상세), 아니면 CalendarOut(공개용).
  - **GET /calendar/{host_username}/bookings?year=&month=**: 해당 호스트 캘린더의 해당 연월 부킹 + 같은 기간 Google Calendar 이벤트 리스트. year≥2026.
  - **GET /calendar/{host_username}/bookings/stream**: 위와 동일 데이터를 NDJSON 스트리밍. DB 부킹 먼저 스트림, 3초 sleep 후 Google 이벤트 스트림.
  - **POST /calendar**: 로그인 사용자. is_host 아니면 GuestPermissionError. Calendar 생성 (CalendarCreateIn). host_id=user.id, Unique 위반 시 CalendarAlreadyExistsError.
  - **PATCH /calendar**: 로그인 사용자. 본인 캘린더만. topics/description/google_calendar_id 부분 수정.

- **타임슬롯**
  - **GET /time-slots/{host_username}**: 활성 호스트의 캘린더 타임슬롯 목록.
  - **POST /time-slots**: 호스트만. TimeSlotCreateIn. SQLite/PostgreSQL 분기로 기존 타임슬롯과 시간·요일 겹침 검사 후 겹치면 TimeSlotOverlapError. 새 TimeSlot 저장.

- **부킹**
  - **GET /guest-calendar/bookings**: 로그인 사용자. 본인(guest) 부킹 페이지네이션 (page, page_size). PaginatedBookingOut.
  - **POST /bookings/{host_username}**: 호스트가 아니고, 본인이 호스트가 아니며, when≥오늘, time_slot이 해당 호스트 캘린더 소속이고 when의 요일이 time_slot.weekdays에 있을 때만. 동일 guest·when·time_slot_id 중복 시 BookingAlreadyExistsError. Booking 생성 후 백그라운드에서 Google Calendar 이벤트 생성하고 google_event_id 저장.
  - **GET /bookings**: 호스트 본인 캘린더 부킹 목록 (페이지네이션).
  - **GET /bookings/{booking_id}**: 호스트면 자신 캘린더 또는 자신이 guest인 부킹, 아니면 자신이 guest인 부킹만. 404 시 "예약 내역이 없습니다."
  - **PATCH /bookings/{booking_id}**: 호스트용. when/time_slot_id 변경. 과거 일자면 PastBookingError. 변경 후 google_event_id 있으면 백그라운드에서 Google 이벤트 update.
  - **PATCH /guest-bookings/{booking_id}**: 게스트 본인 부킹만. topic, description, when, time_slot_id 수정. Google 이벤트 동기화.
  - **PATCH /bookings/{booking_id}/status**: 호스트용. attendance_status만 변경 (HostBookingStatusUpdateIn).
  - **DELETE /guest-bookings/{booking_id}**: 게스트 본인만. 당일 이전만. attendance_status를 CANCELLED로 바꾸고, google_event_id 있으면 백그라운드에서 Google 이벤트 삭제.
  - **POST /bookings/{booking_id}/upload**: 게스트 본인 부킹에 파일 1~3개 업로드. BookingFile 레코드 추가.

### 7.3 타임슬롯 겹침 검사

- **check_overlap_sqlite**: 기존 타임슬롯의 weekdays와 새 weekdays에 공통 요일이 있는지 확인 (Python).
- **create_time_slot** 내부: SQLite는 기존 타임슬롯을 가져와서 시간 구간 겹침 + 위 함수로 요일 겹침 검사. PostgreSQL은 `jsonb_array_elements_text(weekdays)` 등으로 SQL에서 겹치는 TimeSlot 존재 여부 확인.

### 7.4 스키마 — `apps/calendar/schemas.py`

- CalendarOut / CalendarDetailOut, CalendarCreateIn / CalendarUpdateIn. Topics 타입은 리스트 중복 제거·정렬(AfterValidator).
- TimeSlotCreateIn (start_time < end_time 검증), TimeSlotOut.
- BookingCreateIn, BookingOut (time_slot, host, files 포함), SimpleBookingOut, PaginatedBookingOut, BookingFileOut.
- HostBookingUpdateIn, GuestBookingUpdateIn, HostBookingStatusUpdateIn.
- GoogleCalendarEventOut: id, start/end dict 기반으로 time_slot(GoogleCalendarTimeSlot), when(date) computed.

### 7.5 의존성 — `apps/calendar/deps.py`

- **UtcNow**: `Annotated[datetime, Depends(utcnow)]` — `libs/datetime/datetime.utcnow()`.

### 7.6 예외 — `apps/calendar/exceptions.py`

- HostNotFoundError, CalendarNotFoundError, CalendarAlreadyExistsError, GuestPermissionError, TimeSlotOverlapError, TimeSlotNotFoundError, SelfBookingError, PastBookingError, BookingAlreadyExistsError, InvalidYearMonthError.

---

## 8. 공용 라이브러리 (libs)

### 8.1 datetime — `libs/datetime/datetime.py`

- **utcnow()**: 현재 UTC 시각 (timezone 붙은 datetime).
- **aware_datetime(dt, tzinfo)**: datetime에 tzinfo 설정.

### 8.2 Google Calendar — `libs/google/calendar/`

- **services.py**
  - **GoogleCalendarService**: Service Account 파일(`GOOGLE_CREDENTIALS_PATH`)로 인증, Calendar API v3.
  - **make_event_body**: start/end(datetime, timezone), summary, description, reminder 등으로 이벤트 body dict 생성.
  - **create_event**: insert 후 이벤트 반환 (실패 시 None).
  - **event_list**: time_min, time_max, calendar_id로 list.
  - **update_event**, **delete_event**, **get_event**.
- **schemas.py**: Reminder, CalendarItem, CalendarEvent 등 Google API 응답용 모델.
- **deps.py**: **get_google_calendar_service(google_calendar_id)** — env `GOOGLE_CALENDAR_ID` 또는 인자로 서비스 생성. **GoogleCalendarServiceDep** 로 주입.

### 8.3 collections — `libs/collections/sort.py`

- **deduplicate_and_sort(items)**: 리스트 중복 제거, 등장 순서 유지 (`dict.fromkeys`).

### 8.4 query — `libs/query.py`

- **exact_match_list_json(session_or_dialect, attr, value, target_type)**: JSON/JSONB 배열 속성에 value가 포함되는지 검사하는 Select. SQLite는 json_each, PostgreSQL은 jsonb_array_elements_text 등으로 분기. CalendarAdmin 검색 등에서 사용.

---

## 9. 관리자 (SQLAdmin)

### 9.1 설정 — `appserver/admin.py`

- **include_admin_views(admin)**: UserAdmin, CalendarAdmin, TimeSlotAdmin, BookingAdmin, BookingFileAdmin, OAuthAccountAdmin 등록.
- **AdminAuthentication**: 로그인 시 account의 login 엔드포인트에 username/password 전달해 200이면 응답의 access_token을 세션에 저장. authenticate 시 세션 토큰 decode. 로그아웃 시 세션 clear.

### 9.2 계정 Admin — `apps/account/admin.py`

- **UserAdmin**: 목록/검색/정렬, 폼에서 비밀번호는 insert/update 시 hash_password 적용. 삭제 시 delete_model에서 on_model_delete로 username/email 등을 deleted/랜덤으로 바꾸고 status=DELETED, after_model_delete에서 연관 OAuthAccount 삭제.
- **OAuthAccountAdmin**: provider, provider_account_id, user 등 CRUD.

### 9.3 캘린더 Admin — `apps/calendar/admin.py`

- **CalendarAdmin**: topics JSON 검색 시 exact_match_list_json 사용. (참고: search_query 내 cast(field, String)에서 String 미임포트 시 NameError 가능.)
- **TimeSlotAdmin**: weekdays 포맷터로 요일 한글 표시.
- **BookingAdmin**, **BookingFileAdmin**: BookingFile은 이미지/PDF/오피스 등 확장자별 file_formatter.

---

## 10. 배포 (CI/CD)

### 10.1 워크플로 — `.github/workflows/deploy-aws.yaml`

- **트리거**: `main` 브랜치 push.
- **환경**: ubuntu-latest.

**단계 요약:**

1. **Checkout**  
   - 저장소 코드 체크아웃.

2. **Copy project (SCP)**  
   - Bastion(`WITHSEUNGZZANG_BASTION_PUBLIC_IP`) 경유해 private app 서버(`WITHSEUNGZZANG_APP_PRIVATE_IP`)의 `/home/ubuntu/deploy-temp`로 현재 디렉터리 복사.  
   - `WITHSEUNGZZANG_SSH_KEY` 사용. rm + overwrite.

3. **Deploy (SSH)**  
   - 같은 Bastion 경유로 app 서버에 SSH 접속 후 아래 스크립트 실행.
   - **WORKDIR**: `/withseungzzang`, **TMPDIR**: `/home/ubuntu/deploy-temp`.
   - `sudo mkdir -p "$WORKDIR"`.
   - `sudo rsync -av --delete` 로 TMPDIR → WORKDIR. 제외: .git, .github, .venv, __pycache__, .pytest_cache.
   - `sudo chown -R ubuntu:ubuntu "$WORKDIR"`.
   - `cd "$WORKDIR"`.
   - `export DATABASE_URL="${{ secrets.RDS_DATABASE_URL }}"`.
   - `. .venv/bin/activate` → `pip install --upgrade pip`, `pip install poetry`.
   - `poetry config virtualenvs.create false` → `poetry install --no-interaction --no-root`.
   - `mkdir -p uploads/bookings static`, chown/chmod.
   - **alembic upgrade head**.
   - **sudo systemctl restart calendarapp**, **sudo systemctl restart nginx**.
   - sleep 5 후 **curl -fsS http://127.0.0.1:8000/health**, **curl -fsS http://127.0.0.1/app/** 로 성공 여부 확인.

### 10.2 필요한 시크릿

- `WITHSEUNGZZANG_APP_PRIVATE_IP`: 앱 서버 사설 IP.
- `WITHSEUNGZZANG_SSH_KEY`: SSH 비밀키.
- `WITHSEUNGZZANG_BASTION_PUBLIC_IP`: Bastion 공인 IP.
- `RDS_DATABASE_URL`: PostgreSQL 연결 문자열 (예: `postgresql+psycopg://...?sslmode=verify-full&sslrootcert=...`).

### 10.3 서버 측 가정

- systemd 서비스 `calendarapp` (예: uvicorn 실행).
- nginx가 8000 포트의 앱을 리버스 프록시하고 `/app/` 등으로 프론트 서빙.
- app 서버에 `.venv`, poetry로 의존성 설치된 상태에서 rsync로 코드만 갱신 후 재시작.

---

## 요약 표

| 구분 | 위치/경로 |
|------|-----------|
| 앱 진입점 | appserver/app.py |
| DB 세션/엔진 | appserver/db.py |
| 마이그레이션 | alembic/env.py, alembic/versions/*.py |
| 계정 API | appserver/apps/account/endpoints.py, prefix /account |
| 캘린더 API | appserver/apps/calendar/endpoints.py, prefix 없음 |
| 관리자 UI | appserver/admin.py, /seungzzang/admin/ |
| 배포 | .github/workflows/deploy-aws.yaml |

이 문서만으로도 프론트를 제외한 **데이터 모델 → API → 라이브러리 → Admin → 배포** 흐름을 한 번에 따라가며 설명할 수 있습니다. 특정 파일/함수를 더 쪼개서 보고 싶으면 해당 경로를 지정해 요청하면 됩니다.
