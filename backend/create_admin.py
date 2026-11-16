
from getpass import getpass

from mysql.connector import Error

from backend.database import get_db_connection
from backend.security import hash_password


def create_superadmin():
    print("\n=== PEMBUATAN SUPERADMIN CAMPUSAI UNPRI ===")

    # Mengambil identitas admin
    nama = input("Nama lengkap: ").strip()
    username = input("Username: ").strip()

    if not nama or not username:
        print("Nama dan username wajib diisi.")
        return

    # Password tidak ditampilkan saat diketik
    password = getpass("Password: ")
    konfirmasi = getpass("Konfirmasi password: ")

    if len(password) < 12:
        print("Password minimal harus 12 karakter.")
        return

    if password != konfirmasi:
        print("Konfirmasi password tidak cocok.")
        return

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Memeriksa apakah username sudah digunakan
        cursor.execute(
            "SELECT id FROM admin WHERE username = %s",
            (username,)
        )

        if cursor.fetchone():
            print("Username sudah digunakan.")
            return

        # Mengenkripsi password sebelum disimpan
        password_hash = hash_password(password)

        # Membuat akun dengan role superadmin
        cursor.execute(
            """
            INSERT INTO admin
            (nama, username, password_hash, role)
            VALUES (%s, %s, %s, %s)
            """,
            (nama, username, password_hash, "superadmin")
        )

        connection.commit()

        print("\nSuperadmin berhasil dibuat!")
        print(f"Nama     : {nama}")
        print(f"Username : {username}")
        print("Role     : superadmin")

    except Error as error:
        if connection and connection.is_connected():
            connection.rollback()

        print(f"Gagal membuat Superadmin: {error}")

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    create_superadmin()
