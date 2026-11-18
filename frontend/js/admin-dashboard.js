
const API_URL = "http://127.0.0.1:8000";

// Mengambil token dan identitas admin dari sesi login
const token = sessionStorage.getItem("adminToken");
const adminData = JSON.parse(
    sessionStorage.getItem("adminData") || "null"
);

// Jika belum login, arahkan kembali ke halaman login
if (!token || !adminData) {
    window.location.href = "admin-login.html";
}

const informationTable = document.getElementById("informationTable");
const categoryTable = document.getElementById("categoryTable");

const informationModal = document.getElementById("informationModal");
const categoryModal = document.getElementById("categoryModal");

let informationData = [];
let categoryData = [];

// Mengamankan teks sebelum ditampilkan ke dalam HTML
function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, function(character) {
        return {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#039;"
        }[character];
    });
}

// Mengirim permintaan ke API
async function apiRequest(endpoint, options = {}) {
    const response = await fetch(`${API_URL}${endpoint}`, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {}),
            ...(options.auth ? {
                "Authorization": `Bearer ${token}`
            } : {})
        }
    });

    const result = await response.json().catch(() => ({}));

    if (response.status === 401) {
        sessionStorage.removeItem("adminToken");
        sessionStorage.removeItem("adminData");
        window.location.href = "admin-login.html";
        throw new Error("Sesi login berakhir. Silakan login kembali.");
    }

    if (!response.ok) {
        throw new Error(
            result.detail || result.message || "Terjadi kesalahan pada server."
        );
    }

    return result;
}

// Menampilkan identitas admin
function displayAdmin() {
    document.getElementById("adminInfo").textContent =
        `${adminData.nama}\nUsername: ${adminData.username}\nRole: ${adminData.role}`;
}

// Mengambil data kategori
async function loadCategories() {
    const result = await apiRequest("/api/kategori");

    categoryData = result.data || [];

    document.getElementById("totalCategories").textContent =
        categoryData.length;

    categoryTable.innerHTML = "";

    if (categoryData.length === 0) {
        categoryTable.innerHTML = `
            <tr><td colspan="3" class="empty-state">
                Belum ada kategori.
            </td></tr>`;
    } else {
        categoryData.forEach((category, index) => {
            categoryTable.innerHTML += `
                <tr>
                    <td>${index + 1}</td>
                    <td>${escapeHTML(category.nama_kategori)}</td>
                    <td>${escapeHTML(category.deskripsi || "-")}</td>
                </tr>`;
        });
    }

    // Memperbarui pilihan kategori pada form informasi
    const categorySelect = document.getElementById("informationCategory");

    categorySelect.innerHTML = '<option value="">Pilih kategori</option>';

    categoryData.forEach(category => {
        categorySelect.innerHTML += `
            <option value="${category.id}">
                ${escapeHTML(category.nama_kategori)}
            </option>`;
    });
}

// Mengambil data informasi kampus
async function loadInformation() {
    const result = await apiRequest("/api/informasi");

    informationData = result.data || [];

    document.getElementById("totalInformation").textContent =
        informationData.length;

    document.getElementById("activeInformation").textContent =
        informationData.filter(item => item.status === "aktif").length;

    informationTable.innerHTML = "";

    if (informationData.length === 0) {
        informationTable.innerHTML = `
            <tr><td colspan="5" class="empty-state">
                Belum ada informasi kampus.
            </td></tr>`;
        return;
    }

    
informationData.forEach((item, index) => {
    const status = item.status || "nonaktif";

    informationTable.innerHTML += `
        <tr>
            <td>${index + 1}</td>
            <td>${escapeHTML(item.judul)}</td>
            <td>${escapeHTML(item.nama_kategori)}</td>
            <td>
                <span class="status ${status}">
                    ${escapeHTML(status)}
                </span>
            </td>
            <td>
                <div class="action-buttons">
                    <button
                        class="secondary-button"
                        onclick="editInformation(${Number(item.id)})">
                        Edit
                    </button>

                    <button
                        class="${status === "aktif" ? "danger-button" : "primary-button"}"
                        onclick="toggleInformationStatus(${Number(item.id)})">
                        ${status === "aktif" ? "Nonaktifkan" : "Aktifkan"}
                    </button>
                </div>
            </td>
        </tr>`;
});

}

// Memuat seluruh data dashboard
async function loadDashboard() {
    informationTable.innerHTML = `
        <tr><td colspan="5" class="empty-state">Memuat data...</td></tr>`;

    try {
        await loadCategories();
        await loadInformation();
    } catch (error) {
        informationTable.innerHTML = `
            <tr><td colspan="5" class="empty-state">
                ${escapeHTML(error.message)}
            </td></tr>`;

        alert(error.message);
    }
}

// Membuka form tambah informasi
document.getElementById("addInformationBtn").addEventListener("click", function() {
    document.getElementById("informationForm").reset();
    document.getElementById("informationId").value = "";
    document.getElementById("informationModalTitle").textContent =
        "Tambah Informasi";
    document.getElementById("informationMessage").textContent = "";

    informationModal.classList.add("show");
});

