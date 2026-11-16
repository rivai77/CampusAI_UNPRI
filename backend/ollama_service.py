
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:1b"


def generate_answer(question: str, context: str) -> str:
    """Menghasilkan jawaban berdasarkan informasi dari database."""

    prompt = f"""Kamu adalah CampusAI, asisten informasi Universitas Prima Indonesia (UNPRI).

Gunakan informasi berikut untuk menjawab pertanyaan mahasiswa.

INFORMASI:
{context}

PERTANYAAN:
{question}

PETUNJUK:
- Jawab dalam bahasa Indonesia.
- Gunakan hanya fakta yang tertulis pada INFORMASI.
- Jangan menambahkan langkah, biaya, jadwal, atau persyaratan baru.
- Jika informasi hanya menjelaskan sebagian, jawab sebatas informasi tersebut.
- Jangan mengatakan informasi tidak tersedia jika jawabannya ada pada INFORMASI.
- Jawab secara langsung dan maksimal 2 kalimat.

JAWABAN:"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 120,
                    "top_p": 0.8
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
