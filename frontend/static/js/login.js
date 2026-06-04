const roleInputs = document.querySelectorAll('input[name="role"]');
const roleHint = document.getElementById("roleHint");
const passwordInput = document.getElementById("adminPassword");
const quotePanel = document.querySelector(".quote-panel");
const loginQuote = document.getElementById("loginQuote");
const loginQuoteAuthor = document.getElementById("loginQuoteAuthor");

function updateLoginMode() {
    const selectedRole = document.querySelector('input[name="role"]:checked')?.value || "user";
    const isAdmin = selectedRole === "admin";

    if (roleHint) {
        roleHint.textContent = isAdmin
            ? "管理员模式：需要输入管理员密码"
            : "用户模式：直接进入工具工作台";
    }

    if (passwordInput) {
        passwordInput.placeholder = isAdmin ? "请输入管理员密码" : "普通用户可留空";
        passwordInput.toggleAttribute("required", isAdmin);
    }
}

roleInputs.forEach(function (input) {
    input.addEventListener("change", updateLoginMode);
});

updateLoginMode();

async function loadLoginQuote() {
    if (!quotePanel || !loginQuote || !quotePanel.dataset.quoteUrl) {
        return;
    }

    try {
        const response = await fetch(quotePanel.dataset.quoteUrl);
        if (!response.ok) {
            return;
        }

        const data = await response.json();
        if (data && data.quote) {
            loginQuote.textContent = data.quote;
        }
        if (loginQuoteAuthor && data && data.author) {
            loginQuoteAuthor.textContent = `—— ${data.author}`;
        }
    } catch (error) {
        return;
    }
}

loadLoginQuote();