// Membuka form edit dengan data yang dipilih
window.editInformation = function(id) {
    const item = informationData.find(data => Number(data.id) === Number(id));

    if (!item) return;

    document.getElementById("informationId").value = item.id;
    document.getElementById("informationTitle").value = item.judul;
    document.getElementById("informationCategory").value = item.kategori_id;
    document.getElementById("informationContent").value = item.isi;
    document.getElementById("informationSource").value = item.sumber || "";
    document.getElementById("informationDate").value =
        item.tanggal_berlaku
            ? String(item.tanggal_berlaku).substring(0, 10)
            : "";
    document.getElementById("informationStatus").value =
        item.status || "aktif";

    document.getElementById("informationModalTitle").textContent =
        "Edit Informasi";

    document.getElementById("informationMessage").textContent = "";

    informationModal.classList.add("show");
};

// Menyimpan informasi baru atau perubahan informasi
document.getElementById("informationForm").addEventListener("submit", async function(event) {
    event.preventDefault();

    const id = document.getElementById("informationId").value;
    const message = document.getElementById("informationMessage");
    const saveButton = document.getElementById("saveInformationBtn");

    const payload = {
        kategori_id: Number(document.getElementById("informationCategory").value),
        judul: document.getElementById("informationTitle").value.trim(),
        isi: document.getElementById("informationContent").value.trim(),
        sumber: document.getElementById("informationSource").value.trim() || null,
        tanggal_berlaku: document.getElementById("informationDate").value || null,
        status: document.getElementById("informationStatus").value
    };

    saveButton.disabled = true;
    message.textContent = "Menyimpan...";
    message.className = "form-message";

    try {
        const result = await apiRequest(
            id ? `/api/informasi/${id}` : "/api/informasi",
            {
                method: id ? "PUT" : "POST",
                auth: true,
                body: JSON.stringify(payload)
            }
        );

        message.textContent = result.message || "Informasi berhasil disimpan.";
        message.className = "form-message success-message";

        await loadInformation();

        setTimeout(() => informationModal.classList.remove("show"), 600);

    } catch (error) {
        message.textContent = error.message;
        message.className = "form-message error-message";
    } finally {
        saveButton.disabled = false;
    }
});

// Menghapus informasi kampus
// Mengaktifkan atau menonaktifkan informasi tanpa menghapus data
window.toggleInformationStatus = async function(id) {
    const item = informationData.find(
        data => Number(data.id) === Number(id)
    );

    if (!item) {
        alert("Data informasi tidak ditemukan.");
        return;
    }

    const newStatus = item.status === "aktif" ? "nonaktif" : "aktif";

    const action = newStatus === "aktif"
        ? "mengaktifkan"
        : "menonaktifkan";

    const confirmed = confirm(
        `Apakah kamu yakin ingin ${action} informasi "${item.judul}"?`
    );

    if (!confirmed) return;

    // Mempertahankan data lama dan hanya mengubah status
    const payload = {
        kategori_id: Number(item.kategori_id),
        judul: item.judul,
        isi: item.isi,
        sumber: item.sumber || null,
        tanggal_berlaku: item.tanggal_berlaku
            ? String(item.tanggal_berlaku).substring(0, 10)
            : null,
        status: newStatus
    };

    try {
        const result = await apiRequest(`/api/informasi/${id}`, {
            method: "PUT",
            auth: true,
            body: JSON.stringify(payload)
        });

        alert(
            result.message ||
            `Informasi berhasil ${action}.`
        );

        await loadInformation();

    } catch (error) {
        alert(error.message);
    }
};

// Membuka form kategori
document.getElementById("addCategoryBtn").addEventListener("click", function() {
    document.getElementById("categoryForm").reset();
    document.getElementById("categoryMessage").textContent = "";
    categoryModal.classList.add("show");
});

// Menyimpan kategori baru
document.getElementById("categoryForm").addEventListener("submit", async function(event) {
    event.preventDefault();

    const message = document.getElementById("categoryMessage");
    const saveButton = document.getElementById("saveCategoryBtn");

    const payload = {
        nama_kategori: document.getElementById("categoryName").value.trim(),
        deskripsi: document.getElementById("categoryDescription").value.trim() || null
    };

    saveButton.disabled = true;
    message.textContent = "Menyimpan...";
    message.className = "form-message";

    try {
        const result = await apiRequest("/api/kategori", {
            method: "POST",
            auth: true,
            body: JSON.stringify(payload)
        });

        message.textContent = result.message || "Kategori berhasil ditambahkan.";
        message.className = "form-message success-message";

        await loadCategories();

        setTimeout(() => categoryModal.classList.remove("show"), 600);

    } catch (error) {
        message.textContent = error.message;
        message.className = "form-message error-message";
    } finally {
        saveButton.disabled = false;
    }
});

// Menutup modal
document.getElementById("closeInformationModal").addEventListener("click", () => {
    informationModal.classList.remove("show");
});

document.getElementById("closeCategoryModal").addEventListener("click", () => {
    categoryModal.classList.remove("show");
});

// Navigasi menu
document.getElementById("dashboardMenu").addEventListener("click", () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
});

document.getElementById("informationMenu").addEventListener("click", () => {
    document.getElementById("informationPanel").scrollIntoView({
        behavior: "smooth"
    });
});

document.getElementById("categoryMenu").addEventListener("click", () => {
    document.getElementById("categoryPanel").scrollIntoView({
        behavior: "smooth"
    });
});

// Logout admin
document.getElementById("logoutBtn").addEventListener("click", function() {
    if (confirm("Apakah kamu yakin ingin keluar dari dashboard?")) {
        sessionStorage.removeItem("adminToken");
        sessionStorage.removeItem("adminData");
        window.location.href = "admin-login.html";
    }
});

// Jalankan dashboard
if (token && adminData) {
    displayAdmin();
    loadDashboard();
}
