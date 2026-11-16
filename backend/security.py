
import os
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

# Konfigurasi keamanan
SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY belum diatur. Atur SECRET_KEY di environment."
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Menggunakan Argon2 untuk hashing password
password_hash = PasswordHash.recommended()


# Membuat hash password sebelum disimpan ke database
def hash_password(password: str) -> str:
    return password_hash.hash(password)


# Memeriksa password saat admin login
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


# Membuat JWT setelah admin berhasil login
def create_access_token(data: dict) -> str:
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


# Memverifikasi JWT ketika admin mengakses endpoint
def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM]
    )
