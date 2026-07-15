const saveStatus = document.querySelector("#save-status");
const searchInput = document.querySelector("#endpoint-search");
const endpointItems = Array.from(document.querySelectorAll(".endpoint-item"));
const toolSource = document.querySelector("#tool-source");
const toolList = document.querySelector("#tool-list");
const toolFilePath = document.querySelector("#tool-file-path");
const toolSourceNote = document.querySelector("#tool-source-note");
const toolForm = document.querySelector("#tool-form");
const toolStatus = document.querySelector("#tool-status");
const configStatusButton = document.querySelector("#config-status-check");
const configStatus = document.querySelector("#config-status");
const fastgptHealthCheckAllButton = document.querySelector("#fastgpt-health-check-all");
const fastgptHealthSystemPrompt = document.querySelector("#fastgpt-health-system-prompt");
const fastgptHealthUserPrompt = document.querySelector("#fastgpt-health-user-prompt");
const fastgptHealthSummary = document.querySelector("#fastgpt-health-summary");
const fastgptHealthResultList = document.querySelector("#fastgpt-health-result-list");
const exportButton = document.querySelector("#config-export");
const refreshLogsButton = document.querySelector("#refresh-fastgpt-logs");
const logLimit = document.querySelector("#fastgpt-log-limit");
const logStatus = document.querySelector("#fastgpt-log-status");
const logList = document.querySelector("#fastgpt-log-list");
const featureExplanationForm = document.querySelector("#feature-explanation-form");
const featureExplanationStatus = document.querySelector("#feature-explanation-status");
const refreshUserFeedbackButton = document.querySelector("#refresh-user-feedback");
const userFeedbackStatus = document.querySelector("#user-feedback-status");
const userFeedbackList = document.querySelector("#user-feedback-list");
const refreshAdminUsersButton = document.querySelector("#refresh-admin-users");
const adminUserStatus = document.querySelector("#admin-user-status");
const adminUserList = document.querySelector("#admin-user-list");
const adminCommentPageKey = document.querySelector("#admin-comment-page-key");
const adminCommentSort = document.querySelector("#admin-comment-sort");
const refreshAdminCommentsButton = document.querySelector("#refresh-admin-comments");
const deleteSelectedCommentsButton = document.querySelector("#delete-selected-comments");
const adminCommentStatus = document.querySelector("#admin-comment-status");
const adminCommentList = document.querySelector("#admin-comment-list");

let currentTools = [];

const sourceNotes = {
    local: "本地工具从数据库读取，并被 /tools 页面使用。",
    fastgpt: "FastGPT 工具从数据库读取，并被 FastGPT 页面和推荐流程使用。",
    custom: "自定义工具保存到数据库，当前不会被 /tools 默认加载。"
};

function setTextStatus(element, message, isError = false) {
    if (!element) {
        return;
    }
    element.textContent = message;
    element.style.color = isError ? "#b42318" : "#376345";
}

function setStatus(message, isError = false) {
    setTextStatus(saveStatus, message, isError);
}

document.querySelectorAll("[data-tab-target]").forEach((button) => {
    button.addEventListener("click", () => {
        document.querySelectorAll("[data-tab-target]").forEach((item) => {
            item.classList.toggle("active", item === button);
        });
        document.querySelectorAll(".tab-panel").forEach((panel) => {
            panel.classList.toggle("active", panel.id === button.dataset.tabTarget);
        });
        if (button.dataset.tabTarget === "logs-panel" && !logList.dataset.loaded) {
            loadFastgptLogs();
        }
        if (button.dataset.tabTarget === "explanation-panel") {
            loadFeatureExplanation();
        }
        if (button.dataset.tabTarget === "feedback-panel") {
            loadUserFeedback();
        }
        if (button.dataset.tabTarget === "users-panel") {
            loadAdminUsers();
        }
        if (button.dataset.tabTarget === "comments-panel") {
            loadAdminComments();
        }
    });
});

if (searchInput) {
    searchInput.addEventListener("input", () => {
        const keyword = searchInput.value.trim().toLowerCase();
        endpointItems.forEach((item) => {
            const text = item.dataset.search.toLowerCase();
            item.hidden = keyword && !text.includes(keyword);
        });
    });
}

