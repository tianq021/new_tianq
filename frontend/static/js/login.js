const roleInputs = document.querySelectorAll('input[name="role"]');
const roleHint = document.getElementById("roleHint");
const usernameInput = document.getElementById("loginUsername");
const passwordInput = document.getElementById("loginPassword");
const quotePanel = document.querySelector(".quote-panel");
const loginQuote = document.getElementById("loginQuote");
const loginQuoteAuthor = document.getElementById("loginQuoteAuthor");
const ambientBg = document.querySelector(".ambient-bg");

function randomBetween(min, max) {
    return Math.random() * (max - min) + min;
}

function renderRandomBackgroundShapes() {
    if (!ambientBg) {
        return;
    }

    const types = ["circle", "square", "diamond", "line", "ring", "triangle"];
    const colors = [
        "rgba(37, 99, 235, 0.12)",
        "rgba(8, 145, 178, 0.13)",
        "rgba(15, 23, 42, 0.08)",
        "rgba(14, 165, 233, 0.12)"
    ];
    const fragment = document.createDocumentFragment();
    const shapeCount = window.matchMedia("(max-width: 760px)").matches ? 12 : 20;

    ambientBg.querySelectorAll(".shape").forEach(function (shape) {
        shape.remove();
    });

    for (let index = 0; index < shapeCount; index += 1) {
        const type = types[Math.floor(Math.random() * types.length)];
        const shape = document.createElement("span");
        const size = randomBetween(28, type === "line" ? 170 : 130);
        const color = colors[Math.floor(Math.random() * colors.length)];

        shape.className = `shape shape-${type}`;
        shape.style.left = `${randomBetween(-4, 96)}%`;
        shape.style.top = `${randomBetween(-5, 92)}%`;
        shape.style.width = `${size}px`;
        shape.style.height = `${type === "line" ? 2 : size}px`;
        shape.style.opacity = String(randomBetween(0.26, 0.82));
        shape.style.setProperty("--rotate", `${randomBetween(0, 180)}deg`);
        shape.style.setProperty("--tri-size", `${Math.max(24, size / 2)}px`);

        if (type === "line") {
            shape.style.background = `linear-gradient(90deg, transparent, ${color}, transparent)`;
        } else if (type !== "triangle" && type !== "ring") {
            shape.style.background = color;
        }

        fragment.appendChild(shape);
    }

    ambientBg.appendChild(fragment);
}

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

renderRandomBackgroundShapes();

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
