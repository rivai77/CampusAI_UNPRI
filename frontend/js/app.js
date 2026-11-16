
const API_URL = "http://127.0.0.1:8000";

const chatForm = document.getElementById("chatForm");
const questionInput = document.getElementById("questionInput");
const messages = document.getElementById("messages");
const welcomeScreen = document.getElementById("welcomeScreen");
const sendBtn = document.getElementById("sendBtn");
const connectionStatus = document.getElementById("connectionStatus");

const newChatBtn = document.getElementById("newChatBtn");
const mobileMenuBtn = document.getElementById("mobileMenuBtn");
const sidebar = document.getElementById("sidebar");

let sessionId = null;
let isSending = false;


// Memeriksa koneksi backend dan database
async function checkConnection() {
    try {
        const response = await fetch(`${API_URL}/api/health`);

        if (!response.ok) {
            throw new Error("Backend tidak tersedia");
        }

        const result = await response.json();

        if (result.database === "connected") {
            connectionStatus.textContent = "Backend dan database terhubung";
            connectionStatus.classList.add("connected");
            connectionStatus.classList.remove("disconnected");
        } else {
            connectionStatus.textContent = "Database belum terhubung";
            connectionStatus.classList.add("disconnected");
            connectionStatus.classList.remove("connected");
        }

    } catch (error) {
        connectionStatus.textContent = "Backend tidak terhubung";
        connectionStatus.classList.add("disconnected");
        connectionStatus.classList.remove("connected");
    }
}


// Menentukan label berdasarkan mode jawaban
function getAnswerMode(mode) {
    const modes = {
        ollama: {
            label: "Dijawab oleh AI",
            className: "mode-ollama"
        },
        database_fallback: {
            label: "Jawaban dari Database",
            className: "mode-database"
        },
        no_information: {
            label: "Informasi belum tersedia",
            className: "mode-unavailable"
        }
    };

    return modes[mode] || {
        label: "CampusAI",
        className: "mode-default"
    };
}


// Membuat pesan chat
function addMessage(type, text, sources = [], answerMode = null) {
    const message = document.createElement("div");
    message.className = `message ${type}`;

    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.textContent = type === "user" ? "👤" : "🎓";

    const content = document.createElement("div");
    content.className = "message-content";

    // Membuat gelembung pesan
    const bubble = document.createElement("div");
    bubble.className = "message-bubble";
    bubble.textContent = text;

    content.appendChild(bubble);

    if (type === "bot") {

        // Menampilkan mode jawaban
        if (answerMode) {
            const modeInfo = getAnswerMode(answerMode);

            const modeBadge = document.createElement("div");
            modeBadge.className = `answer-mode ${modeInfo.className}`;
            modeBadge.textContent = modeInfo.label;

            content.appendChild(modeBadge);
        }

        // Menampilkan sumber informasi
        if (sources.length > 0) {
            const sourceContainer = document.createElement("div");
            sourceContainer.className = "source-list";

            const label = document.createElement("div");
            label.className = "source-heading";
            label.textContent = "📚 Sumber informasi";

            sourceContainer.appendChild(label);

            sources.forEach(source => {
                const item = document.createElement("div");
                item.className = "source-item";

                const title = document.createElement("strong");
                title.textContent = source.judul;

                const category = document.createElement("span");
                category.textContent = source.kategori;

                item.appendChild(title);
                item.appendChild(category);

                sourceContainer.appendChild(item);
            });

            content.appendChild(sourceContainer);
        }
    }

    if (type === "user") {
        message.appendChild(content);
        message.appendChild(avatar);
    } else {
        message.appendChild(avatar);
        message.appendChild(content);
    }

    messages.appendChild(message);

    message.scrollIntoView({
        behavior: "smooth",
        block: "end"
    });
}


// Menampilkan indikator AI sedang berpikir
function showTyping() {
    const typing = document.createElement("div");

    typing.className = "typing";
    typing.id = "typingIndicator";
    typing.textContent = "🎓 CampusAI sedang menyiapkan jawaban...";

    messages.appendChild(typing);

    typing.scrollIntoView({
        behavior: "smooth",
        block: "end"
    });
}


// Menghapus indikator AI
function hideTyping() {
    const typing = document.getElementById("typingIndicator");

    if (typing) {
        typing.remove();
    }
}


// Mengirim pertanyaan ke backend
async function sendQuestion(question) {
    question = question.trim();

    if (!question || isSending) return;

    isSending = true;

    sendBtn.disabled = true;
    welcomeScreen.style.display = "none";

    addMessage("user", question);

    questionInput.value = "";
    questionInput.style.height = "auto";

    showTyping();

    try {
        const response = await fetch(`${API_URL}/api/chat`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                question: question,
                session_id: sessionId
            })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(
                result.detail || "Terjadi kesalahan pada server."
            );
        }

        if (!result.success) {
            throw new Error("Pertanyaan gagal diproses.");
        }

        // Menyimpan sesi percakapan
        sessionId = result.session_id;

        hideTyping();

        // Menampilkan jawaban beserta sumber dan mode
        addMessage(
            "bot",
            result.answer,
            result.sources || [],
            result.answer_mode
        );

    } catch (error) {
        hideTyping();

        addMessage(
            "bot",
            `Maaf, terjadi kesalahan: ${error.message}. Pastikan backend CampusAI sedang berjalan.`
        );

        console.error("Chat error:", error);

    } finally {
        isSending = false;
        sendBtn.disabled = false;
        questionInput.focus();
    }
}


// Mengirim pesan melalui tombol
chatForm.addEventListener("submit", function(event) {
    event.preventDefault();
    sendQuestion(questionInput.value);
});


// Enter untuk mengirim pesan
questionInput.addEventListener("keydown", function(event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        chatForm.requestSubmit();
    }
});


// Mengatur tinggi textarea otomatis
questionInput.addEventListener("input", function() {
    this.style.height = "auto";
    this.style.height = `${Math.min(this.scrollHeight, 120)}px`;
});


// Mengirim pertanyaan dari rekomendasi
document.querySelectorAll(".suggestion").forEach(button => {
    button.addEventListener("click", function() {
        sendQuestion(this.dataset.question);
    });
});


// Memulai percakapan baru
newChatBtn.addEventListener("click", function() {
    sessionId = null;

    messages.innerHTML = "";
    welcomeScreen.style.display = "block";

    questionInput.value = "";

    sidebar.classList.remove("open");

    questionInput.focus();
});


// Membuka dan menutup sidebar pada HP
mobileMenuBtn.addEventListener("click", function() {
    sidebar.classList.toggle("open");
});


// Memeriksa koneksi ketika halaman dibuka
checkConnection();