document.querySelectorAll("[data-endpoint]").forEach((button) => {
    button.addEventListener("click", async () => {
        const item = button.closest(".endpoint-item");
        const title = item.querySelector("[data-field='title']").value;
        const description = item.querySelector("[data-field='description']").value;

        button.disabled = true;
        setStatus("正在保存...");

        try {
            const response = await fetch(`/api/admin/endpoints/${encodeURIComponent(button.dataset.endpoint)}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ title, description })
            });
            const result = await response.json();
            if (!response.ok || !result.success) {
                throw new Error(result.message || "保存失败");
            }

            item.dataset.search = `${item.querySelector("code").textContent} ${item.querySelector(".method").textContent} ${title} ${description}`;
            setStatus("保存成功");
        } catch (error) {
            setStatus(error.message, true);
        } finally {
            button.disabled = false;
        }
    });
});

function renderToolList() {
    toolList.innerHTML = "";

    if (!currentTools.length) {
        const empty = document.createElement("p");
        empty.className = "empty-state";
        empty.textContent = "暂无工具数据";
        toolList.appendChild(empty);
        return;
    }

    currentTools.forEach((tool, index) => {
        const row = document.createElement("article");
        row.className = "tool-row";

        const summary = document.createElement("button");
        summary.type = "button";
        summary.className = "tool-row-main";
        const categoryText = toolSource.value === "fastgpt"
            ? ""
            : `${escapeHtml(tool.category || "未分类")} · `;
        summary.innerHTML = `
            <strong>${escapeHtml(tool.title || tool.id)}</strong>
            <span>${escapeHtml(tool.id || "")}</span>
            <small>${categoryText}排序 ${Number(tool.sort_order || 100)} · ${tool.enabled === false ? "停用" : "启用"}${tool.has_api_key === false ? " · 未配置密钥" : ""}</small>
        `;
        summary.addEventListener("click", () => fillToolForm(tool));

        const actions = document.createElement("div");
        actions.className = "tool-row-actions";
        if (toolSource.value === "fastgpt") {
            actions.appendChild(createSmallButton("测试", () => testFastgptTool(tool.id)));
        }
        actions.appendChild(createSmallButton(tool.enabled === false ? "启用" : "停用", () => {
            updateToolState(tool.id, { enabled: tool.enabled === false });
        }));
        actions.appendChild(createSmallButton("移除", () => softDeleteTool(tool.id), tool.enabled === false));
        actions.appendChild(createSmallButton("上移", () => moveTool(index, -1), index === 0));
        actions.appendChild(createSmallButton("下移", () => moveTool(index, 1), index === currentTools.length - 1));

        row.appendChild(summary);
        row.appendChild(actions);
        toolList.appendChild(row);
    });
}

function createSmallButton(text, onClick, disabled = false) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "small-button";
    button.textContent = text;
    button.disabled = disabled;
    button.addEventListener("click", onClick);
    return button;
}

function updateToolFormVisibility() {
    const isFastgpt = toolSource.value === "fastgpt";
    const categoryGroup = toolForm.querySelector('[data-field-group="category"]');

    if (categoryGroup) {
        categoryGroup.hidden = isFastgpt;
    }
    if (isFastgpt) {
        toolForm.elements.category.value = "";
    }
}

async function loadTools() {
    setTextStatus(toolStatus, "正在读取...");
    toolSourceNote.textContent = sourceNotes[toolSource.value] || "";
    updateToolFormVisibility();

    try {
        const response = await fetch(`/api/admin/tools?source=${encodeURIComponent(toolSource.value)}`);
        const result = await response.json();
        if (!response.ok || !result.success) {
            throw new Error(result.message || "读取失败");
        }

        currentTools = result.data.tools || [];
        toolFilePath.textContent = result.data.storage === "database" ? "存储位置：数据库 ai_tools" : "";
        renderToolList();
        setTextStatus(toolStatus, `已读取 ${currentTools.length} 条工具`);
    } catch (error) {
        currentTools = [];
        renderToolList();
        setTextStatus(toolStatus, error.message, true);
    }
}

function toolExtraJson(tool) {
    const baseFields = new Set([
        "id",
        "title",
        "desc",
        "intro",
        "category",
        "type",
        "url",
        "enabled",
        "default",
        "sort_order",
        "chat_id",
        "profile_key",
        "has_api_key"
    ]);
    const extra = {};

    Object.entries(tool).forEach(([key, value]) => {
        if (!baseFields.has(key)) {
            extra[key] = value;
        }
    });

    return Object.keys(extra).length ? JSON.stringify(extra, null, 2) : "";
}

function fillToolForm(tool) {
    toolForm.elements.id.value = tool.id || "";
    toolForm.elements.title.value = tool.title || "";
    toolForm.elements.category.value = toolSource.value === "fastgpt" ? "" : (tool.category || "");
    toolForm.elements.type.value = tool.type || "link";
    toolForm.elements.sort_order.value = tool.sort_order || 100;
    toolForm.elements.url.value = tool.url || "";
    toolForm.elements.chat_id.value = tool.chat_id || tool.id || "";
    toolForm.elements.api_key.value = "";
    toolForm.elements.desc.value = tool.desc || "";
    toolForm.elements.intro.value = tool.intro || "";
    toolForm.elements.extra_json.value = toolExtraJson(tool);
    toolForm.elements.enabled.checked = tool.enabled !== false;
    toolForm.elements.default.checked = Boolean(tool.default);
    setTextStatus(toolStatus, `正在编辑 ${tool.id || tool.title}`);
}

function resetToolForm() {
    toolForm.reset();
    toolForm.elements.enabled.checked = true;
    toolForm.elements.type.value = "link";
    toolForm.elements.sort_order.value = "100";
    toolForm.elements.chat_id.value = "";
    toolForm.elements.api_key.value = "";
    toolForm.elements.intro.value = "";
    setTextStatus(toolStatus, "");
}

document.querySelector("#tool-reset").addEventListener("click", resetToolForm);
toolSource.addEventListener("change", () => {
    resetToolForm();
    updateToolFormVisibility();
    loadTools();
});

toolForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const payload = {
        source: toolSource.value,
        id: toolForm.elements.id.value.trim(),
        title: toolForm.elements.title.value.trim(),
        category: toolSource.value === "fastgpt" ? "" : toolForm.elements.category.value.trim(),
        type: toolForm.elements.type.value.trim() || "link",
        sort_order: Number(toolForm.elements.sort_order.value || 100),
        url: toolForm.elements.url.value.trim(),
        chat_id: toolForm.elements.chat_id.value.trim(),
        api_key: toolForm.elements.api_key.value.trim(),
        desc: toolForm.elements.desc.value.trim(),
        intro: toolForm.elements.intro.value.trim(),
        extra_json: toolForm.elements.extra_json.value.trim(),
        enabled: toolForm.elements.enabled.checked,
        default: toolForm.elements.default.checked
    };

    setTextStatus(toolStatus, "正在保存工具...");

    try {
        const response = await fetch("/api/admin/tools", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const result = await response.json();
        if (!response.ok || !result.success) {
            throw new Error(result.message || "保存失败");
        }

        await loadTools();
        setTextStatus(toolStatus, result.data.created ? "工具已添加" : "工具已更新");
    } catch (error) {
        setTextStatus(toolStatus, error.message, true);
    }
});

async function updateToolState(toolId, changes) {
    setTextStatus(toolStatus, "正在更新工具...");
    try {
        const response = await fetch(`/api/admin/tools/${encodeURIComponent(toolSource.value)}/${encodeURIComponent(toolId)}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(changes)
        });
        const result = await response.json();
        if (!response.ok || !result.success) {
            throw new Error(result.message || "更新失败");
        }
        await loadTools();
        setTextStatus(toolStatus, "工具已更新");
    } catch (error) {
        setTextStatus(toolStatus, error.message, true);
    }
}

async function softDeleteTool(toolId) {
    if (!window.confirm("确认移除这个工具？它会被停用，不会从数据库硬删除。")) {
        return;
    }

    setTextStatus(toolStatus, "正在移除工具...");
    try {
        const response = await fetch(`/api/admin/tools/${encodeURIComponent(toolSource.value)}/${encodeURIComponent(toolId)}`, {
            method: "DELETE"
        });
        const result = await response.json();
        if (!response.ok || !result.success) {
            throw new Error(result.message || "移除失败");
        }
        await loadTools();
        setTextStatus(toolStatus, "工具已停用保留");
    } catch (error) {
        setTextStatus(toolStatus, error.message, true);
    }
}

async function testFastgptTool(toolId) {
    setTextStatus(toolStatus, `正在测试 ${toolId}...`);
    try {
        const response = await fetch(`/api/admin/fastgpt/health/${encodeURIComponent(toolId)}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(getFastgptHealthPayload())
        });
        const result = await response.json();
        if (!response.ok || !result.success) {
            throw new Error(result.message || "测试失败");
        }
        const data = result.data || {};
        setTextStatus(
            toolStatus,
            `${toolId}: ${data.ok ? "可用" : "不可用"} - ${data.message || data.status || ""}`,
            !data.ok
        );
    } catch (error) {
        setTextStatus(toolStatus, error.message, true);
    }
}

async function testAllFastgptTools() {
    setTextStatus(fastgptHealthSummary || toolStatus, "正在测试全部 AI，请等待所有工具返回...");
    if (fastgptHealthResultList) {
        fastgptHealthResultList.innerHTML = '<p class="empty-state">正在测试，请稍候...</p>';
    }
    if (fastgptHealthCheckAllButton) {
        fastgptHealthCheckAllButton.disabled = true;
    }

    try {
        const response = await fetch("/api/admin/fastgpt/health", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(getFastgptHealthPayload())
        });
        const result = await response.json();
        if (!response.ok || !result.success) {
            throw new Error(result.message || "批量检查失败");
        }
        const data = result.data || {};
        renderFastgptHealthResults(data.results || []);
        setTextStatus(
            fastgptHealthSummary || toolStatus,
            `测试完成：${Number(data.ok_count || 0)}/${Number(data.total || 0)} 可用，${Number(data.failed_count || 0)} 个异常`,
            Number(data.failed_count || 0) > 0
        );
    } catch (error) {
        if (fastgptHealthResultList) {
            fastgptHealthResultList.innerHTML = "";
        }
        setTextStatus(fastgptHealthSummary || toolStatus, error.message, true);
    } finally {
        if (fastgptHealthCheckAllButton) {
            fastgptHealthCheckAllButton.disabled = false;
        }
    }
}

function renderFastgptHealthResults(results) {
    if (!fastgptHealthResultList) {
        return;
    }

    fastgptHealthResultList.innerHTML = "";

    if (!results.length) {
        fastgptHealthResultList.innerHTML = '<p class="empty-state">暂无可测试的 FastGPT 工具</p>';
        return;
    }

    results.forEach((item) => {
        const row = document.createElement("article");
        row.className = `ai-health-result ${item.ok ? "success" : "error"}`;

        const elapsedText = item.elapsed_ms === null || item.elapsed_ms === undefined
            ? "-"
            : `${Number(item.elapsed_ms || 0)} ms`;
        const httpText = item.http_status ? `HTTP ${item.http_status}` : "本地检查";

        row.innerHTML = `
            <div class="ai-health-result-head">
                <strong>${escapeHtml(item.title || item.tool_id || "FastGPT 工具")}</strong>
                <span>${escapeHtml(item.status_code || item.status || "")}</span>
                <small>${escapeHtml(item.tool_id || "")} · ${escapeHtml(item.chat_id || "")}</small>
            </div>
            <div class="ai-health-result-meta">
                <code>${escapeHtml(httpText)}</code>
                <code>${escapeHtml(elapsedText)}</code>
                <code>${escapeHtml(item.profile_key || "")}</code>
            </div>
            <p>${escapeHtml(item.message || "")}</p>
        `;
        fastgptHealthResultList.appendChild(row);
    });
}

function getFastgptHealthPayload() {
    return {
        system_prompt: fastgptHealthSystemPrompt ? fastgptHealthSystemPrompt.value.trim() : "",
        user_prompt: fastgptHealthUserPrompt ? fastgptHealthUserPrompt.value.trim() : ""
    };
}

if (fastgptHealthCheckAllButton) {
    fastgptHealthCheckAllButton.addEventListener("click", testAllFastgptTools);
}

async function moveTool(index, direction) {
    const current = currentTools[index];
    const target = currentTools[index + direction];
    if (!current || !target) {
        return;
    }

    const currentOrder = Number(current.sort_order || 100);
    const targetOrder = Number(target.sort_order || 100);
    await Promise.all([
        updateToolState(current.id, { sort_order: targetOrder }),
        updateToolState(target.id, { sort_order: currentOrder })
    ]);
}

async function loadConfigStatus() {
    if (!configStatus) {
        return;
    }
    setTextStatus(configStatus, "正在检查配置...");
    try {
        const response = await fetch("/api/admin/config/status");
        const result = await response.json();
        if (!response.ok || !result.success) {
            throw new Error(result.message || "配置检查失败");
        }
        const data = result.data || {};
        const failed = data.failed || [];
        if (!failed.length) {
            setTextStatus(configStatus, "配置检查通过");
            return;
        }
        setTextStatus(
            configStatus,
            `配置提醒：${failed.map((item) => `${item.key} ${item.message}`).join("；")}`,
            true
        );
    } catch (error) {
        setTextStatus(configStatus, error.message, true);
    }
}

if (configStatusButton) {
    configStatusButton.addEventListener("click", loadConfigStatus);
}

if (exportButton) {
    exportButton.addEventListener("click", async () => {
        setTextStatus(toolStatus, "正在导出配置...");
        try {
            const response = await fetch("/api/admin/export");
            const result = await response.json();
            if (!response.ok || !result.success) {
                throw new Error(result.message || "导出失败");
            }
            downloadJson(result.data, `new_tianq_config_${new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-")}.json`);
            setTextStatus(toolStatus, "配置已导出");
        } catch (error) {
            setTextStatus(toolStatus, error.message, true);
        }
    });
}

function downloadJson(data, filename) {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
}

async function loadFastgptLogs() {
    setTextStatus(logStatus, "正在读取日志...");
    try {
        const response = await fetch(`/api/admin/fastgpt/logs?limit=${encodeURIComponent(logLimit.value)}`);
        const result = await response.json();
        if (!response.ok || !result.success) {
            throw new Error(result.message || "日志读取失败");
        }
        renderFastgptLogs(result.data.logs || []);
        logList.dataset.loaded = "true";
        setTextStatus(logStatus, `已读取 ${result.data.logs.length} 条日志`);
    } catch (error) {
        logList.innerHTML = "";
        setTextStatus(logStatus, error.message, true);
    }
}

function renderFastgptLogs(logs) {
    logList.innerHTML = "";
    if (!logs.length) {
        const empty = document.createElement("p");
        empty.className = "empty-state";
        empty.textContent = "暂无 FastGPT 请求日志";
        logList.appendChild(empty);
        return;
    }

    logs.forEach((item) => {
        const row = document.createElement("article");
        row.className = `log-row ${item.success ? "success" : "error"}`;
        row.innerHTML = `
            <div class="log-row-head">
                <strong>${escapeHtml(item.chat_id || "未知会话")}</strong>
                <span>${item.success ? "成功" : "失败"}</span>
                <small>${escapeHtml(item.created_at || "")} · ${Number(item.elapsed_ms || 0).toFixed(0)} 毫秒 · ${escapeHtml(item.remote_addr || "")}</small>
            </div>
            <p><b>用户：</b>${escapeHtml(item.user_message || "")}</p>
            <p><b>回复：</b>${escapeHtml(item.ai_reply || "")}</p>
            ${item.error ? `<p class="log-error"><b>错误：</b>${escapeHtml(item.error)}</p>` : ""}
        `;
        logList.appendChild(row);
    });
}

if (refreshLogsButton) {
    refreshLogsButton.addEventListener("click", loadFastgptLogs);
}

if (logLimit) {
    logLimit.addEventListener("change", loadFastgptLogs);
}

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll("\"", "&quot;")
        .replaceAll("'", "&#039;");
}

async function loadFeatureExplanation() {
    if (!featureExplanationForm) {
        return;
    }
    const pageKey = featureExplanationForm.elements.page_key.value;
    setTextStatus(featureExplanationStatus, "正在读取...");
    try {
        const response = await fetch(
            `/api/admin/feature-explanations/${encodeURIComponent(pageKey)}`
        );
        const result = await response.json();
        if (!response.ok || !result.success) {
            throw new Error(result.message || "读取失败");
        }
        const data = result.data || {};
        featureExplanationForm.elements.title.value = data.title || "功能解释";
        featureExplanationForm.elements.content.value = data.content || "";
        featureExplanationForm.elements.enabled.checked = data.enabled !== false;
        setTextStatus(featureExplanationStatus, data ? "读取完成" : "尚未配置");
    } catch (error) {
        setTextStatus(featureExplanationStatus, error.message, true);
    }
}

if (featureExplanationForm) {
    featureExplanationForm.elements.page_key.addEventListener("change", loadFeatureExplanation);
    featureExplanationForm.addEventListener("submit", async function (event) {
        event.preventDefault();
        const pageKey = featureExplanationForm.elements.page_key.value;
        setTextStatus(featureExplanationStatus, "正在保存...");
        try {
            const response = await fetch(
                `/api/admin/feature-explanations/${encodeURIComponent(pageKey)}`,
                {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        title: featureExplanationForm.elements.title.value.trim(),
                        content: featureExplanationForm.elements.content.value.trim(),
                        enabled: featureExplanationForm.elements.enabled.checked
                    })
                }
            );
            const result = await response.json();
            if (!response.ok || !result.success) {
                throw new Error(result.message || "保存失败");
            }
            setTextStatus(featureExplanationStatus, "功能解释已保存");
        } catch (error) {
            setTextStatus(featureExplanationStatus, error.message, true);
        }
    });
}

