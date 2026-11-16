from backend.chat_service import process_chat
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import date
from mysql.connector import Error
from jwt import InvalidTokenError

from backend.database import get_db_connection
from backend.security import (
    verify_password,
    create_access_token,
    decode_access_token
)

# Membuat aplikasi utama CampusAI UNPRI
app = FastAPI(
    title="CampusAI UNPRI",
    description="AI Asisten Informasi Akademik dan Administrasi UNPRI",
    version="1.0.0"
)

# Mengatur izin akses dari frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Skema autentikasi menggunakan Bearer Token
bearer_scheme = HTTPBearer(auto_error=False)


# Memeriksa token dan memastikan akun admin masih terdaftar
def get_current_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
):
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Silakan login terlebih dahulu",
            headers={"WWW-Authenticate": "Bearer"}
        )

    connection = None
    cursor = None

    try:
        # Memverifikasi token JWT
        payload = decode_access_token(credentials.credentials)
        username = payload.get("sub")

        if not username:
            raise HTTPException(
                status_code=401,
                detail="Token tidak valid"
            )

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, nama, username, role
            FROM admin
            WHERE username = %s
            """,
            (username,)
        )

        admin = cursor.fetchone()

        if not admin or admin["role"] not in ("admin", "superadmin"):
            raise HTTPException(
                status_code=401,
                detail="Akun admin tidak ditemukan atau tidak memiliki akses"
            )

        return admin

    except InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Token tidak valid atau sudah kedaluwarsa",
            headers={"WWW-Authenticate": "Bearer"}
        )

    except HTTPException:
        raise

    except Error:
        raise HTTPException(
            status_code=500,
            detail="Gagal memeriksa akun admin"
        )

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()

# Model data untuk kategori
class KategoriRequest(BaseModel):
    nama_kategori: str = Field(min_length=1, max_length=100)
    deskripsi: Optional[str] = None


# Model data untuk informasi kampus
class InformasiRequest(BaseModel):
    kategori_id: int
    judul: str = Field(min_length=1, max_length=200)
    isi: str = Field(min_length=1)
    sumber: Optional[str] = None
    tanggal_berlaku: Optional[date] = None
    status: Literal["aktif", "nonaktif"] = "aktif"

# Model data untuk login admin
class AdminLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1)

# Model data untuk pertanyaan chatbot
class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    session_id: Optional[str] = None
    
# Endpoint halaman utama
@app.get("/")
def home():
    return {
        "success": True,
        "application": "CampusAI UNPRI",
        "message": "Selamat datang di CampusAI UNPRI!"
    }

# ==========================
# API CHATBOT CAMPUSAI
# ==========================

@app.post("/api/chat")
def chat_endpoint(data: ChatRequest):
    try:
        result = process_chat(
            question=data.question,
            session_id=data.session_id
        )

        return result

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error)
        )

    except Error:
        raise HTTPException(
            status_code=500,
            detail="Terjadi kesalahan saat mengakses database."
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Terjadi kesalahan pada sistem chatbot."
        )

# Endpoint mengecek status backend dan database
@app.get("/api/health")
def health_check():
    connection = None

    try:
        connection = get_db_connection()

        return {
            "status": "online",
            "application": "CampusAI UNPRI",
            "database": "connected"
        }

    except Error as error:
        raise HTTPException(status_code=500, detail=str(error))

    finally:
        if connection and connection.is_connected():
            connection.close()

# ==========================
# API LOGIN ADMIN
# ==========================

@app.post("/api/admin/login")
def admin_login(data: AdminLoginRequest):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Mencari akun berdasarkan username
        cursor.execute(
            """
            SELECT id, nama, username, password_hash, role
            FROM admin
            WHERE username = %s
            """,
            (data.username.strip(),)
        )

        admin = cursor.fetchone()

        # Memeriksa username dan password
        if not admin or not verify_password(
            data.password,
            admin["password_hash"]
        ):
            raise HTTPException(
                status_code=401,
                detail="Username atau password salah"
            )

        if admin["role"] not in ("admin", "superadmin"):
            raise HTTPException(
                status_code=403,
                detail="Akun tidak memiliki akses admin"
            )

        # Membuat token JWT
        token = create_access_token({
            "sub": admin["username"],
            "admin_id": admin["id"],
            "role": admin["role"]
        })

        return {
            "success": True,
            "message": "Login berhasil",
            "access_token": token,
            "token_type": "bearer",
            "admin": {
                "id": admin["id"],
                "nama": admin["nama"],
                "username": admin["username"],
                "role": admin["role"]
            }
        }

    except HTTPException:
        raise

    except Error:
        raise HTTPException(
            status_code=500,
            detail="Terjadi kesalahan pada database"
        )

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()

# ==========================
# API KATEGORI
# ==========================

# Menampilkan semua kategori
@app.get("/api/kategori")
def get_kategori():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT * FROM kategori ORDER BY id DESC")
        data = cursor.fetchall()

        return {
            "success": True,
            "total": len(data),
            "data": data
        }

    except Error as error:
        raise HTTPException(status_code=500, detail=str(error))

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


# Menambahkan kategori
@app.post("/api/kategori", status_code=201)
def create_kategori(
    data: KategoriRequest,
    current_admin: dict = Depends(get_current_admin)
):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        sql = """
            INSERT INTO kategori (nama_kategori, deskripsi)
            VALUES (%s, %s)
        """

        cursor.execute(sql, (data.nama_kategori, data.deskripsi))
        connection.commit()

        return {
            "success": True,
            "message": "Kategori berhasil ditambahkan",
            "id": cursor.lastrowid
        }

    except Error as error:
        if connection:
            connection.rollback()
        raise HTTPException(status_code=500, detail=str(error))

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


# ==========================
# API INFORMASI KAMPUS
# ==========================

# Menampilkan semua informasi kampus
@app.get("/api/informasi")
def get_informasi():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        sql = """
            SELECT
                informasi_kampus.*,
                kategori.nama_kategori
            FROM informasi_kampus
            INNER JOIN kategori
                ON informasi_kampus.kategori_id = kategori.id
            ORDER BY informasi_kampus.id DESC
        """

        cursor.execute(sql)
        data = cursor.fetchall()

        return {
            "success": True,
            "total": len(data),
            "data": data
        }

    except Error as error:
        raise HTTPException(status_code=500, detail=str(error))

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


# Menambahkan informasi kampus
@app.post("/api/informasi", status_code=201)
def create_informasi(
    data: InformasiRequest,
    current_admin: dict = Depends(get_current_admin)
):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Memastikan kategori tersedia
        cursor.execute(
            "SELECT id FROM kategori WHERE id = %s",
            (data.kategori_id,)
        )

        if not cursor.fetchone():
            raise HTTPException(
                status_code=404,
                detail="Kategori tidak ditemukan"
            )

        sql = """
            INSERT INTO informasi_kampus
            (kategori_id, judul, isi, sumber, tanggal_berlaku, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        values = (
            data.kategori_id,
            data.judul,
            data.isi,
            data.sumber,
            data.tanggal_berlaku,
            data.status
        )

        cursor.execute(sql, values)
        connection.commit()

        return {
            "success": True,
            "message": "Informasi kampus berhasil ditambahkan",
            "id": cursor.lastrowid
        }

    except HTTPException:
        raise

    except Error as error:
        if connection:
            connection.rollback()
        raise HTTPException(status_code=500, detail=str(error))

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


# Mengedit informasi kampus
@app.put("/api/informasi/{informasi_id}")
def update_informasi(
    informasi_id: int,
    data: InformasiRequest,
    current_admin: dict = Depends(get_current_admin)
):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id FROM informasi_kampus WHERE id = %s",
            (informasi_id,)
        )

        if not cursor.fetchone():
            raise HTTPException(
                status_code=404,
                detail="Informasi kampus tidak ditemukan"
            )

        cursor.execute(
            "SELECT id FROM kategori WHERE id = %s",
            (data.kategori_id,)
        )

        if not cursor.fetchone():
            raise HTTPException(
                status_code=404,
                detail="Kategori tidak ditemukan"
            )

        sql = """
            UPDATE informasi_kampus
            SET kategori_id = %s,
                judul = %s,
                isi = %s,
                sumber = %s,
                tanggal_berlaku = %s,
                status = %s
            WHERE id = %s
        """

        values = (
            data.kategori_id,
            data.judul,
            data.isi,
            data.sumber,
            data.tanggal_berlaku,
            data.status,
            informasi_id
        )

        cursor.execute(sql, values)
        connection.commit()

        return {
            "success": True,
            "message": "Informasi kampus berhasil diperbarui"
        }

    except HTTPException:
        raise

    except Error as error:
        if connection:
            connection.rollback()
        raise HTTPException(status_code=500, detail=str(error))

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


# Menghapus informasi kampus
@app.delete("/api/informasi/{informasi_id}")
def delete_informasi(
    informasi_id: int,
    current_admin: dict = Depends(get_current_admin)
):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "DELETE FROM informasi_kampus WHERE id = %s",
            (informasi_id,)
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Informasi kampus tidak ditemukan"
            )

        connection.commit()

        return {
            "success": True,
            "message": "Informasi kampus berhasil dihapus"
        }

    except HTTPException:
        raise

    except Error as error:
        if connection:
            connection.rollback()
        raise HTTPException(status_code=500, detail=str(error))

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
