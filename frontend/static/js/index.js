if ("scrollRestoration" in window.history) {
    window.history.scrollRestoration = "manual";
}

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