async function loadUserFeedback() {
    if (!userFeedbackList) {
        return;
    }
    setTextStatus(userFeedbackStatus, "正在读取...");
    try {
        const response = await fetch("/api/admin/feedback?limit=500");
        const result = await response.json();
        if (!response.ok || !result.success) {
            throw new Error(result.message || "反馈读取失败");
        }
        userFeedbackList.innerHTML = "";
        const feedback = result.feedback || [];
        if (!feedback.length) {
            userFeedbackList.innerHTML = '<p class="empty-state">暂无用户反馈</p>';
        } else {
            feedback.forEach(function (item) {
                const row = document.createElement("article");
                row.className = "log-row";
                row.innerHTML = `
                    <div class="log-row-head">
                        <strong>${escapeHtml(item.display_name || item.username || "用户")}</strong>
                        <span>#${Number(item.id || 0)}</span>
                        <small>${escapeHtml(item.created_at || "")} · ${escapeHtml(item.username || "")}</small>
                    </div>
                    <p>${escapeHtml(item.content || "")}</p>
                `;
                userFeedbackList.appendChild(row);
            });
        }
        userFeedbackList.dataset.loaded = "1";
        setTextStatus(userFeedbackStatus, `共 ${feedback.length} 条反馈`);
    } catch (error) {
        setTextStatus(userFeedbackStatus, error.message, true);
    }
}

