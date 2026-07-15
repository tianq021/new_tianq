if ("scrollRestoration" in window.history) {
    window.history.scrollRestoration = "manual";
}

function randomBetween(min, max) {
    return Math.random() * (max - min) + min;
}

function renderUserBackgroundShapes() {
    const ambientBg = document.querySelector(".user-ambient-bg");
    if (!ambientBg) {
        return;
    }

    const types = ["circle", "square", "ring", "line", "diamond"];
    const shapeCount = window.matchMedia("(max-width: 860px)").matches ? 10 : 16;
    const fragment = document.createDocumentFragment();

    ambientBg.querySelectorAll(".user-bg-shape").forEach(function (shape) {
        shape.remove();
    });

    for (let index = 0; index < shapeCount; index += 1) {
        const type = types[Math.floor(Math.random() * types.length)];
        const shape = document.createElement("span");
        const size = randomBetween(34, type === "line" ? 190 : 150);

        shape.className = `user-bg-shape user-bg-${type}`;
        shape.style.left = `${randomBetween(-5, 96)}%`;
        shape.style.top = `${randomBetween(-6, 94)}%`;
        shape.style.width = `${size}px`;
        shape.style.height = `${type === "line" ? 2 : size}px`;
        shape.style.opacity = String(randomBetween(0.22, 0.62));
        shape.style.setProperty("--rotate", `${randomBetween(0, 180)}deg`);
        fragment.appendChild(shape);
    }

    ambientBg.appendChild(fragment);
}

renderUserBackgroundShapes();

window.addEventListener("load", function () {
    window.scrollTo(0, 0);
});

function formatLocalTime(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hour = String(date.getHours()).padStart(2, '0');
    const minute = String(date.getMinutes()).padStart(2, '0');
    const second = String(date.getSeconds()).padStart(2, '0');

    return `${year}-${month}-${day} ${hour}:${minute}:${second}`;
}

function showLocalTime() {
    const timeElement = document.getElementById('timeText');

    if (!timeElement) {
        return;
    }

    timeElement.innerText = formatLocalTime(new Date());
}

showLocalTime();
setInterval(showLocalTime, 1000);

const userUpdateButton = document.getElementById("userUpdateButton");
const userUpdatePanel = document.getElementById("userUpdatePanel");
const userUpdateClose = document.getElementById("userUpdateClose");
const userUpdateTitle = document.getElementById("userUpdateTitle");
const userUpdateText = document.getElementById("userUpdateText");
const userFeedbackButton = document.getElementById("userFeedbackButton");
const userFeedbackPanel = document.getElementById("userFeedbackPanel");
const userFeedbackClose = document.getElementById("userFeedbackClose");
const userFeedbackForm = document.getElementById("userFeedbackForm");
const userFeedbackContent = document.getElementById("userFeedbackContent");
const userFeedbackStatus = document.getElementById("userFeedbackStatus");

async function openUserUpdate() {
    userUpdatePanel.classList.add("open");
    userUpdatePanel.setAttribute("aria-hidden", "false");
    userUpdateText.textContent = "正在读取...";
    try {
        const response = await fetch("/api/feature-explanations/user");
        const data = await response.json();
        if (!response.ok || !data.success) {
            throw new Error(data.message || "更新消息读取失败");
        }
        userUpdateTitle.textContent = data.data.title || "更新消息";
        userUpdateText.textContent = data.data.content || "";
    } catch (error) {
        userUpdateText.textContent = error.message || "更新消息读取失败";
    }
}

function closeUserUpdate() {
    userUpdatePanel.classList.remove("open");
    userUpdatePanel.setAttribute("aria-hidden", "true");
}

if (userUpdateButton) {
    userUpdateButton.addEventListener("click", openUserUpdate);
}
if (userUpdateClose) {
    userUpdateClose.addEventListener("click", closeUserUpdate);
}

function openUserFeedback() {
    userFeedbackPanel.classList.add("open");
    userFeedbackPanel.setAttribute("aria-hidden", "false");
    userFeedbackStatus.textContent = "";
    userFeedbackContent.focus();
}

function closeUserFeedback() {
    userFeedbackPanel.classList.remove("open");
    userFeedbackPanel.setAttribute("aria-hidden", "true");
}

if (userFeedbackButton) {
    userFeedbackButton.addEventListener("click", openUserFeedback);
}
if (userFeedbackClose) {
    userFeedbackClose.addEventListener("click", closeUserFeedback);
}
if (userFeedbackForm) {
    userFeedbackForm.addEventListener("submit", async function (event) {
        event.preventDefault();
        const content = userFeedbackContent.value.trim();
        if (!content) {
            userFeedbackStatus.textContent = "请输入反馈内容";
            return;
        }
        const submitButton = userFeedbackForm.querySelector('[type="submit"]');
        submitButton.disabled = true;
        userFeedbackStatus.textContent = "正在提交...";
        try {
            const response = await fetch("/api/feedback", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ content: content })
            });
            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.message || "提交失败");
            }
            userFeedbackContent.value = "";
            userFeedbackStatus.textContent = "反馈已提交，谢谢";
        } catch (error) {
            userFeedbackStatus.textContent = error.message || "提交失败";
        } finally {
            submitButton.disabled = false;
        }
    });
}
