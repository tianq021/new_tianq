const saveStatus = document.querySelector("#save-status");
const searchInput = document.querySelector("#endpoint-search");
const endpointItems = Array.from(document.querySelectorAll(".endpoint-item"));
const toolSource = document.querySelector("#tool-source");
const toolList = document.querySelector("#tool-list");
const toolFilePath = document.querySelector("#tool-file-path");
const toolSourceNote = document.querySelector("#tool-source-note");
const toolForm = document.querySelector("#tool-form");
const toolStatus = document.querySelector("#tool-status");
const exportButton = document.querySelector("#config-export");
const refreshLogsButton = document.querySelector("#refresh-fastgpt-logs");
const logLimit = document.querySelector("#fastgpt-log-limit");
const logStatus = document.querySelector("#fastgpt-log-status");
const logList = document.querySelector("#fastgpt-log-list");

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
        summary.innerHTML = `
            <strong>${escapeHtml(tool.title || tool.id)}</strong>
            <span>${escapeHtml(tool.id || "")}</span>
            <small>${escapeHtml(tool.category || "未分类")} · 排序 ${Number(tool.sort_order || 100)} · ${tool.enabled === false ? "停用" : "启用"}${tool.has_api_key === false ? " · 未配置 Key" : ""}</small>
        `;
        summary.addEventListener("click", () => fillToolForm(tool));

        const actions = document.createElement("div");
        actions.className = "tool-row-actions";
        actions.appendChild(createSmallButton(tool.enabled === false ? "启用" : "停用", () => {
            updateToolState(tool.id, { enabled: tool.enabled === false });
        }));
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

async function loadTools() {
    setTextStatus(toolStatus, "正在读取...");
    toolSourceNote.textContent = sourceNotes[toolSource.value] || "";

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
    toolForm.elements.category.value = tool.category || "";
    toolForm.elements.type.value = tool.type || "link";
    toolForm.elements.sort_order.value = tool.sort_order || 100;
    toolForm.elements.url.value = tool.url || "";
    toolForm.elements.chat_id.value = tool.chat_id || tool.id || "";
    toolForm.elements.api_key.value = "";
    toolForm.elements.desc.value = tool.desc || "";
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
    setTextStatus(toolStatus, "");
}

document.querySelector("#tool-reset").addEventListener("click", resetToolForm);
toolSource.addEventListener("change", () => {
    resetToolForm();
    loadTools();
});

toolForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const payload = {
        source: toolSource.value,
        id: toolForm.elements.id.value.trim(),
        title: toolForm.elements.title.value.trim(),
        category: toolForm.elements.category.value.trim(),
        type: toolForm.elements.type.value.trim() || "link",
        sort_order: Number(toolForm.elements.sort_order.value || 100),
        url: toolForm.elements.url.value.trim(),
        chat_id: toolForm.elements.chat_id.value.trim(),
        api_key: toolForm.elements.api_key.value.trim(),
        desc: toolForm.elements.desc.value.trim(),
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
                <strong>${escapeHtml(item.chat_id || "unknown")}</strong>
                <span>${item.success ? "成功" : "失败"}</span>
                <small>${escapeHtml(item.created_at || "")} · ${Number(item.elapsed_ms || 0).toFixed(0)} ms · ${escapeHtml(item.remote_addr || "")}</small>
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

loadTools();