if (refreshUserFeedbackButton) {
    refreshUserFeedbackButton.addEventListener("click", loadUserFeedback);
}

async function loadAdminUsers() {
    if (!adminUserList) {
        return;
    }

    setTextStatus(adminUserStatus, "正在读取...");
    adminUserList.innerHTML = "";

    try {
        const response = await fetch("/api/admin/users");
        const result = await response.json();
        if (!response.ok || !result.success) {
            throw new Error(result.message || "用户读取失败");
        }

        renderAdminUsers(result.users || []);
        adminUserList.dataset.loaded = "1";
        setTextStatus(adminUserStatus, `共 ${Number((result.users || []).length)} 个账号`);
    } catch (error) {
        setTextStatus(adminUserStatus, error.message, true);
    }
}

function renderAdminUsers(users) {
    adminUserList.innerHTML = "";

    if (!users.length) {
        adminUserList.innerHTML = '<p class="empty-state">暂无用户</p>';
        return;
    }

    users.forEach(function (user) {
        const row = document.createElement("article");
        row.className = "log-row admin-user-row";

        const head = document.createElement("div");
        head.className = "log-row-head";
        head.innerHTML = `
            <strong>${escapeHtml(user.display_name || user.username || "用户")}</strong>
            <span>用户 ID ${Number(user.id || 0)}</span>
            <span>${escapeHtml(user.role === "admin" ? "管理员" : "普通用户")}</span>
            <small>${escapeHtml(user.username || "")} · ${user.enabled ? "启用" : "停用"} · 最近登录 ${escapeHtml(user.last_login_at || "无")}</small>
        `;

        const form = document.createElement("form");
        form.className = "admin-password-reset";
        form.innerHTML = `
            <input type="password" name="password" minlength="8" maxlength="128" placeholder="输入新密码，至少 8 位" autocomplete="new-password" required>
            <button class="small-button" type="submit">重置密码</button>
            <span aria-live="polite"></span>
        `;
        form.addEventListener("submit", function (event) {
            event.preventDefault();
            resetAdminUserPassword(user, form);
        });

        row.appendChild(head);
        row.appendChild(form);
        adminUserList.appendChild(row);
    });
}

