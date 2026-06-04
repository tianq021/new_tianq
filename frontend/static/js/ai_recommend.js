(function () {
    const root = document.getElementById("aiRecommendRoot");
    if (!root) return;

    const page = root.dataset.page || "tools";
    const apiUrl = root.dataset.apiUrl || "/api/ai/tools/recommend";
    const mode = root.dataset.mode || "recommend";
    const embedded = root.dataset.embedded === "true";
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

    function scrollBottom() {
        messages.scrollTop = messages.scrollHeight;
    }

    function createDeleteButton() {
        const button = document.createElement("button");
        button.className = "ai-msg-delete";
        button.type = "button";
        button.title = "删除这条智能回复";
        button.setAttribute("aria-label", "删除这条智能回复");
        button.textContent = "×";
        return button;
    }

    function makeDeletable(item) {
        if (!item || item.querySelector(".ai-msg-delete")) {
            return;
        }

        item.classList.add("ai-deletable");
        item.appendChild(createDeleteButton());
    }

    function enhanceDeletableItems() {
        messages.querySelectorAll(".ai-msg-bot, .ai-tool-card").forEach(makeDeletable);
    }

    function restoreHistory() {
        const html = sessionStorage.getItem(storageKey);

        if (html) {
            messages.innerHTML = html;
            enhanceDeletableItems();
            scrollBottom();
            return;
        }

        enhanceDeletableItems();
    }

    function openPanel() {
        panel.classList.add("open");
        sessionStorage.setItem(openKey, "1");
        if (!embedded) {
            input.focus();
        }
        scrollBottom();
    }

    function closePanel() {
        panel.classList.remove("open");
        sessionStorage.setItem(openKey, "0");
    }

    function setMessageText(messageNode, text) {
        let content = messageNode.querySelector(".ai-msg-content");

        if (!content) {
            messageNode.textContent = "";
            content = document.createElement("span");
            content.className = "ai-msg-content";
            messageNode.appendChild(content);
            makeDeletable(messageNode);
        }

        content.textContent = text;
    }

    function addTextMessage(role, text) {
        const div = document.createElement("div");
        div.className = role === "user" ? "ai-msg ai-msg-user" : "ai-msg ai-msg-bot";

        const content = document.createElement("span");
        content.className = "ai-msg-content";
        content.textContent = text;
        div.appendChild(content);

        if (role !== "user") {
            makeDeletable(div);
        }

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

        makeDeletable(card);
        messages.appendChild(card);
        saveHistory();
        scrollBottom();
    }

    if (btn) {
        btn.addEventListener("click", function () {
            openPanel();
        });
    }

    if (closeBtn) {
        closeBtn.addEventListener("click", function () {
            closePanel();
        });
    }

    messages.addEventListener("click", function (event) {
        const deleteBtn = event.target.closest(".ai-msg-delete");

        if (!deleteBtn) {
            return;
        }

        const item = deleteBtn.closest(".ai-msg-bot, .ai-tool-card");

        if (!item) {
            return;
        }

        item.remove();
        saveHistory();
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
                setMessageText(loading, data.message || "请求失败，请稍后再试。");
                saveHistory();
                return;
            }

            setMessageText(loading, data.reply || "我暂时没有生成回复。");

            if (mode !== "chat" && Array.isArray(data.tools)) {
                data.tools.forEach(addToolCard);
            }

            saveHistory();
            scrollBottom();
        } catch (err) {
            setMessageText(loading, "请求失败，请检查后端接口或网络。");
            saveHistory();
        } finally {
            submitBtn.disabled = false;
        }
    });

    restoreHistory();

    if (embedded) {
        openPanel();
    } else if (sessionStorage.getItem(openKey) === "1") {
        openPanel();
    }
})();
