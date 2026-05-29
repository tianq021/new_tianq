const app = document.getElementById("dataAnalysisApp");

const state = {
    pageConfig: null,
    analysisData: null,
    chartType: "",
    selectedFile: null
};

const els = {
    pageTitle: document.getElementById("pageTitle"),
    backLink: document.getElementById("backLink"),
    brandTitle: document.getElementById("brandTitle"),
    brandSubtitle: document.getElementById("brandSubtitle"),
    statusText: document.getElementById("statusText"),
    uploadTitle: document.getElementById("uploadTitle"),
    uploadDesc: document.getElementById("uploadDesc"),
    uploadIcon: document.getElementById("uploadIcon"),
    uploadDropTitle: document.getElementById("uploadDropTitle"),
    uploadDropMeta: document.getElementById("uploadDropMeta"),
    fileInput: document.getElementById("fileInput"),
    fileSummary: document.getElementById("fileSummary"),
    filterList: document.getElementById("filterList"),
    analyzeBtn: document.getElementById("analyzeBtn"),
    resetBtn: document.getElementById("resetBtn"),
    stepList: document.getElementById("stepList"),
    overviewTitle: document.getElementById("overviewTitle"),
    resultDesc: document.getElementById("resultDesc"),
    loading: document.getElementById("loading"),
    loadingText: document.getElementById("loadingText"),
    metricGrid: document.getElementById("metricGrid"),
    chartTitle: document.getElementById("chartTitle"),
    chartDesc: document.getElementById("chartDesc"),
    chartTabs: document.getElementById("chartTabs"),
    chartSvg: document.getElementById("chartSvg"),
    insightTitle: document.getElementById("insightTitle"),
    insightDesc: document.getElementById("insightDesc"),
    insightList: document.getElementById("insightList"),
    tableTitle: document.getElementById("tableTitle"),
    tableDesc: document.getElementById("tableDesc"),
    exportBtn: document.getElementById("exportBtn"),
    tableHead: document.getElementById("tableHead"),
    tableBody: document.getElementById("tableBody"),
    dropZone: document.getElementById("dropZone")
};

async function requestJson(url, options) {
    const response = await fetch(url, options);
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }
    return response.json();
}

async function loadPageConfig() {
    try {
        return await requestJson(app.dataset.pageConfigUrl);
    } catch (error) {
        return getEmptyPageConfig();
    }
}

async function runAnalysis(formData) {
    try {
        return await requestJson(app.dataset.analysisUrl, {
            method: "POST",
            body: formData
        });
    } catch (error) {
        return getEmptyAnalysisData();
    }
}

function setText(el, value) {
    el.textContent = value || "";
}

function formatSize(bytes) {
    if (!bytes) return "";
    const units = ["B", "KB", "MB", "GB"];
    const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
    return `${(bytes / Math.pow(1024, index)).toFixed(index ? 1 : 0)} ${units[index]}`;
}

function renderPageConfig(config) {
    state.pageConfig = config;
    state.chartType = config.chart.defaultType || "";

    document.title = config.page.title;
    setText(els.pageTitle, config.page.title);
    setText(els.backLink, config.page.backIcon);
    els.backLink.href = config.page.backUrl;
    els.backLink.setAttribute("aria-label", config.page.backLabel);
    setText(els.brandTitle, config.page.title);
    setText(els.brandSubtitle, config.page.subtitle);
    setText(els.statusText, config.page.statusText);

    setText(els.uploadTitle, config.upload.title);
    setText(els.uploadDesc, config.upload.desc);
    setText(els.uploadIcon, config.upload.icon);
    setText(els.uploadDropTitle, config.upload.dropTitle);
    setText(els.uploadDropMeta, config.upload.dropMeta);
    els.fileInput.accept = config.upload.accept;
    setFile(null);

    setText(els.analyzeBtn, config.buttons.analyze);
    setText(els.resetBtn, config.buttons.reset);
    setText(els.exportBtn, config.buttons.export);
    setText(els.loadingText, config.loadingText);

    renderFilters(config.filters);
    renderSteps(config.steps);
    renderChartTabs(config.chart.tabs);

    setText(els.overviewTitle, config.sections.overview.title);
    setText(els.resultDesc, config.sections.overview.desc);
    setText(els.chartTitle, config.sections.chart.title);
    setText(els.chartDesc, config.sections.chart.desc);
    els.chartSvg.setAttribute("aria-label", config.sections.chart.ariaLabel);
    setText(els.insightTitle, config.sections.insight.title);
    setText(els.insightDesc, config.sections.insight.desc);
    setText(els.tableTitle, config.sections.table.title);
    setText(els.tableDesc, config.sections.table.desc);
}

function renderFilters(filters) {
    els.filterList.innerHTML = "";
    filters.forEach((filter) => {
        const row = document.createElement("div");
        row.className = "form-row";

        const label = document.createElement("label");
        label.setAttribute("for", filter.id);
        label.textContent = filter.label;

        const select = document.createElement("select");
        select.id = filter.id;
        select.name = filter.name;
        filter.options.forEach((item) => {
            const option = document.createElement("option");
            option.value = item.value;
            option.textContent = item.label;
            select.appendChild(option);
        });

        row.append(label, select);
        els.filterList.appendChild(row);
    });
}

