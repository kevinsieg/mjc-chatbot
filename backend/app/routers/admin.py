import hmac

from fastapi import APIRouter, Depends, Header, HTTPException
from psycopg.errors import UniqueViolation

from app.auth import hash_password, require_role, verify_password
from app.db_util import get_connection
from app.schemas.admin import (
    ApiUsageRow,
    AuthVerifyRequest,
    AuthVerifyResponse,
    DailyPoint,
    HeatmapPoint,
    HourlyPoint,
    PagedUsers,
    StatsOverview,
    TopSourceRow,
    UserCheckRequest,
    UserCheckResponse,
    UserCreate,
    UserOut,
    UserPatch,
    WeekdayPoint,
)
from app.settings import get_nextauth_secret

router = APIRouter()


# ── Internal auth endpoint (called by Auth.js Credentials provider) ─────────

@router.post("/internal/auth/verify", response_model=AuthVerifyResponse, include_in_schema=False)
def auth_verify(
    body: AuthVerifyRequest,
    x_service_token: str = Header(alias="x-service-token"),
) -> AuthVerifyResponse:
    """Verify credentials for Auth.js. Protected by X-Service-Token matching NEXTAUTH_SECRET."""
    if not hmac.compare_digest(x_service_token, get_nextauth_secret()):
        raise HTTPException(status_code=401, detail="Invalid service token")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, email, name, password_hash, role FROM users WHERE email = %s AND deleted_at IS NULL",
                (body.email,),
            )
            row = cur.fetchone()
    if not row or not verify_password(body.password, row[3]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return AuthVerifyResponse(id=row[0], email=row[1], name=row[2], role=row[4])


@router.post("/internal/user-check", response_model=UserCheckResponse, include_in_schema=False)
def user_check(
    body: UserCheckRequest,
    x_service_token: str = Header(alias="x-service-token"),
) -> UserCheckResponse:
    """Re-validate a session user: return current role and whether the account is still active."""
    if not hmac.compare_digest(x_service_token, get_nextauth_secret()):
        raise HTTPException(status_code=401, detail="Invalid service token")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT role, deleted_at FROM users WHERE id = %s",
                (body.user_id,),
            )
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return UserCheckResponse(role=row[0], active=row[1] is None)


# ── Stats endpoints ──────────────────────────────────────────────────────────

@router.get("/stats/overview", response_model=StatsOverview)
def stats_overview(
    principal: dict = Depends(require_role("admin", "staff")),
) -> StatsOverview:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    COUNT(DISTINCT session_id)                                    AS total_sessions,
                    COUNT(*)                                                      AS total_messages,
                    COALESCE(AVG(latency_ms), 0)                                 AS avg_latency_ms,
                    COALESCE(
                        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms),
                        0
                    )                                                             AS p95_latency_ms,
                    COALESCE(SUM(cost_eur), 0)                                   AS total_cost_eur,
                    CASE WHEN COUNT(DISTINCT session_id) > 0
                        THEN COUNT(*)::float / COUNT(DISTINCT session_id)
                        ELSE 0 END                                                AS avg_messages_per_session,
                    CASE WHEN COUNT(*) > 0
                        THEN COALESCE(SUM(cost_eur), 0)::float / COUNT(*)
                        ELSE 0 END                                                AS cost_per_message
                FROM chat_logs
            """)
            row = cur.fetchone()
    return StatsOverview(
        total_sessions=row[0],
        total_messages=row[1],
        avg_latency_ms=round(float(row[2]), 1),
        p95_latency_ms=round(float(row[3]), 1),
        total_cost_eur=round(float(row[4]), 6),
        avg_messages_per_session=round(float(row[5]), 2),
        cost_per_message=round(float(row[6]), 6),
    )


@router.get("/stats/weekday", response_model=list[WeekdayPoint])
def stats_weekday(
    principal: dict = Depends(require_role("admin", "staff")),
) -> list[WeekdayPoint]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT EXTRACT(DOW FROM timestamp)::INT AS day, COUNT(*) AS count
                FROM chat_logs
                GROUP BY day
                ORDER BY day
            """)
            rows = cur.fetchall()
    return [WeekdayPoint(day=r[0], count=r[1]) for r in rows]


@router.get("/stats/daily", response_model=list[DailyPoint])
def stats_daily(
    principal: dict = Depends(require_role("admin", "staff")),
) -> list[DailyPoint]:
    """Messages per day for the last 30 days."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    TO_CHAR(DATE(timestamp), 'YYYY-MM-DD') AS day,
                    COUNT(*)                               AS count
                FROM chat_logs
                WHERE timestamp >= NOW() - INTERVAL '30 days'
                GROUP BY day
                ORDER BY day
            """)
            rows = cur.fetchall()
    return [DailyPoint(date=r[0], count=r[1]) for r in rows]


@router.get("/stats/hourly", response_model=list[HourlyPoint])
def stats_hourly(
    principal: dict = Depends(require_role("admin", "staff")),
) -> list[HourlyPoint]:
    """Message count by hour of day (0–23, all time)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT EXTRACT(HOUR FROM timestamp)::INT AS hour, COUNT(*) AS count
                FROM chat_logs
                GROUP BY hour
                ORDER BY hour
            """)
            rows = cur.fetchall()
    return [HourlyPoint(hour=r[0], count=r[1]) for r in rows]


