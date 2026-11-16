
const API_URL = "http://127.0.0.1:8000";

const loginForm = document.getElementById("loginForm");
const loginBtn = document.getElementById("loginBtn");
const errorMessage = document.getElementById("errorMessage");

loginForm.addEventListener("submit", async function(event) {
    event.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;

    errorMessage.textContent = "";
    loginBtn.disabled = true;
    loginBtn.textContent = "Memproses...";

    try {
        const response = await fetch(`${API_URL}/api/admin/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                username: username,
                password: password
            })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || "Login gagal.");
        }

        // Menyimpan token dan identitas admin di browser
        sessionStorage.setItem("adminToken", result.access_token);
        sessionStorage.setItem("adminData", JSON.stringify(result.admin));

        window.location.href = "admin-dashboard.html";

    } catch (error) {
        errorMessage.textContent = error.message;
    } finally {
        loginBtn.disabled = false;
        loginBtn.textContent = "Login Admin";
    }
});
