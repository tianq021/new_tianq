const roleInputs = document.querySelectorAll('input[name="role"]');
const roleHint = document.getElementById("roleHint");
const usernameInput = document.getElementById("loginUsername");
const passwordInput = document.getElementById("loginPassword");
const quotePanel = document.querySelector(".quote-panel");
const loginQuote = document.getElementById("loginQuote");
const loginQuoteAuthor = document.getElementById("loginQuoteAuthor");

function updateLoginMode() {
    const selectedRole = document.querySelector('input[name="role"]:checked')?.value || "user";
    const isAdmin = selectedRole === "admin";

    if (roleHint) {
        roleHint.textContent = isAdmin
            ? "管理员模式：使用管理员账号登录"
            : "用户模式：使用普通用户账号登录";
    }

    if (usernameInput && !usernameInput.value) {
        usernameInput.placeholder = isAdmin ? "管理员用户名" : "普通用户名";
    }

    if (passwordInput) {
        passwordInput.placeholder = "请输入密码";
        passwordInput.required = true;
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
