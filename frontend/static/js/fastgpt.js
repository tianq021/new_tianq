document.addEventListener("DOMContentLoaded", function () {
    const toolItems = document.querySelectorAll(".tool-link-item");
    const toolRows = document.querySelectorAll(".tool-link-row");
    const favoriteToolList = document.getElementById("favoriteToolList");
    const allToolList = document.getElementById("allToolList");
    const favoriteToolsEmpty = document.getElementById("favoriteToolsEmpty");
    const featureExplanationButton = document.getElementById("featureExplanationButton");
    const featureExplanationPanel = document.getElementById("featureExplanationPanel");
    const featureExplanationClose = document.getElementById("featureExplanationClose");
    const featureExplanationTitle = document.getElementById("featureExplanationTitle");
    const featureExplanationText = document.getElementById("featureExplanationText");
    const chatWorkspace = document.querySelector(".chat-workspace");
    const chatTitle = document.getElementById("chatTitle");
    const chatMessages = document.getElementById("mainChatMessages");
    const chatForm = document.getElementById("fastgptMainChatForm");
    const chatInput = document.getElementById("fastgptMainChatInput");
    const chatSubmit = document.getElementById("fastgptMainChatSubmit");
    const openButton = document.getElementById("openSelectedTool");
    const exportCurrentButton = document.getElementById("exportCurrentChat");
    const exportAllButton = document.getElementById("exportAllChats");
    const clearCurrentButton = document.getElementById("clearCurrentChat");
    const historyPrefix = "fastgpt_main_chat_history_";
    let selectedUrl = "";
    let selectedId = "";
    let selectedTitle = "";
    let requestRunning = false;
    let favoriteIds = new Set();
    const historySaveTimers = new Map();

    async function openFeatureExplanation() {
        featureExplanationPanel.classList.add("open");
        featureExplanationPanel.setAttribute("aria-hidden", "false");
        featureExplanationText.textContent = "正在读取...";
        try {
            const response = await fetch("/api/feature-explanations/fastgpt");
            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.message || "功能解释读取失败");
            }
            featureExplanationTitle.textContent = data.data.title || "功能解释";
            featureExplanationText.textContent = data.data.content || "";
        } catch (error) {
            featureExplanationText.textContent = error.message || "功能解释读取失败";
        }
    }

    function closeFeatureExplanation() {
        featureExplanationPanel.classList.remove("open");
        featureExplanationPanel.setAttribute("aria-hidden", "true");
    }

    async function loadFavoriteIds() {
        try {
            const response = await fetch("/api/ai/favorites");
            const data = await response.json();
            favoriteIds = new Set(
                response.ok && data.success && Array.isArray(data.favorites)
                    ? data.favorites.map(String)
                    : []
            );
        } catch (error) {
            favoriteIds = new Set();
        }
    }

    function renderFavoriteTools() {
        if (!favoriteToolList || !allToolList) {
            return;
        }

        toolRows.forEach(function (row) {
            const toolId = row.dataset.toolId || "";
            const isFavorite = favoriteIds.has(toolId);
            const toggle = row.querySelector(".favorite-toggle");

            (isFavorite ? favoriteToolList : allToolList).appendChild(row);
            if (toggle) {
                toggle.textContent = isFavorite ? "★" : "☆";
                toggle.classList.toggle("active", isFavorite);
                toggle.setAttribute("aria-pressed", String(isFavorite));
                toggle.title = isFavorite ? "从常用中移除" : "添加到常用";
                toggle.setAttribute("aria-label", toggle.title);
            }
        });

        if (favoriteToolsEmpty) {
            favoriteToolsEmpty.hidden = favoriteToolList.children.length > 0;
        }
    }

    async function toggleFavorite(toolId, button) {
        const removing = favoriteIds.has(toolId);
        button.disabled = true;

        try {
            const response = await fetch(
                `/api/ai/favorites/${encodeURIComponent(toolId)}`,
                { method: removing ? "DELETE" : "POST" }
            );
            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.message || "常用设置保存失败");
            }

            if (removing) {
                favoriteIds.delete(toolId);
            } else {
                favoriteIds.add(toolId);
            }
            renderFavoriteTools();
        } catch (error) {
            console.error("保存常用 AI 失败", error);
        } finally {
            button.disabled = false;
        }
    }

    function getSessionId() {
        return selectedId || "fastgpt-default";
    }

    function getSessionKey(toolId) {
        return historyPrefix + (toolId || "fastgpt-default");
    }

    function getToolTitle(toolId) {
        const item = Array.from(toolItems).find(function (toolItem) {
            return toolItem.dataset.id === toolId;
        });
        return item ? item.dataset.title || toolId : toolId;
    }

    function normalizeExportText(text) {
        return (text || "")
            .replace(/\u00a0/g, " ")
            .replace(/[ \t]+\n/g, "\n")
            .replace(/\n{3,}/g, "\n\n")
            .trim();
    }

    function historyHtmlToMarkdown(html, title, toolId) {
        const container = document.createElement("div");
        container.innerHTML = html || "";
        const sections = [
            "# " + (title || toolId || "FastGPT 对话"),
            "",
            "- 工具编号：" + (toolId || "fastgpt-default"),
            ""
        ];

        container.querySelectorAll(".chat-message").forEach(function (message) {
            const role = message.classList.contains("user") ? "用户" : "助手";
            const bubble = message.querySelector(".bubble");
            const toolCard = message.querySelector(".chat-tool-card");

            if (bubble) {
                const text = normalizeExportText(bubble.textContent);
                if (text) {
                    sections.push("## " + role, "", text, "");
                }
                return;
            }

            if (toolCard) {
                const cardTitle = normalizeExportText(
                    (toolCard.querySelector(".chat-tool-card-title") || {}).textContent
                );
                const cardDesc = normalizeExportText(
                    (toolCard.querySelector(".chat-tool-card-desc") || {}).textContent
                );
                const link = toolCard.querySelector("a[href]");
                sections.push("## 助手推荐", "");
                if (cardTitle) sections.push("**" + cardTitle + "**", "");
                if (cardDesc) sections.push(cardDesc, "");
                if (link) sections.push("[打开工具](" + link.href + ")", "");
                return;
            }

            const fallback = normalizeExportText(message.textContent);
            if (fallback) {
                sections.push("## " + role, "", fallback, "");
            }
        });

        return normalizeExportText(sections.join("\n")) + "\n";
    }

    function safeFilename(value) {
        return (value || "FastGPT")
            .replace(/[<>:"/\\|?*\u0000-\u001f]/g, "_")
            .replace(/[. ]+$/g, "")
            .slice(0, 80) || "FastGPT";
    }

    function timestampForFilename() {
        const now = new Date();
        const pad = function (value) {
            return String(value).padStart(2, "0");
        };
        return (
            now.getFullYear() +
            pad(now.getMonth() + 1) +
            pad(now.getDate()) +
            "_" +
            pad(now.getHours()) +
            pad(now.getMinutes()) +
            pad(now.getSeconds())
        );
    }

    function downloadMarkdown(filename, content) {
        const blob = new Blob(["\ufeff", content], {
            type: "text/markdown;charset=utf-8"
        });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.setTimeout(function () {
            URL.revokeObjectURL(url);
        }, 0);
    }

    function exportCurrentChat() {
        saveCurrentSession();
        const toolId = getSessionId();
        const title = selectedTitle || getToolTitle(toolId) || "FastGPT 对话";
        const html = chatMessages ? chatMessages.innerHTML : "";
        const markdown = historyHtmlToMarkdown(html, title, toolId);
        downloadMarkdown(
            safeFilename(title) + "_聊天记录_" + timestampForFilename() + ".md",
            markdown
        );
    }

    function exportAllChats() {
        saveCurrentSession();
        const records = [];

        for (let index = 0; index < sessionStorage.length; index += 1) {
            const key = sessionStorage.key(index);
            if (!key || !key.startsWith(historyPrefix)) {
                continue;
            }

            const toolId = key.slice(historyPrefix.length) || "fastgpt-default";
            records.push({
                toolId: toolId,
                title: getToolTitle(toolId),
                html: sessionStorage.getItem(key) || ""
            });
        }

        records.sort(function (left, right) {
            return (left.title || left.toolId).localeCompare(
                right.title || right.toolId,
                "zh-CN"
            );
        });

        if (records.length === 0 && chatMessages) {
            records.push({
                toolId: getSessionId(),
                title: selectedTitle || "FastGPT 对话",
                html: chatMessages.innerHTML
            });
        }

        const exportedAt = new Date().toLocaleString("zh-CN", { hour12: false });
        const markdown = [
            "# FastGPT 全部聊天记录",
            "",
            "- 导出时间：" + exportedAt,
            "- 会话数量：" + records.length,
            "",
            records.map(function (record) {
                return historyHtmlToMarkdown(
                    record.html,
                    record.title,
                    record.toolId
                );
            }).join("\n\n---\n\n")
        ].join("\n");

        downloadMarkdown(
            "FastGPT_全部聊天记录_" + timestampForFilename() + ".md",
            markdown
        );
    }

    async function clearCurrentChat() {
        const toolId = selectedId;
        const toolTitle = selectedTitle || toolId;
        if (!toolId || !window.confirm(`确定清空“${toolTitle}”的全部对话吗？`)) {
            return;
        }

        clearCurrentButton.disabled = true;
        try {
            const response = await fetch(
                `/api/ai/history/${encodeURIComponent(toolId)}`,
                { method: "DELETE" }
            );
            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.message || "清空失败");
            }

            window.clearTimeout(historySaveTimers.get(toolId));
            historySaveTimers.delete(toolId);
            sessionStorage.removeItem(getSessionKey(toolId));
            if (selectedId === toolId) {
                renderWelcomeMessage();
                scrollChatBottom();
            }
        } catch (error) {
            window.alert(error.message || "清空对话失败");
        } finally {
            clearCurrentButton.disabled = false;
        }
    }

    function getWelcomeMessage() {
        if (selectedTitle) {
            return "这里是“" + selectedTitle + "”的独立对话。你在其他工具里的聊天不会混到这里。";
        }

        return "请从左侧选择 AI 工具，也可以直接描述你的任务。";
    }

    function createMessageElement(role, text) {
        const message = document.createElement("div");
        message.className = role === "user" ? "chat-message user" : "chat-message bot";

        const avatar = document.createElement("span");
        avatar.className = "avatar";
        avatar.textContent = role === "user" ? "我" : "助手";

        const bubble = document.createElement("div");
        bubble.className = "bubble";
        bubble.textContent = text;

        if (role === "user") {
            message.appendChild(bubble);
            message.appendChild(avatar);
        } else {
            message.appendChild(avatar);
            message.appendChild(bubble);
        }

        return message;
    }

    function renderWelcomeMessage() {
        chatMessages.innerHTML = "";
        chatMessages.appendChild(createMessageElement("bot", getWelcomeMessage()));
    }

    function serializeChatHistory() {
        const history = [];
        chatMessages.querySelectorAll(".chat-message").forEach(function (message) {
            const bubble = message.querySelector(".bubble");
            const card = message.querySelector(".chat-tool-card");
            if (bubble) {
                history.push({
                    type: "message",
                    role: message.classList.contains("user") ? "user" : "bot",
                    text: bubble.textContent || ""
                });
            } else if (card) {
                const link = card.querySelector("a[href]");
                history.push({
                    type: "tool",
                    title: (card.querySelector(".chat-tool-card-title") || {}).textContent || "",
                    desc: (card.querySelector(".chat-tool-card-desc") || {}).textContent || "",
                    url: link ? link.href : "",
                    external: Boolean(link && link.target === "_blank")
                });
            }
        });
        return history;
    }

    function renderStructuredHistory(history) {
        chatMessages.innerHTML = "";
        history.forEach(function (item) {
            if (item.type === "message") {
                chatMessages.appendChild(createMessageElement(item.role, item.text || ""));
            } else if (item.type === "tool") {
                addRecommendedTool(item, false);
            }
        });
        scrollChatBottom();
    }

    function persistHistory(toolId, history) {
        window.clearTimeout(historySaveTimers.get(toolId));
        historySaveTimers.set(toolId, window.setTimeout(async function () {
            try {
                await fetch(`/api/ai/history/${encodeURIComponent(toolId)}`, {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ history: history })
                });
            } catch (error) {
                console.error("聊天记录保存失败", error);
            } finally {
                historySaveTimers.delete(toolId);
            }
        }, 300));
    }

    function persistCurrentHistoryOnExit() {
        if (!selectedId || !chatMessages) {
            return;
        }
        fetch(`/api/ai/history/${encodeURIComponent(selectedId)}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ history: serializeChatHistory() }),
            keepalive: true
        }).catch(function () {
            return;
        });
    }

    function saveCurrentSession() {
        if (!chatMessages || !selectedId) {
            return;
        }

        const toolId = getSessionId();
        sessionStorage.setItem(getSessionKey(toolId), chatMessages.innerHTML);
        persistHistory(toolId, serializeChatHistory());
    }

    async function loadToolSession(toolId) {
        const localHistory = sessionStorage.getItem(getSessionKey(toolId));
        if (localHistory) {
            chatMessages.innerHTML = localHistory;
            scrollChatBottom();
        }

        try {
            const response = await fetch(`/api/ai/history/${encodeURIComponent(toolId)}`);
            const data = await response.json();
            if (selectedId !== toolId) {
                return;
            }
            if (response.ok && data.success && Array.isArray(data.history) && data.history.length) {
                renderStructuredHistory(data.history);
                sessionStorage.setItem(getSessionKey(toolId), chatMessages.innerHTML);
                return;
            }
        } catch (error) {
            console.error("聊天记录读取失败", error);
        }

        if (!localHistory && selectedId === toolId) {
            renderWelcomeMessage();
        }
        saveCurrentSession();
        scrollChatBottom();
    }

    function selectTool(item) {
        if (requestRunning) {
            return;
        }

        saveCurrentSession();

        toolItems.forEach(function (toolItem) {
            toolItem.classList.remove("active");
        });

        item.classList.add("active");
        selectedUrl = item.dataset.url || "";
        selectedId = item.dataset.id || "";
        selectedTitle = item.dataset.title || "";

        if (chatTitle) {
            chatTitle.textContent = selectedTitle || "FastGPT 对话";
        }

        if (openButton) {
            openButton.disabled = !selectedUrl;
            openButton.textContent = selectedUrl ? "开始使用" : "未配置链接";
            openButton.title = selectedUrl ? "打开 FastGPT 对话页面" : "请在后台为该工具配置 URL";
        }

        loadToolSession(getSessionId());
    }

    function scrollChatBottom() {
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    function addChatMessage(role, text) {
        const message = createMessageElement(role, text);
        chatMessages.appendChild(message);
        scrollChatBottom();
        saveCurrentSession();
        return message.querySelector(".bubble");
    }

    function updateBubbleText(bubble, text) {
        if (bubble) {
            bubble.textContent = text;
            saveCurrentSession();
        }
    }

    function addRecommendedTool(tool, shouldSave = true) {
        const card = document.createElement("div");
        card.className = "chat-tool-card";

        const title = document.createElement("div");
        title.className = "chat-tool-card-title";
        title.textContent = tool.title || "推荐工具";

        const desc = document.createElement("div");
        desc.className = "chat-tool-card-desc";
        desc.textContent = tool.reason || tool.desc || "";

        card.appendChild(title);
        card.appendChild(desc);

        if (tool.url) {
            const link = document.createElement("a");
            link.href = tool.url;
            link.textContent = tool.link_text || "打开工具";
            if (tool.external) {
                link.target = "_blank";
                link.rel = "noopener";
            }
            card.appendChild(link);
        }

        const message = document.createElement("div");
        message.className = "chat-message bot";

        const avatar = document.createElement("span");
        avatar.className = "avatar";
        avatar.textContent = "助手";

        message.appendChild(avatar);
        message.appendChild(card);
        chatMessages.appendChild(message);
        scrollChatBottom();
        if (shouldSave) {
            saveCurrentSession();
        }
    }

    function buildMessage(message) {
        if (!selectedTitle) {
            return message;
        }

        return "当前选择工具：" + selectedTitle + "\n用户需求：" + message;
    }

    function setRequestRunning(isRunning) {
        requestRunning = isRunning;
        chatSubmit.disabled = isRunning;
        toolItems.forEach(function (item) {
            item.disabled = isRunning;
        });
    }

    async function submitMainChat(message) {
        const apiUrl = chatWorkspace.dataset.apiUrl || "/api/ai/fastgpt/recommend";
        addChatMessage("user", message);
        const loading = addChatMessage("bot", "正在请求当前工具...");
        setRequestRunning(true);

        const selectedTool = {
            id: selectedId,
            title: selectedTitle,
            url: selectedUrl
        };
        const body = {
            message: buildMessage(message),
            page: "fastgpt",
            selected_tool: selectedTool
        };


        try {
            const response = await fetch(apiUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(body)
            });
            const data = await response.json();

            if (!data.success) {
                updateBubbleText(loading, data.message || "请求失败，请稍后再试。");
                return;
            }

            updateBubbleText(loading, data.reply || "我暂时没有生成回复。");

            if (Array.isArray(data.tools) && data.tools.length > 0) {
                data.tools.forEach(addRecommendedTool);
            }
        } catch (error) {
            updateBubbleText(loading, "请求失败，请检查后端接口或网络。");
        } finally {
            setRequestRunning(false);
            chatInput.focus();
        }
    }

    toolItems.forEach(function (item) {
        item.addEventListener("click", function () {
            selectTool(item);
        });
    });

    document.querySelectorAll(".favorite-toggle").forEach(function (button) {
        button.addEventListener("click", function () {
            const row = button.closest(".tool-link-row");
            if (row) {
                toggleFavorite(row.dataset.toolId || "", button);
            }
        });
    });

    if (openButton) {
        openButton.addEventListener("click", function () {
            if (selectedUrl) {
                window.open(selectedUrl, "_blank", "noopener");
            }
        });
    }

    if (exportCurrentButton) {
        exportCurrentButton.addEventListener("click", exportCurrentChat);
    }

    if (exportAllButton) {
        exportAllButton.addEventListener("click", exportAllChats);
    }

    if (clearCurrentButton) {
        clearCurrentButton.addEventListener("click", clearCurrentChat);
    }

    async function initializeToolList() {
        await loadFavoriteIds();
        renderFavoriteTools();

        const activeTool =
            document.querySelector(".favorite-tools .tool-link-item") ||
            document.querySelector(".tool-link-item.active") ||
            toolItems[0];

        if (activeTool) {
            selectTool(activeTool);
        }
    }

    initializeToolList();

    if (chatForm) {
        chatForm.addEventListener("submit", function (event) {
            event.preventDefault();

            let message = chatInput.value.trim();

            if (!message || chatSubmit.disabled) {
                return;
            }


            chatInput.value = "";
            submitMainChat(message);
        });
    }

    window.addEventListener("pagehide", persistCurrentHistoryOnExit);

    if (featureExplanationButton) {
        featureExplanationButton.addEventListener("click", openFeatureExplanation);
    }
    if (featureExplanationClose) {
        featureExplanationClose.addEventListener("click", closeFeatureExplanation);
    }

});