async function resetAdminUserPassword(user, form) {
    const passwordInput = form.elements.password;
    const status = form.querySelector("span");
    const button = form.querySelector("button");
    const password = passwordInput.value;

    if (password.length < 8) {
        status.textContent = "密码至少需要 8 个字符";
        status.classList.add("error-text");
        return;
    }

    if (!window.confirm(`确认重置 ${user.username} 的密码？`)) {
        return;
    }

    button.disabled = true;
    status.textContent = "正在重置...";
    status.classList.remove("error-text");

    try {
        const response = await fetch(`/api/admin/users/${encodeURIComponent(user.id)}/password`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                password: password
            })
        });
        const result = await response.json();
        if (!response.ok || !result.success) {
            throw new Error(result.message || "密码重置失败");
        }

        passwordInput.value = "";
        status.textContent = "密码已重置";
    } catch (error) {
        status.textContent = error.message;
        status.classList.add("error-text");
    } finally {
        button.disabled = false;
    }
}

if (refreshAdminUsersButton) {
    refreshAdminUsersButton.addEventListener("click", loadAdminUsers);
}

async function loadAdminComments() {
    if (!adminCommentList) {
        return;
    }

    setTextStatus(adminCommentStatus, "正在读取...");
    adminCommentList.innerHTML = "";

    try {
        const params = new URLSearchParams({
            page_key: adminCommentPageKey.value,
            sort: adminCommentSort.value,
            page_size: "100"
        });
        const response = await fetch(`/api/admin/comments?${params.toString()}`);
        const result = await response.json();
        if (!response.ok || !result.success) {
            throw new Error(result.message || "评论读取失败");
        }

        renderAdminComments(result.comments || []);
        adminCommentList.dataset.loaded = "1";
        setTextStatus(adminCommentStatus, `共 ${Number(result.total || 0)} 条评论`);
    } catch (error) {
        adminCommentList.innerHTML = "";
        setTextStatus(adminCommentStatus, error.message, true);
    }
}