function renderSteps(steps) {
    els.stepList.innerHTML = steps.map((step) => `
        <div class="step">
            <span class="step-num">${step.index}</span>
            <div>
                <strong>${step.title}</strong>
                <span>${step.desc}</span>
            </div>
        </div>
    `).join("");
}

function renderChartTabs(tabs) {
    els.chartTabs.innerHTML = tabs.map((tab) => `
        <button
            class="chart-tab ${tab.type === state.chartType ? "active" : ""}"
            type="button"
            data-chart="${tab.type}"
        >${tab.label}</button>
    `).join("");

    els.chartTabs.querySelectorAll(".chart-tab").forEach((button) => {
        button.addEventListener("click", () => {
            els.chartTabs.querySelectorAll(".chart-tab").forEach((item) => item.classList.remove("active"));
            button.classList.add("active");
            state.chartType = button.dataset.chart;
            renderChart();
        });
    });
}

function setFile(file) {
    state.selectedFile = file || null;
    const labels = state.pageConfig.upload.fileSummary;
    const name = document.createElement("strong");
    const meta = document.createElement("span");
    name.textContent = file ? file.name : labels.emptyTitle;
    meta.textContent = file
        ? labels.selectedMeta
            .replace("{size}", formatSize(file.size))
            .replace("{type}", file.type || labels.unknownType)
        : labels.emptyMeta;

    els.fileSummary.replaceChildren(name, meta);
}

function renderAnalysis(data) {
    state.analysisData = data || getEmptyAnalysisData();
    setText(els.resultDesc, data.resultDesc);
    renderMetrics(data.metrics || []);
    renderInsights(data.insights || []);
    renderTable(data.table || { columns: [], rows: [] });
    renderChart();
}

function renderMetrics(metrics) {
    els.metricGrid.innerHTML = metrics.map((metric) => `
        <div class="section metric">
            <p class="metric-label">${metric.label}</p>
            <p class="metric-value">${metric.value}</p>
            <p class="metric-note ${metric.level || ""}">${metric.note}</p>
        </div>
    `).join("");
}

function renderInsights(items) {
    els.insightList.innerHTML = items.map((item) => `
        <li class="insight-item ${item.level || ""}">
            <span class="insight-mark"></span>
            <div>
                <strong>${item.title}</strong>
                <span>${item.desc}</span>
            </div>
        </li>
    `).join("");
}

function renderTable(table) {
    els.tableHead.innerHTML = table.columns.map((column) => `<th>${column.label}</th>`).join("");
    els.tableBody.innerHTML = table.rows.map((row) => `
        <tr>
            ${table.columns.map((column) => renderTableCell(row[column.key], column)).join("")}
        </tr>
    `).join("");
}

function renderTableCell(value, column) {
    if (column.type !== "tag") {
        return `<td>${value}</td>`;
    }

    const tag = (state.analysisData.statusMap || {})[value] || {};
    return `<td><span class="tag ${tag.level || ""}">${tag.label || value}</span></td>`;
}

function svgEl(name, attrs = {}) {
    const node = document.createElementNS("http://www.w3.org/2000/svg", name);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
    return node;
}

function renderChart() {
    const chart = state.analysisData.chart || {};
    if (!chart.labels || !chart.series || !chart.labels.length || !chart.series.length) {
        els.chartSvg.innerHTML = "";
        return;
    }

    const labels = chart.labels;
    const values = chart.series;
    const width = els.chartSvg.clientWidth || 760;
    const height = 290;
    const padding = { top: 18, right: 18, bottom: 42, left: 44 };
    const innerWidth = width - padding.left - padding.right;
    const innerHeight = height - padding.top - padding.bottom;
    const max = Math.max(...values, 1) * 1.18;

    els.chartSvg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    els.chartSvg.innerHTML = "";

    [0, 0.25, 0.5, 0.75, 1].forEach((ratio) => {
        const y = padding.top + innerHeight * ratio;
        els.chartSvg.appendChild(svgEl("line", {
            x1: padding.left,
            x2: width - padding.right,
            y1: y,
            y2: y,
            stroke: "#e5e7eb",
            "stroke-width": 1
        }));
    });

    if (state.chartType === "bar") {
        renderBarChart(labels, values, max, width, height, padding, innerWidth, innerHeight);
        return;
    }

    renderLineChart(labels, values, max, height, padding, innerWidth, innerHeight);
}

function renderBarChart(labels, values, max, width, height, padding, innerWidth, innerHeight) {
    const gap = 16;
    const barWidth = Math.max(24, (innerWidth - gap * (values.length - 1)) / values.length);
    values.forEach((value, index) => {
        const x = padding.left + index * (barWidth + gap);
        const barHeight = value / max * innerHeight;
        const y = padding.top + innerHeight - barHeight;

        els.chartSvg.appendChild(svgEl("rect", {
            x,
            y,
            width: Math.min(barWidth, width),
            height: barHeight,
            rx: 6,
            fill: index < 2 ? "#2563eb" : "#7dd3fc"
        }));
        appendChartText(x + barWidth / 2, y - 8, value, "#344054", 700);
        appendChartText(x + barWidth / 2, height - 16, labels[index], "#667085", 400);
    });
}

