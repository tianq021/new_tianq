document.addEventListener("DOMContentLoaded", function () {
    const majorItems = document.querySelectorAll(".major-menu-item");
    const minorGroups = document.querySelectorAll(".minor-group");
    const toolItems = document.querySelectorAll(".tool-link-item");
    const chatWorkspace = document.querySelector(".chat-workspace");
    const chatTitle = document.getElementById("chatTitle");
    const chatDesc = document.getElementById("chatDesc");
    const chatMessages = document.getElementById("mainChatMessages");
    const chatForm = document.getElementById("fastgptMainChatForm");
    const chatInput = document.getElementById("fastgptMainChatInput");
    const chatSubmit = document.getElementById("fastgptMainChatSubmit");
    const openButton = document.getElementById("openSelectedTool");
    let selectedUrl = "";
    let selectedId = "";
    let selectedTitle = "";
    let requestRunning = false;

    function getSessionId() {
        return selectedId || "fastgpt-default";
    }

    function getSessionKey(toolId) {
        return "fastgpt_main_chat_history_" + (toolId || "fastgpt-default");
    }

    function getWelcomeMessage() {
        if (selectedTitle) {
            return "这里是“" + selectedTitle + "”的独立对话。你在其他工具里的聊天不会混到这里。";
        }

        return "请选择左侧的大类和小类，也可以直接描述你的任务。我会调用 FastGPT 接口，把结果展示在这里。";
    }

    function createMessageElement(role, text) {
        const message = document.createElement("div");
        message.className = role === "user" ? "chat-message user" : "chat-message bot";

        const avatar = document.createElement("span");
        avatar.className = "avatar";
        avatar.textContent = role === "user" ? "我" : "AI";

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

    function saveCurrentSession() {
        if (!chatMessages || !selectedId) {
            return;
        }

        sessionStorage.setItem(getSessionKey(getSessionId()), chatMessages.innerHTML);
    }

    function loadToolSession(toolId) {
        const history = sessionStorage.getItem(getSessionKey(toolId));

        if (history) {
            chatMessages.innerHTML = history;
        } else {
            renderWelcomeMessage();
            saveCurrentSession();
        }

        scrollChatBottom();
    }

    function showGroup(group) {
        minorGroups.forEach(function (minorGroup) {
            minorGroup.classList.toggle("active", minorGroup.dataset.group === group);
        });
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

        if (chatDesc) {
            chatDesc.textContent = item.dataset.desc || "右侧主页面是当前工具的独立对话区。";
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

    function addRecommendedTool(tool) {
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
        avatar.textContent = "AI";

        message.appendChild(avatar);
        message.appendChild(card);
        chatMessages.appendChild(message);
        scrollChatBottom();
        saveCurrentSession();
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
        majorItems.forEach(function (item) {
            item.disabled = isRunning;
        });
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

    majorItems.forEach(function (item) {
        item.addEventListener("click", function () {
            if (requestRunning) {
                return;
            }

            majorItems.forEach(function (majorItem) {
                majorItem.classList.remove("active");
            });

            item.classList.add("active");
            showGroup(item.dataset.group);

            const firstTool = document.querySelector(
                '.minor-group.active .tool-link-item'
            );

            if (firstTool) {
                selectTool(firstTool);
            }
        });
    });

    toolItems.forEach(function (item) {
        item.addEventListener("click", function () {
            selectTool(item);
        });
    });

    if (openButton) {
        openButton.addEventListener("click", function () {
            if (selectedUrl) {
                window.open(selectedUrl, "_blank", "noopener");
            }
        });
    }

    const activeTool = document.querySelector(".tool-link-item.active") || toolItems[0];

    if (activeTool) {
        selectTool(activeTool);
    }

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

});