function renderAdminComments(comments) {
    adminCommentList.innerHTML = "";

    if (!comments.length) {
        adminCommentList.innerHTML = '<p class="empty-state">暂无评论</p>';
        updateSelectedCommentState();
        return;
    }

    comments.forEach(function (comment) {
        const row = document.createElement("article");
        row.className = "log-row admin-comment-row";
        row.dataset.commentId = String(comment.id || "");

        const head = document.createElement("div");
        head.className = "log-row-head";
        const sourceLabel = comment.page_key || "unknown";
        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.className = "admin-comment-check";
        checkbox.value = String(comment.id || "");
        checkbox.setAttribute("aria-label", `选择评论 ${comment.id}`);
        checkbox.addEventListener("change", updateSelectedCommentState);

        head.innerHTML = `
            <strong>${escapeHtml(comment.nickname || "匿名用户")}</strong>
            <span>评论 ID ${Number(comment.id || 0)}</span>
            <span>来源 ${escapeHtml(sourceLabel)}</span>
            <small>${escapeHtml(comment.created_at || "")} · 点赞 ${Number(comment.like_count || 0)} · 回复 ${Number(comment.reply_count || 0)}</small>
        `;
        head.prepend(checkbox);

        const content = document.createElement("p");
        content.textContent = comment.content || "";

        const actions = document.createElement("div");
        actions.className = "admin-comment-actions";
        const openLink = document.createElement("a");
        openLink.className = "small-button admin-comment-open";
        openLink.href = `/comments/${comment.id}?page_key=${encodeURIComponent(comment.page_key || "tools")}&from=admin`;
        openLink.target = "_blank";
        openLink.rel = "noopener";
        openLink.textContent = "打开";

        const deleteButton = createSmallButton("删除", function () {
            deleteAdminComment(comment);
        });
        deleteButton.classList.add("danger-button");

        actions.appendChild(openLink);
        actions.appendChild(deleteButton);

        row.appendChild(head);
        row.appendChild(content);
        row.appendChild(actions);
        adminCommentList.appendChild(row);
    });

    updateSelectedCommentState();
}

