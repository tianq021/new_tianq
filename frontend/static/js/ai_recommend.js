(function () {
    const root = document.getElementById("aiRecommendRoot");
    if (!root) return;

    const page = root.dataset.page || "tools";
    const apiUrl = root.dataset.apiUrl || "/api/ai/tools/recommend";
    const sessionUrl = root.dataset.sessionUrl || "";
    const conversationsUrl = root.dataset.conversationsUrl || "";
    const mode = root.dataset.mode || "recommend";
    const embedded = root.dataset.embedded === "true";
    const conversationEnabled = embedded && page === "user" && !!conversationsUrl;
    const storageScope = [page, root.dataset.userId || "guest"].join("_");
    const storageKey = "ai_recommend_history_" + storageScope;
    const openKey = "ai_recommend_open_" + storageScope;
    const maxVisibleMessages = embedded ? 40 : 30;

    const btn = document.getElementById("aiRecommendBtn");
    const panel = document.getElementById("aiRecommendPanel");
    const closeBtn = document.getElementById("aiRecommendClose");
    const form = document.getElementById("aiRecommendForm");
    const input = document.getElementById("aiRecommendInput");
    const messages = document.getElementById("aiRecommendMessages");
    const header = panel ? panel.querySelector(".ai-recommend-header") : null;
    let aiAvailable = true;
    let historyExpanded = false;
    let activeConversationId = null;
    let conversationSelect = null;
    let newSessionButton = null;
    let clearButton = null;
    let deleteSessionButton = null;

    function disableAiEntry(message) {
        aiAvailable = false;
        root.hidden = true;
        root.setAttribute("aria-hidden", "true");
        if (message) {
            root.dataset.disabledReason = message;
        }
    }

    async function checkAiAvailability() {
        if (!apiUrl.includes("/api/ai/tools/")) {
            return;
        }

        try {
            const response = await fetch("/api/ai/capabilities");
            const result = await response.json();
            const toolsChat = result.data && result.data.tools_chat;
            if (!response.ok || !result.success || !toolsChat || !toolsChat.enabled || !toolsChat.has_key) {
                disableAiEntry("工具页 AI 对话未配置或已停用");
            }
        } catch (error) {
            disableAiEntry("工具页 AI 对话暂不可用");
        }
    }

    function getConversationItems() {
        return Array.from(messages.querySelectorAll(".ai-msg, .ai-tool-card"));
    }

    function updateHiddenNotice(hiddenCount) {
        let notice = messages.querySelector(".ai-history-notice");

        if (!hiddenCount || historyExpanded) {
            if (notice) {
                notice.remove();
            }
            return;
        }

        if (!notice) {
            notice = document.createElement("button");
            notice.type = "button";
            notice.className = "ai-history-notice";
            messages.insertBefore(notice, messages.firstChild);
        }

        notice.textContent = `已隐藏更早的 ${hiddenCount} 条消息，点击展开`;
    }

    function applyMessageLimit() {
        const items = getConversationItems();

        if (historyExpanded || items.length <= maxVisibleMessages) {
            items.forEach(function (item) {
                item.classList.remove("ai-msg-hidden");
            });
            updateHiddenNotice(0);
            return;
        }

        const hiddenCount = items.length - maxVisibleMessages;
        items.forEach(function (item, index) {
            item.classList.toggle("ai-msg-hidden", index < hiddenCount);
        });
        updateHiddenNotice(hiddenCount);
    }

    function saveHistory() {
        applyMessageLimit();
        if (!conversationEnabled) {
            sessionStorage.setItem(storageKey, messages.innerHTML);
        }
    }

    function scrollBottom() {
        messages.scrollTop = messages.scrollHeight;
    }

    function createDeleteButton() {
        const button = document.createElement("button");
        button.className = "ai-msg-delete";
        button.type = "button";
        button.title = conversationEnabled ? "从当前会话记录删除这条消息" : "从当前页面删除这条消息";
        button.setAttribute("aria-label", button.title);
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
        messages.querySelectorAll(".ai-msg, .ai-tool-card").forEach(makeDeletable);
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
        messageNode.dataset.text = text;
    }

    function addTextMessage(role, text, options) {
        const opts = options || {};
        const normalizedRole = role === "assistant" ? "bot" : role;
        const div = document.createElement("div");
        div.className = normalizedRole === "user" ? "ai-msg ai-msg-user" : "ai-msg ai-msg-bot";
        div.dataset.role = normalizedRole === "user" ? "user" : "assistant";
        div.dataset.text = text;

        const content = document.createElement("span");
        content.className = "ai-msg-content";
        content.textContent = text;
        div.appendChild(content);

        makeDeletable(div);

        messages.appendChild(div);
        if (!opts.skipSave) {
            saveHistory();
        } else {
            applyMessageLimit();
        }
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

    function getMessagePayload() {
        return Array.from(messages.querySelectorAll(".ai-msg")).map(function (item) {
            const content = item.querySelector(".ai-msg-content");
            return {
                role: item.dataset.role || (item.classList.contains("ai-msg-user") ? "user" : "assistant"),
                text: content ? content.textContent : item.textContent
            };
        }).filter(function (item) {
            return item.text && item.text.trim();
        });
    }

    async function saveConversationMessages(messageList) {
        if (!conversationEnabled || !activeConversationId) {
            return;
        }

        try {
            await fetch(`${conversationsUrl}/${activeConversationId}`, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    messages: messageList
                })
            });
        } catch (error) {
            addTextMessage("bot", "当前会话保存失败，请稍后再试。");
        }
    }

    async function persistCurrentMessages() {
        await saveConversationMessages(getMessagePayload());
    }

    function renderConversationMessages(conversation) {
        historyExpanded = false;
        messages.innerHTML = "";
        activeConversationId = conversation && conversation.id ? conversation.id : null;

        const list = conversation && Array.isArray(conversation.messages) ? conversation.messages : [];
        if (!list.length) {
            addTextMessage("bot", "有什么想问的，可以直接在这里发送。", { skipSave: true });
        } else {
            list.forEach(function (item) {
                addTextMessage(item.role === "user" ? "user" : "assistant", item.text || "", { skipSave: true });
            });
        }
        saveHistory();
        scrollBottom();
    }

    function renderConversationSelect(conversations, current) {
        if (!conversationSelect) {
            return;
        }

        conversationSelect.innerHTML = "";
        conversations.forEach(function (item) {
            const option = document.createElement("option");
            option.value = String(item.id);
            option.textContent = item.title || "新对话";
            conversationSelect.appendChild(option);
        });

        if (current && current.id) {
            conversationSelect.value = String(current.id);
            activeConversationId = current.id;
        }

        const hasConversation = conversations.length > 0;
        conversationSelect.disabled = !hasConversation;
        if (clearButton) clearButton.disabled = !hasConversation;
        if (deleteSessionButton) deleteSessionButton.disabled = conversations.length <= 1;
    }

    async function loadConversations() {
        if (!conversationEnabled) {
            return;
        }

        try {
            const response = await fetch(conversationsUrl);
            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.message || "会话读取失败");
            }

            renderConversationSelect(data.conversations || [], data.current);
            renderConversationMessages(data.current);
        } catch (error) {
            addTextMessage("bot", error.message || "会话读取失败，请稍后再试。");
        }
    }

    async function createConversation() {
        if (!conversationEnabled || !newSessionButton) {
            return;
        }

        newSessionButton.disabled = true;
        try {
            const response = await fetch(conversationsUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    title: "新对话"
                })
            });
            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.message || "新会话创建失败");
            }
            renderConversationSelect(data.conversations || [], data.current);
            renderConversationMessages(data.current);
        } catch (error) {
            addTextMessage("bot", error.message || "新会话创建失败，请稍后再试。");
        } finally {
            newSessionButton.disabled = false;
        }
    }

    async function selectConversation(conversationId) {
        if (!conversationEnabled || !conversationId) {
            return;
        }

        try {
            const response = await fetch(`${conversationsUrl}/${conversationId}/select`, {
                method: "POST"
            });
            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.message || "会话切换失败");
            }
            renderConversationSelect(data.conversations || [], data.current);
            renderConversationMessages(data.current);
        } catch (error) {
            addTextMessage("bot", error.message || "会话切换失败，请稍后再试。");
        }
    }

    async function deleteConversation() {
        if (!conversationEnabled || !activeConversationId || !deleteSessionButton) {
            return;
        }

        if (!window.confirm("确定删除当前会话吗？本地保存的消息会被删除，FastGPT 远程历史不会被硬删除。")) {
            return;
        }

        deleteSessionButton.disabled = true;
        try {
            const response = await fetch(`${conversationsUrl}/${activeConversationId}`, {
                method: "DELETE"
            });
            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.message || "会话删除失败");
            }
            renderConversationSelect(data.conversations || [], data.current);
            renderConversationMessages(data.current);
        } catch (error) {
            addTextMessage("bot", error.message || "会话删除失败，请稍后再试。");
        } finally {
            deleteSessionButton.disabled = false;
        }
    }

    function restoreHistory() {
        if (conversationEnabled) {
            return;
        }

        const html = sessionStorage.getItem(storageKey);

        if (html) {
            messages.innerHTML = html;
            enhanceDeletableItems();
            applyMessageLimit();
            scrollBottom();
            return;
        }

        enhanceDeletableItems();
        applyMessageLimit();
    }

    function openPanel() {
        if (!aiAvailable) {
            return;
        }
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

    function addHeaderActions() {
        if (!embedded || !header || header.querySelector(".ai-header-actions")) {
            return;
        }

        const actions = document.createElement("div");
        actions.className = "ai-header-actions";

        if (conversationEnabled) {
            conversationSelect = document.createElement("select");
            conversationSelect.className = "ai-conversation-select";
            conversationSelect.title = "选择历史会话";
            actions.appendChild(conversationSelect);

            conversationSelect.addEventListener("change", function () {
                selectConversation(conversationSelect.value);
            });
        }

        clearButton = document.createElement("button");
        clearButton.type = "button";
        clearButton.className = "ai-header-action";
        clearButton.textContent = conversationEnabled ? "清空当前" : "清空本页";
        clearButton.title = conversationEnabled ? "清空当前会话在本地保存的消息，不会删除 FastGPT 远程上下文" : "只清空当前页面显示，不会删除 FastGPT 远程上下文";

        newSessionButton = document.createElement("button");
        newSessionButton.type = "button";
        newSessionButton.className = "ai-header-action";
        newSessionButton.textContent = "新会话";
        newSessionButton.title = "开启新的 FastGPT 远程会话，旧远程上下文不会被删除";
        newSessionButton.disabled = conversationEnabled ? false : !sessionUrl;

        actions.appendChild(clearButton);
        actions.appendChild(newSessionButton);

        if (conversationEnabled) {
            deleteSessionButton = document.createElement("button");
            deleteSessionButton.type = "button";
            deleteSessionButton.className = "ai-header-action ai-header-danger";
            deleteSessionButton.textContent = "删除";
            deleteSessionButton.title = "删除当前会话的本地记录";
            actions.appendChild(deleteSessionButton);
        }

        header.appendChild(actions);

        clearButton.addEventListener("click", async function () {
            historyExpanded = false;
            messages.innerHTML = "";
            if (conversationEnabled) {
                await saveConversationMessages([]);
                addTextMessage("bot", "有什么想问的，可以直接在这里发送。", { skipSave: true });
            } else {
                sessionStorage.removeItem(storageKey);
                addTextMessage("bot", "已清空当前页面显示。FastGPT 远程上下文不会被删除。");
            }
        });

        newSessionButton.addEventListener("click", async function () {
            if (conversationEnabled) {
                await createConversation();
                return;
            }

            if (!sessionUrl || newSessionButton.disabled) {
                return;
            }

            newSessionButton.disabled = true;
            try {
                const response = await fetch(sessionUrl, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        page: page
                    })
                });
                const data = await response.json();
                if (!response.ok || !data.success) {
                    throw new Error(data.message || "新会话创建失败");
                }

                historyExpanded = false;
                messages.innerHTML = "";
                sessionStorage.removeItem(storageKey);
                addTextMessage("bot", "已开启新会话。之后的问题会使用新的远程上下文，旧会话仍保留在 FastGPT。");
            } catch (error) {
                addTextMessage("bot", error.message || "新会话创建失败，请稍后再试。");
            } finally {
                newSessionButton.disabled = false;
            }
        });

        if (deleteSessionButton) {
            deleteSessionButton.addEventListener("click", deleteConversation);
        }
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

    messages.addEventListener("click", async function (event) {
        const deleteBtn = event.target.closest(".ai-msg-delete");

        if (!deleteBtn) {
            return;
        }

        const item = deleteBtn.closest(".ai-msg, .ai-tool-card");

        if (!item) {
            return;
        }

        item.remove();
        saveHistory();
        await persistCurrentMessages();
    });

    messages.addEventListener("click", function (event) {
        const notice = event.target.closest(".ai-history-notice");
        if (!notice) {
            return;
        }

        historyExpanded = true;
        applyMessageLimit();
        saveHistory();
    });

    form.addEventListener("submit", async function (event) {
        event.preventDefault();
        if (!aiAvailable) {
            return;
        }

        const message = input.value.trim();
        if (!message) return;

        addTextMessage("user", message);
        input.value = "";

        const loadingText = mode === "chat" ? "正在回复..." : "正在分析适合你的工具...";
        const loading = addTextMessage("bot", loadingText);

        const submitBtn = form.querySelector("button");
        submitBtn.disabled = true;

        try {
            const requestBody = {
                message: message,
                page: page
            };
            if (conversationEnabled && activeConversationId) {
                requestBody.conversation_id = activeConversationId;
            }

            const res = await fetch(apiUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(requestBody)
            });

            const data = await res.json();

            if (!data.success) {
                if (data.code === "ai_profile_unavailable") {
                    disableAiEntry(data.message || "AI 对话未配置或已停用");
                }
                setMessageText(loading, data.message || "请求失败，请稍后再试。");
                saveHistory();
                return;
            }

            setMessageText(loading, data.reply || "我暂时没有生成回复。");

            if (data.conversation) {
                activeConversationId = data.conversation.id;
                renderConversationMessages(data.conversation);
                loadConversations();
            }

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

    addHeaderActions();
    checkAiAvailability();
    if (conversationEnabled) {
        loadConversations();
    } else {
        restoreHistory();
    }

    if (embedded) {
        openPanel();
    } else if (sessionStorage.getItem(openKey) === "1") {
        openPanel();
    }
})();