function renderLineChart(labels, values, max, height, padding, innerWidth, innerHeight) {
    const points = values.map((value, index) => {
        const x = padding.left + index * (innerWidth / Math.max(values.length - 1, 1));
        const y = padding.top + innerHeight - value / max * innerHeight;
        return [x, y, value];
    });
    const path = points.map((point, index) => `${index ? "L" : "M"} ${point[0]} ${point[1]}`).join(" ");
    const areaPath = `${path} L ${points[points.length - 1][0]} ${padding.top + innerHeight} L ${points[0][0]} ${padding.top + innerHeight} Z`;

    els.chartSvg.appendChild(svgEl("path", {
        d: areaPath,
        fill: "#dbeafe",
        opacity: 0.75
    }));
    els.chartSvg.appendChild(svgEl("path", {
        d: path,
        fill: "none",
        stroke: "#2563eb",
        "stroke-width": 3,
        "stroke-linecap": "round",
        "stroke-linejoin": "round"
    }));

    points.forEach(([x, y, value], index) => {
        els.chartSvg.appendChild(svgEl("circle", {
            cx: x,
            cy: y,
            r: 5,
            fill: "#ffffff",
            stroke: "#2563eb",
            "stroke-width": 3
        }));
        appendChartText(x, y - 12, value, "#344054", 700);
        appendChartText(x, height - 16, labels[index], "#667085", 400);
    });
}

function appendChartText(x, y, text, fill, fontWeight) {
    const node = svgEl("text", {
        x,
        y,
        "text-anchor": "middle",
        "font-size": 12,
        "font-weight": fontWeight,
        fill
    });
    node.textContent = text;
    els.chartSvg.appendChild(node);
}

async function handleAnalyze() {
    const formData = new FormData();
    if (state.selectedFile) {
        formData.append("file", state.selectedFile);
    }
    els.filterList.querySelectorAll("select").forEach((select) => {
        formData.append(select.name, select.value);
    });

    els.loading.classList.add("show");
    els.analyzeBtn.disabled = true;
    setText(els.resultDesc, state.pageConfig.messages.analyzing);

    const data = await runAnalysis(formData);
    renderAnalysis(data);

    els.loading.classList.remove("show");
    els.analyzeBtn.disabled = false;
}

function bindEvents() {
    els.fileInput.addEventListener("change", (event) => {
        setFile(event.target.files[0]);
    });

    ["dragenter", "dragover"].forEach((type) => {
        els.dropZone.addEventListener(type, (event) => {
            event.preventDefault();
            els.dropZone.classList.add("dragging");
        });
    });

    ["dragleave", "drop"].forEach((type) => {
        els.dropZone.addEventListener(type, (event) => {
            event.preventDefault();
            els.dropZone.classList.remove("dragging");
        });
    });

    els.dropZone.addEventListener("drop", (event) => {
        const file = event.dataTransfer.files[0];
        if (file) setFile(file);
    });

    els.analyzeBtn.addEventListener("click", handleAnalyze);
    els.resetBtn.addEventListener("click", () => {
        els.fileInput.value = "";
        setFile(null);
        renderAnalysis(state.pageConfig.initialAnalysisData || getEmptyAnalysisData());
    });
    window.addEventListener("resize", renderChart);
}

async function init() {
    const config = await loadPageConfig();
    renderPageConfig(config);
    bindEvents();
    renderAnalysis(config.initialAnalysisData || getEmptyAnalysisData());
}

function getEmptyPageConfig() {
    return {
        page: {
            title: "",
            subtitle: "",
            statusText: "",
            backUrl: "/",
            backIcon: "",
            backLabel: ""
        },
        upload: {
            title: "",
            desc: "",
            icon: "",
            dropTitle: "",
            dropMeta: "",
            accept: "",
            fileSummary: {
                emptyTitle: "",
                emptyMeta: "",
                selectedMeta: "{size} {type}",
                unknownType: ""
            }
        },
        filters: [],
        buttons: {
            analyze: "",
            reset: "",
            export: ""
        },
        steps: [],
        sections: {
            overview: {
                title: "",
                desc: ""
            },
            chart: {
                title: "",
                desc: "",
                ariaLabel: ""
            },
            insight: {
                title: "",
                desc: ""
            },
            table: {
                title: "",
                desc: ""
            }
        },
        chart: {
            defaultType: "",
            tabs: []
        },
        loadingText: "",
        messages: {
            analyzing: ""
        },
        initialAnalysisData: getEmptyAnalysisData()
    };
}

function getEmptyAnalysisData() {
    return {
        resultDesc: "",
        metrics: [],
        chart: {
            labels: [],
            series: []
        },
        insights: [],
        table: {
            columns: [],
            rows: []
        },
        statusMap: {}
    };
}

init();