async function deleteAdminComment(comment) {
    if (!window.confirm(`确认删除 #${comment.id} 这条评论？删除后会同时删除点赞和回复。`)) {
        return;
    }

    setTextStatus(adminCommentStatus, "正在删除...");

    try {
        const response = await fetch(`/api/admin/comments/${encodeURIComponent(comment.id)}`, {
            method: "DELETE"
        });
        const result = await response.json();
        if (!response.ok || !result.success) {
            throw new Error(result.message || "删除失败");
        }
        removeAdminCommentRows([comment.id]);
        setTextStatus(adminCommentStatus, "评论已删除");
    } catch (error) {
        setTextStatus(adminCommentStatus, error.message, true);
    }
}

function getSelectedAdminCommentIds() {
    return Array.from(adminCommentList.querySelectorAll(".admin-comment-check:checked"))
        .map((checkbox) => Number(checkbox.value))
        .filter((commentId) => commentId > 0);
}

function updateSelectedCommentState() {
    if (!deleteSelectedCommentsButton || !adminCommentList) {
        return;
    }
    const selectedCount = getSelectedAdminCommentIds().length;
    deleteSelectedCommentsButton.disabled = selectedCount === 0;
    deleteSelectedCommentsButton.textContent = selectedCount > 0
        ? `删除选中 ${selectedCount}`
        : "删除选中";
}

