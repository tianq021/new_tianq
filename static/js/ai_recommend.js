(function () {
    const root = document.getElementById("aiRecommendRoot");
    if (!root) return;

    const page = root.dataset.page || "tools";
    const apiUrl = root.dataset.apiUrl || "/api/ai/tools/recommend";
    const mode = root.dataset.mode || "recommend";
    const storageKey = "ai_recommend_history_" + page;
    const openKey = "ai_recommend_open_" + page;

    const btn = document.getElementById("aiRecommendBtn");
    const panel = document.getElementById("aiRecommendPanel");
    const closeBtn = document.getElementById("aiRecommendClose");
    const form = document.getElementById("aiRecommendForm");
    const input = document.getElementById("aiRecommendInput");
    const messages = document.getElementById("aiRecommendMessages");

    function saveHistory() {
        sessionStorage.setItem(storageKey, messages.innerHTML);
    }

    function restoreHistory() {
        const html = sessionStorage.getItem(storageKey);
        if (html) {
            messages.innerHTML = html;
            scrollBottom();
        }
    }

    function scrollBottom() {
        messages.scrollTop = messages.scrollHeight;
    }

    function openPanel() {
        panel.classList.add("open");
        sessionStorage.setItem(openKey, "1");
        input.focus();
        scrollBottom();
    }

    function closePanel() {
        panel.classList.remove("open");
        sessionStorage.setItem(openKey, "0");
    }

    function addTextMessage(role, text) {
        const div = document.createElement("div");
        div.className = role === "user" ? "ai-msg ai-msg-user" : "ai-msg ai-msg-bot";
        div.textContent = text;
        messages.appendChild(div);
        saveHistory();
        scrollBottom();
        return div;
    }

    function addToolCard(tool) {
        const card = document.createElement("div");
        card.className = "ai-tool-card";

        const title = document.createElement("div");
        title.className = "ai-tool-card-title";
        title.textContent = tool.title || "推荐工具";

        const desc = document.createElement("div");
        desc.className = "ai-tool-card-desc";
        desc.textContent = tool.reason || tool.desc || "";

        card.appendChild(title);
        card.appendChild(desc);

        if (tool.url) {
            const link = document.createElement("a");
            link.href = tool.url;
            link.dataset.target = tool.target || "";
            link.textContent = tool.link_text || "打开工具";

            if (tool.external) {
                link.target = "_blank";
                link.rel = "noopener";
            }

            card.appendChild(link);
        }

        messages.appendChild(card);
        saveHistory();
        scrollBottom();
    }

    btn.addEventListener("click", function () {
        openPanel();
    });

    closeBtn.addEventListener("click", function () {
        closePanel();
    });

    form.addEventListener("submit", async function (event) {
        event.preventDefault();

        const message = input.value.trim();
        if (!message) return;

        addTextMessage("user", message);
        input.value = "";

        const loadingText = mode === "chat" ? "正在回复..." : "正在分析适合你的工具...";
        const loading = addTextMessage("bot", loadingText);

        const submitBtn = form.querySelector("button");
        submitBtn.disabled = true;

        try {
            const res = await fetch(apiUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    message: message
                })
            });

            const data = await res.json();

            if (!data.success) {
                loading.textContent = data.message || "请求失败，请稍后再试。";
                saveHistory();
                return;
            }

            loading.textContent = data.reply || "我暂时没有生成回复。";

            if (mode !== "chat" && Array.isArray(data.tools)) {
                data.tools.forEach(addToolCard);
            }

            saveHistory();
            scrollBottom();

        } catch (err) {
            loading.textContent = "请求失败，请检查后端接口或网络。";
            saveHistory();
        } finally {
            submitBtn.disabled = false;
        }
    });

    restoreHistory();

    if (sessionStorage.getItem(openKey) === "1") {
        openPanel();
    }
})();
