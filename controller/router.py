import os
import hmac
import hashlib
import secrets
import string
import logging
import psycopg
from psycopg.rows import dict_row
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, Request
from schemas.user import Email_Schema, Otp_Verify_Schema
from service.db import get_db
from service.app import send_email
from service.limiter import limiter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

OTP_EXPIRY_MINUTES = 10
RESEND_COOLDOWN_SECONDS = 60
MAX_ATTEMPTS = 5
OTP_SECRET = os.environ["OTP_SECRET"].encode()


def generate_otp(length: int = 6) -> str:
    return "".join(secrets.choice(string.digits) for _ in range(length))


def hash_otp(email: str, otp: str) -> str:
    return hmac.new(OTP_SECRET, f"{email}:{otp}".encode(), hashlib.sha256).hexdigest()


@router.post("/send-otp")
@limiter.limit('2/minute')
def send_otp(
    request:Request,
    body: Email_Schema,
    background_tasks: BackgroundTasks,
    db=Depends(get_db),
):
    email = body.email.strip().lower()
    otp = generate_otp()
    query = """
        INSERT INTO email_login
            (email, otp_hash, otp_expired_at, otp_verified, otp_attempts, otp_sent_at)
        VALUES (%s, %s, now() + make_interval(mins => %s), false, 0, now())
        ON CONFLICT (email) DO UPDATE SET
            otp_hash       = EXCLUDED.otp_hash,
            otp_expired_at = EXCLUDED.otp_expired_at,
            otp_verified   = false,
            otp_attempts   = 0,
            otp_sent_at    = now()
        WHERE email_login.otp_sent_at IS NULL
           OR email_login.otp_sent_at < now() - make_interval(secs => %s)
        RETURNING email
    """
    try:
        with db.cursor() as cursor:
            cursor.execute(
                query,
                (email, hash_otp(email, otp), OTP_EXPIRY_MINUTES, RESEND_COOLDOWN_SECONDS),
            )
            row = cursor.fetchone()
        db.commit()
    except psycopg.Error:
        db.rollback()
        logger.exception("send_otp failed")
        raise HTTPException(status_code=500, detail="Could not create OTP")

    if row is None:
        raise HTTPException(
            status_code=429,
            detail=f"Please wait {RESEND_COOLDOWN_SECONDS}s before requesting a new OTP",
        )

    background_tasks.add_task(
        send_email,
        [email],
        "Your OTP code",
        f"Your OTP is {otp}. It expires in {OTP_EXPIRY_MINUTES} minutes.",
    )
    return {"message": "OTP sent to your email"}


@router.post("/verify-otp")
@limiter.limit('20/minute')
def verify_otp(
    request:Request,
    body: Otp_Verify_Schema,
    db=Depends(get_db),
):
    email = body.email.strip().lower()

    attempt_query = """
        UPDATE email_login
        SET otp_attempts = otp_attempts + 1
        WHERE email = %s
          AND otp_hash IS NOT NULL
          AND otp_expired_at > now()
          AND otp_attempts < %s
        RETURNING otp_hash
    """
    success_query = """
        UPDATE email_login
        SET otp_verified = true, otp_hash = NULL, otp_attempts = 0
        WHERE email = %s
    """
    try:
        with db.cursor(row_factory=dict_row) as cursor:
            cursor.execute(attempt_query, (email, MAX_ATTEMPTS))
            row = cursor.fetchone()
            db.commit()  # wrong aanaalum attempt count persist aaganum

            if row is None or not hmac.compare_digest(
                row["otp_hash"], hash_otp(email, body.otp)
            ):
                raise HTTPException(status_code=400, detail="Invalid or expired OTP")

            cursor.execute(success_query, (email,))
        db.commit()
    except psycopg.Error:
        db.rollback()
        logger.exception("verify_otp failed")
        raise HTTPException(status_code=500, detail="Something went wrong")

    return {"message": "OTP verified"}