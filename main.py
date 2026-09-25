import asyncio
import hashlib
import re
import secrets
import sqlite3
import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr


DB_PATH = "soap.db"

HOST = "0.0.0.0"
PORT = 80

CODE_TTL = 300
MAX_VERIFY_ATTEMPTS = 5
SEND_COOLDOWN = 60

DB_CLEANUP_PERIOD = 600


@asynccontextmanager
async def lifespan(app: FastAPI):
    cleanup_task = asyncio.create_task(cleanup_expired_codes())

    yield

    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


app = FastAPI(lifespan=lifespan)


class SendRequest(BaseModel):
    email: EmailStr


class VerifyRequest(BaseModel):
    email: EmailStr
    verification_code: str


def get_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS verification_codes (
                email TEXT PRIMARY KEY,
                code_hash TEXT NOT NULL,
                expires_at INTEGER NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                sent_at INTEGER NOT NULL
            )
            """
        )


def hash_code(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def make_response(status_code: int, state: str, **data):
    return JSONResponse(
        status_code=status_code,
        content={"code": status_code, "state": state, **data},
    )


# очистка бд


async def cleanup_expired_codes():
    while True:
        try:
            now = int(time.time())

            with get_db() as connection:
                connection.execute(
                    """
                    DELETE FROM verification_codes
                    WHERE expires_at <= ?
                    """,
                    (now,),
                )

        except asyncio.CancelledError:
            raise

        except Exception as exc:
            print(f"Cleanup error: {exc}")

        await asyncio.sleep(DB_CLEANUP_PERIOD)


# ловцы ошибок


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    if request.url.path == "/api/mail/send":
        state = "Invalid email"
    else:
        state = "Invalid request"

    return make_response(400, state)


# обработчики


@app.post("/api/mail/send")
async def send_code(data: SendRequest):
    email = str(data.email)
    now = int(time.time())

    with get_db() as connection:
        existing = connection.execute(
            "SELECT sent_at FROM verification_codes WHERE email = ?",
            (email,),
        ).fetchone()

        if existing and now - existing["sent_at"] < SEND_COOLDOWN:
            return make_response(429, "Too Many Requests")

        code = f"{secrets.randbelow(1_000_000):06d}"

        connection.execute(
            """
            INSERT OR REPLACE INTO verification_codes
            (email, code_hash, expires_at, attempts, sent_at)
            VALUES (?, ?, ?, 0, ?)
            """,
            (email, hash_code(code), now + CODE_TTL, now),
        )

    try:
        # TODO: отправка email
        print(f"Verification code for {email}: {code}")
    except Exception:
        with get_db() as connection:
            connection.execute(
                "DELETE FROM verification_codes WHERE email = ?",
                (email,),
            )

        return make_response(503, "Mail service unavailable")

    return make_response(200, "OK")


@app.post("/api/mail/verify")
async def verify_code(data: VerifyRequest):
    email = str(data.email)
    code = data.verification_code

    if not re.fullmatch(r"[0-9]{6}", code):
        return make_response(400, "Invalid request")

    with get_db() as connection:
        record = connection.execute(
            """
            SELECT code_hash, expires_at, attempts
            FROM verification_codes
            WHERE email = ?
            """,
            (email,),
        ).fetchone()

        if record is None:
            return make_response(404, "Verification code not found")

        if record["attempts"] >= MAX_VERIFY_ATTEMPTS:
            connection.execute(
                "DELETE FROM verification_codes WHERE email = ?",
                (email,),
            )
            return make_response(429, "Too many verification attempts")

        if record["expires_at"] <= int(time.time()):
            connection.execute(
                "DELETE FROM verification_codes WHERE email = ?",
                (email,),
            )
            return make_response(410, "Verification code expired")

        if not secrets.compare_digest(
            hash_code(code),
            record["code_hash"],
        ):
            attempts = record["attempts"] + 1

            if attempts >= MAX_VERIFY_ATTEMPTS:
                connection.execute(
                    "DELETE FROM verification_codes WHERE email = ?",
                    (email,),
                )
                return make_response(429, "Too many verification attempts")

            connection.execute(
                """
                UPDATE verification_codes
                SET attempts = ?
                WHERE email = ?
                """,
                (attempts, email),
            )

            return make_response(200, "OK", verification=False)

        connection.execute(
            "DELETE FROM verification_codes WHERE email = ?",
            (email,),
        )

    return make_response(200, "OK", verification=True)


def main():
    init_db()
    uvicorn.run(app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()