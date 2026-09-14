from db import get_connection
import bcrypt
import secrets
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import os
from pathlib import Path

# Keep auth settings isolated from the YouTube chatbot service settings.
load_dotenv(Path(__file__).with_name(".env"))

def google_login(name,email,google_id):
    conn=get_connection()
    cur=conn.cursor()

    try:
        cur.execute("""
        SELECT id,name,email from users WHERE email=%s
        """,(email,))

        user=cur.fetchone()

        if user:
            return {
                "id":user[0],
                "name":user[1],
                "email":user[2]
            }

        cur.execute("""
            INSERT INTO users (name,email,google_id,email_verified) VALUES (%s,%s,%s,%s) RETURNING id
        """,(name,email,google_id,True))

        user_id=cur.fetchone()[0]
        conn.commit()

        return {
            "id":user_id,
            "name":name,
            "email":email
        }

    except Exception as e:
        conn.rollback()
        print(e)
        return None
    finally:
        cur.close()
        conn.close()

def hash_password(password):
    return bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    ).decode()

def check_password(password, password_hash):
    return bcrypt.checkpw(
        password.encode(),
        password_hash.encode()
    )

def generate_otp():
    return f"{secrets.randbelow(1000000):06d}"

def register_user(name, email, password):
    conn = get_connection()
    cur = conn.cursor()
    email = email.strip().lower()
    password_hash = hash_password(password)
    try:
        cur.execute(
            """
            INSERT INTO users (name, email, password_hash, email_verified)
            VALUES (%s, %s, %s, FALSE)
            RETURNING id
            """,
            (name, email, password_hash)
        )
        user_id = cur.fetchone()[0]
        conn.commit()

        return user_id
    except Exception as e:
        conn.rollback()
        return None
    finally:
        cur.close()
        conn.close()

def save_otp(user_id, otp):
    otp_hash = bcrypt.hashpw(
        otp.encode(),
        bcrypt.gensalt()
    ).decode()
    expires_at = datetime.now() + timedelta(minutes=10)
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO email_verifications
            (user_id, otp_hash, expires_at)
            VALUES (%s, %s, %s)
            """,
            (user_id, otp_hash, expires_at)
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()

def verify_otp(user_id, otp):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, otp_hash, expires_at, attempts, used
            FROM email_verifications
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (user_id,)
        )
        row = cur.fetchone()
        if not row:
            return False
        otp_id, otp_hash, expires_at, attempts, used = row
        if used:
            return False
        if datetime.now() > expires_at:
            return False
        if attempts >= 5:
            return False
        if not bcrypt.checkpw(otp.encode(),otp_hash.encode()):
            cur.execute(
                """
                UPDATE email_verifications
                SET attempts = attempts + 1
                WHERE id = %s
                """,
                (otp_id,)
            )
            conn.commit()
            return False
        cur.execute(
            """
            UPDATE email_verifications
            SET used = TRUE
            WHERE id = %s
            """,
            (otp_id,)
        )
        cur.execute(
            """
            UPDATE users
            SET email_verified = TRUE
            WHERE id = %s
            """,
            (user_id,)
        )
        conn.commit()
        return True
    finally:
        cur.close()
        conn.close()

def send_otp_email(to_email, otp):
    msg = EmailMessage()

    msg["Subject"] = "Your Email Verification OTP"
    msg["From"] = os.getenv("SMTP_EMAIL")
    msg["To"] = to_email

    msg.set_content(
        f"""
        Hello,
        Your OTP for email verification is:

        {otp}

        This OTP is valid for 10 minutes.
        If you did not request this, please ignore this email.
        Thanks
        """
    )

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(
            os.getenv("SMTP_EMAIL"),
            os.getenv("SMTP_PASSWORD")
        )
        server.send_message(msg)

def login_user(email, password):
    conn = get_connection()
    cur = conn.cursor()

    email = email.strip().lower()

    try:
        cur.execute(
            """
            SELECT id, name, email, password_hash, email_verified
            FROM users
            WHERE email = %s
            """,
            (email,)
        )

        user = cur.fetchone()

        if not user:
            return None

        user_id, name, email, password_hash, email_verified = user

        if not email_verified:
            return "NOT_VERIFIED"

        if not password_hash:
            return None

        if not check_password(password, password_hash):
            return None

        return {
            "id": user_id,
            "name": name,
            "email": email
        }

    finally:
        cur.close()
        conn.close()
