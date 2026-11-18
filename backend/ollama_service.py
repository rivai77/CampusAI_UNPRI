
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:1b"


def generate_answer(question: str, context: str) -> str:
    """Menghasilkan jawaban berdasarkan informasi dari database."""

    prompt = f"""Kamu adalah CampusAI, asisten informasi Universitas Prima Indonesia (UNPRI).

TUGAS:
Jawab pertanyaan mahasiswa hanya berdasarkan INFORMASI DATABASE.

INFORMASI DATABASE:
{context}

PERTANYAAN MAHASISWA:
{question}

ATURAN WAJIB:
1. Gunakan hanya fakta yang tertulis dalam INFORMASI DATABASE.
2. Dilarang membuat langkah-langkah prosedur sendiri.
3. Dilarang menambahkan alamat website, nama menu, tombol, biaya, jadwal, atau persyaratan yang tidak tertulis dalam database.
4. Jangan menganggap fitur SIAM pasti memiliki menu tertentu jika tidak disebutkan dalam database.
5. Jika informasi hanya menjelaskan sebagian, sampaikan hanya bagian yang diketahui.
6. Jika mahasiswa meminta prosedur rinci tetapi database hanya memberikan informasi umum, jelaskan bahwa prosedur rinci belum tersedia.
7. Jangan mengarang informasi untuk membuat jawaban terlihat lengkap.
8. Jawab dalam bahasa Indonesia yang sopan, singkat, dan mudah dipahami.
9. Maksimal 3 kalimat.

JAWABAN:"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0,
    "num_predict": 80,
    "top_p": 0.5,
    "repeat_penalty": 1.1
                }
            },
            timeout=120
        )

        response.raise_for_status()

        result = response.json()
        answer = result.get("response", "").strip()

        if not answer:
            raise RuntimeError("Ollama tidak menghasilkan jawaban.")

        return answer

    except requests.exceptions.Timeout:
        raise RuntimeError("Ollama membutuhkan waktu terlalu lama.")

    except requests.exceptions.ConnectionError:
        raise RuntimeError("Tidak dapat terhubung ke Ollama.")

    except requests.exceptions.RequestException as error:
        raise RuntimeError(f"Kesalahan Ollama: {error}")

    except (ValueError, TypeError):
        raise RuntimeError("Respons Ollama tidak dapat dibaca.")
