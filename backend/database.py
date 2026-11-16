
import mysql.connector
from mysql.connector import Error


# Konfigurasi koneksi database CampusAI UNPRI
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "campus_ai_unpri"
}


# Fungsi untuk menghubungkan Python ke MySQL
def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)

        if connection.is_connected():
            return connection

    except Error as error:
        print(f"Gagal menghubungkan database: {error}")
        raise