function removeAdminCommentRows(commentIds) {
    const idSet = new Set((commentIds || []).map((commentId) => String(commentId)));
    adminCommentList.querySelectorAll(".admin-comment-row").forEach((row) => {
        if (idSet.has(row.dataset.commentId)) {
            row.remove();
        }
    });

    if (!adminCommentList.querySelector(".admin-comment-row")) {
        adminCommentList.innerHTML = '<p class="empty-state">暂无评论</p>';
    }

    updateSelectedCommentState();
}

async function deleteSelectedAdminComments() {
    const commentIds = getSelectedAdminCommentIds();

    if (!commentIds.length) {
        setTextStatus(adminCommentStatus, "请选择要删除的评论", true);
        return;
    }

    if (!window.confirm(`确认删除选中的 ${commentIds.length} 条评论？删除后会同时删除点赞和回复。`)) {
        return;
    }

    setTextStatus(adminCommentStatus, "正在批量删除...");
    deleteSelectedCommentsButton.disabled = true;

    try {
        const response = await fetch("/api/admin/comments/bulk", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                comment_ids: commentIds
            })
        });
        const result = await response.json();
        if (!response.ok || !result.success) {
            throw new Error(result.message || "批量删除失败");
        }
        const deletedIds = result.data && result.data.ids ? result.data.ids : commentIds;
        removeAdminCommentRows(deletedIds);
        setTextStatus(adminCommentStatus, `已删除 ${Number((result.data && result.data.deleted_count) || deletedIds.length)} 条评论`);
    } catch (error) {
        try {
            const deletedIds = await deleteAdminCommentsOneByOne(commentIds);
            removeAdminCommentRows(deletedIds);
            setTextStatus(adminCommentStatus, `已删除 ${deletedIds.length} 条评论`);
        } catch (fallbackError) {
            setTextStatus(adminCommentStatus, fallbackError.message || error.message, true);
            updateSelectedCommentState();
        }
    }
}

async function deleteAdminCommentsOneByOne(commentIds) {
    const deletedIds = [];

    for (const commentId of commentIds) {
        const response = await fetch(`/api/admin/comments/${encodeURIComponent(commentId)}`, {
            method: "DELETE"
        });
        const result = await response.json();
        if (!response.ok || !result.success) {
            throw new Error(result.message || `评论 ${commentId} 删除失败`);
        }
        deletedIds.push(commentId);
    }

    return deletedIds;
}

if (refreshAdminCommentsButton) {
    refreshAdminCommentsButton.addEventListener("click", loadAdminComments);
}

if (deleteSelectedCommentsButton) {
    deleteSelectedCommentsButton.disabled = true;
    deleteSelectedCommentsButton.addEventListener("click", deleteSelectedAdminComments);
}

if (adminCommentPageKey) {
    adminCommentPageKey.addEventListener("change", loadAdminComments);
}

if (adminCommentSort) {
    adminCommentSort.addEventListener("change", loadAdminComments);
}

loadTools();
