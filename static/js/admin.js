const saveStatus = document.querySelector("#save-status");
const searchInput = document.querySelector("#endpoint-search");
const endpointItems = Array.from(document.querySelectorAll(".endpoint-item"));
const toolSource = document.querySelector("#tool-source");
const toolList = document.querySelector("#tool-list");
const toolFilePath = document.querySelector("#tool-file-path");
const toolSourceNote = document.querySelector("#tool-source-note");
const toolForm = document.querySelector("#tool-form");
const toolStatus = document.querySelector("#tool-status");

let currentTools = [];

const sourceNotes = {
    local: "本地工具 JSON 会被 /tools 页面读取。为了保持本地工具页默认入口，新增自定义工具建议保存到“自定义工具 JSON”。",
    fastgpt: "FastGPT JSON 用于 FastGPT 工具页和推荐流程。",
    custom: "自定义工具 JSON 保存到 data/admin/custom_tools.json，不会被当前本地工具页默认加载。"
};

function setTextStatus(element, message, isError = false) {
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
    });
});

searchInput.addEventListener("input", () => {
    const keyword = searchInput.value.trim().toLowerCase();

    endpointItems.forEach((item) => {
        const text = item.dataset.search.toLowerCase();
        item.hidden = keyword && !text.includes(keyword);
    });
});

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
                headers: {
                    "Content-Type": "application/json"
                },
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

    currentTools.forEach((tool) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "tool-row";
        button.innerHTML = `
            <strong>${tool.title || tool.id}</strong>
            <span>${tool.id || ""}</span>
            <small>${tool.category || "未分类"} · ${tool.enabled === false ? "停用" : "启用"}</small>
        `;
        button.addEventListener("click", () => fillToolForm(tool));
        toolList.appendChild(button);
    });
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
        toolFilePath.textContent = result.data.file || "";
        renderToolList();
        setTextStatus(toolStatus, `已读取 ${currentTools.length} 条工具`);
    } catch (error) {
        currentTools = [];
        renderToolList();
        setTextStatus(toolStatus, error.message, true);
    }
}

function toolExtraJson(tool) {
    const baseFields = new Set(["id", "title", "desc", "category", "type", "url", "enabled", "default"]);
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
    toolForm.elements.url.value = tool.url || "";
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
        url: toolForm.elements.url.value.trim(),
        desc: toolForm.elements.desc.value.trim(),
        extra_json: toolForm.elements.extra_json.value.trim(),
        enabled: toolForm.elements.enabled.checked,
        default: toolForm.elements.default.checked,
        sync_db: toolForm.elements.sync_db.checked
    };

    setTextStatus(toolStatus, "正在保存工具...");

    try {
        const response = await fetch("/api/admin/tools", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });
        const result = await response.json();

        if (!response.ok || !result.success) {
            throw new Error(result.message || "保存失败");
        }

        await loadTools();

        if (payload.sync_db && result.data.db_error) {
            setTextStatus(toolStatus, `JSON 已保存，数据库同步失败：${result.data.db_error}`, true);
            return;
        }

        setTextStatus(toolStatus, result.data.created ? "工具已添加" : "工具已更新");
    } catch (error) {
        setTextStatus(toolStatus, error.message, true);
    }
});

loadTools();
