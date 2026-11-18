
import re
import uuid

from backend.database import get_db_connection
from backend.ollama_service import generate_answer


# Kata umum yang tidak terlalu membantu pencarian
STOPWORDS = {
    "apa", "bagaimana", "dimana", "kapan", "siapa",
    "yang", "dan", "atau", "untuk", "dengan", "dari",
    "ke", "di", "pada", "saya", "mahasiswa", "tolong",
    "cara", "tentang", "apakah", "bisa", "mohon",
    "mau", "ingin", "nya", "ada", "adalah", "itu",
    "ini", "prosedur"
}


# Kumpulan istilah yang memiliki maksud atau topik serupa

CONCEPTS = {
    "krs": [
        "krs",
        "kartu rencana studi",
        "pengisian krs",
        "mengisi krs",
        "isi krs",
        "ambil mata kuliah",
        "mengambil mata kuliah",
        "memilih mata kuliah",
        "rencana studi",
        "registrasi mata kuliah",
        "pengambilan mata kuliah"
    ],

    "siam": [
        "siam",
        "siam unpri",
        "sistem informasi akademik",
        "sistem informasi akademik mahasiswa",
        "layanan sistem akademik"
    ],

    "jadwal kuliah": [
        "jadwal kuliah",
        "jadwal perkuliahan",
        "melihat jadwal",
        "cek jadwal",
        "jadwal mata kuliah",
        "jadwal kelas"
    ],

    "surat aktif kuliah": [
        "surat aktif kuliah",
        "surat keterangan aktif",
        "surat keterangan mahasiswa aktif",
        "status mahasiswa aktif",
        "bukti aktif kuliah"
    ],

    "ukt": [
        "ukt",
        "uang kuliah",
        "uang kuliah tunggal",
        "biaya kuliah",
        "pembayaran kuliah",
        "pembayaran uang kuliah",
        "uang semester",
        "tagihan kuliah",
        "tagihan semester"
    ],

    "khs": [
        "khs",
        "kartu hasil studi",
        "hasil studi",
        "transkrip nilai semester"
    ],

    "nilai akademik": [
        "nilai akademik",
        "melihat nilai",
        "cek nilai",
        "cek nilai akademik",
        "nilai semester",
        "nilai kuliah",
        "nilai mahasiswa",
        "hasil nilai"
    ],

    "cuti kuliah": [
        "cuti kuliah",
        "izin tidak kuliah",
        "berhenti sementara",
        "penundaan kuliah",
        "cuti akademik"
    ]
}



def normalize_text(text):
    """Membersihkan teks agar lebih mudah dibandingkan."""
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def get_keywords(question: str):
    """Mengambil kata penting dari pertanyaan."""
    words = re.findall(
        r"\b[a-zA-Z0-9]+\b",
        normalize_text(question)
    )

    return [
        word for word in words
        if len(word) >= 2 and word not in STOPWORDS
    ]


def detect_concepts(question: str):
    """Mendeteksi topik berdasarkan sinonim dan variasi kalimat."""
    question = f" {normalize_text(question)} "
    detected = []

    for concept, aliases in CONCEPTS.items():
        all_terms = [concept] + aliases

        for term in all_terms:
            normalized_term = normalize_text(term)

            if f" {normalized_term} " in question:
                detected.append(concept)
                break

    return detected


# Mencari informasi kampus berdasarkan relevansi
def search_information(question: str):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        sql = """
            SELECT
                informasi_kampus.id,
                informasi_kampus.judul,
                informasi_kampus.isi,
                informasi_kampus.sumber,
                informasi_kampus.tanggal_berlaku,
                kategori.nama_kategori
            FROM informasi_kampus
            INNER JOIN kategori
                ON informasi_kampus.kategori_id = kategori.id
            WHERE informasi_kampus.status = 'aktif'
        """

        cursor.execute(sql)
        records = cursor.fetchall()

        keywords = get_keywords(question)
        concepts = detect_concepts(question)

        results = []

        if concepts:
            for record in records:
                title = normalize_text(record["judul"])
                content = normalize_text(record["isi"])

                score = 0

                for concept in concepts:
                    terms = [concept] + CONCEPTS[concept]

                    title_match = any(
                        f" {normalize_text(term)} " in f" {title} "
                        for term in terms
                    )

                    content_match = any(
                        f" {normalize_text(term)} " in f" {content} "
                        for term in terms
                    )

                    if title_match:
                        score += 10
                    elif content_match:
                        score += 5

                if score > 0:
                    record["score"] = score
                    results.append(record)

        else:
            for record in records:
                title = normalize_text(record["judul"])
                content = normalize_text(record["isi"])

                title_words = set(title.split())
                content_words = set(content.split())

                score = 0

                for keyword in keywords:
                    if keyword in title_words:
                        score += 3

                    if keyword in content_words:
                        score += 1

                if score > 0:
                    record["score"] = score
                    results.append(record)

        results.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        return results[:5]

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# Menyimpan percakapan ke database
def save_chat(session_id: str, question: str, answer: str):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        sql = """
            INSERT INTO riwayat_chat
            (session_id, pesan_user, jawaban_ai)
            VALUES (%s, %s, %s)
        """

        cursor.execute(
            sql,
            (session_id, question, answer)
        )

        connection.commit()

    except Exception:
        if connection:
            connection.rollback()
        raise

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()




# Memproses pertanyaan mahasiswa
def process_chat(question: str, session_id: str = None):
    question = question.strip()

    if not question:
        raise ValueError("Pertanyaan tidak boleh kosong.")

    if not session_id:
        session_id = str(uuid.uuid4())

    # Mencari informasi menggunakan Smart Search
    information = search_information(question)

    # Jika informasi tidak ditemukan
    if not information:
        answer = (
            "Maaf, informasi yang kamu tanyakan belum tersedia "
            "dalam basis data CampusAI UNPRI. "
            "Silakan hubungi bagian administrasi kampus "
            "untuk mendapatkan informasi lebih lanjut."
        )

        save_chat(session_id, question, answer)

        return {
            "success": True,
            "session_id": session_id,
            "question": question,
            "answer": answer,
            "answer_mode": "no_information",
            "sources": []
        }

    # Menggunakan informasi database sebagai jawaban utama
    answer = information[0]["isi"]
    answer_mode = "database"

    # Menyiapkan sumber informasi
    sources = [
        {
            "id": item["id"],
            "judul": item["judul"],
            "kategori": item["nama_kategori"]
        }
        for item in information
    ]

    # Menyimpan percakapan ke database
    save_chat(session_id, question, answer)

    return {
        "success": True,
        "session_id": session_id,
        "question": question,
        "answer": answer,
        "answer_mode": answer_mode,
        "sources": sources
    }