@router.get("/stats/heatmap", response_model=list[HeatmapPoint])
def stats_heatmap(
    principal: dict = Depends(require_role("admin", "staff")),
) -> list[HeatmapPoint]:
    """Message count by (day-of-week, hour) for all time."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    EXTRACT(DOW FROM timestamp)::INT  AS day,
                    EXTRACT(HOUR FROM timestamp)::INT AS hour,
                    COUNT(*)                          AS count
                FROM chat_logs
                GROUP BY day, hour
                ORDER BY day, hour
            """)
            rows = cur.fetchall()
    return [HeatmapPoint(day=r[0], hour=r[1], count=r[2]) for r in rows]


@router.get("/stats/top-sources", response_model=list[TopSourceRow])
def stats_top_sources(
    principal: dict = Depends(require_role("admin", "staff")),
) -> list[TopSourceRow]:
    """Top 10 knowledge sources retrieved by the RAG pipeline."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT source, COUNT(*) AS hit_count
                FROM chat_logs, UNNEST(retrieved_sources) AS source
                WHERE retrieved_sources IS NOT NULL
                GROUP BY source
                ORDER BY hit_count DESC
                LIMIT 10
            """)
            rows = cur.fetchall()
    return [TopSourceRow(source=r[0], hit_count=r[1]) for r in rows]


@router.get("/stats/api-usage", response_model=list[ApiUsageRow])
def stats_api_usage(
    principal: dict = Depends(require_role("admin", "staff")),
) -> list[ApiUsageRow]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    model,
                    SUM(prompt_tokens)::INT            AS prompt_tokens,
                    SUM(completion_tokens)::INT        AS completion_tokens,
                    ROUND(SUM(cost_eur)::NUMERIC, 6)  AS cost_eur,
                    ROUND(AVG(latency_ms)::NUMERIC, 1) AS avg_latency_ms
                FROM chat_logs
                GROUP BY model
                ORDER BY model
            """)
            rows = cur.fetchall()
    return [
        ApiUsageRow(
            model=r[0],
            prompt_tokens=r[1],
            completion_tokens=r[2],
            cost_eur=float(r[3]),
            avg_latency_ms=float(r[4]),
        )
        for r in rows
    ]


# ── User management endpoints (admin only) ──────────────────────────────────

@router.get("/users", response_model=PagedUsers)
def list_users(
    page: int = 1,
    principal: dict = Depends(require_role("admin")),
) -> PagedUsers:
    page_size = 20
    offset = (page - 1) * page_size
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM users")
            total = cur.fetchone()[0]
            cur.execute(
                """
                SELECT id, email, name, role, created_at, deleted_at
                FROM users
                ORDER BY deleted_at IS NOT NULL, created_at DESC
                LIMIT %s OFFSET %s
                """,
                (page_size, offset),
            )
            rows = cur.fetchall()
    items = [
        UserOut(id=r[0], email=r[1], name=r[2], role=r[3], created_at=r[4], deleted_at=r[5])
        for r in rows
    ]
    return PagedUsers(items=items, total=total, page=page, page_size=page_size)


@router.post("/users", response_model=UserOut)
def create_user(
    body: UserCreate,
    principal: dict = Depends(require_role("admin")),
) -> UserOut:
    ph = hash_password(body.password)
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (email, name, password_hash, role)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, email, name, role, created_at, deleted_at
                    """,
                    (body.email, body.name, ph, body.role),
                )
                row = cur.fetchone()
            conn.commit()
    except UniqueViolation:
        raise HTTPException(status_code=409, detail="Email already exists")
    return UserOut(id=row[0], email=row[1], name=row[2], role=row[3], created_at=row[4], deleted_at=row[5])


@router.patch("/users/{user_id}", response_model=UserOut)
def patch_user(
    user_id: int,
    body: UserPatch,
    principal: dict = Depends(require_role("admin")),
) -> UserOut:
    updates: dict = {}
    if "role" in body.model_fields_set:
        updates["role"] = body.role
    if "name" in body.model_fields_set:
        updates["name"] = body.name
    if "email" in body.model_fields_set:
        updates["email"] = body.email
    if "password" in body.model_fields_set:
        updates["password_hash"] = hash_password(body.password)
    if not updates:
        raise HTTPException(status_code=422, detail="Nothing to update")
    set_clause = ", ".join(f"{col} = %s" for col in updates)
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE users SET {set_clause}
                    WHERE id = %s AND deleted_at IS NULL
                    RETURNING id, email, name, role, created_at, deleted_at
                    """,
                    (*updates.values(), user_id),
                )
                row = cur.fetchone()
            conn.commit()
    except UniqueViolation:
        raise HTTPException(status_code=409, detail="Email already exists")
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut(id=row[0], email=row[1], name=row[2], role=row[3], created_at=row[4], deleted_at=row[5])


@router.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    principal: dict = Depends(require_role("admin")),
) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET deleted_at = NOW() WHERE id = %s AND deleted_at IS NULL",
                (user_id,),
            )
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="User not found")
        conn.commit()
