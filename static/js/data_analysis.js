const root = document.getElementById("dataAnalysisApp");
const { createApp, nextTick } = Vue;

function requestJson(url, options) {
    return fetch(url, options).then(function (response) {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        return response.json();
    });
}

function svgEl(name, attrs) {
    const node = document.createElementNS("http://www.w3.org/2000/svg", name);

    Object.entries(attrs || {}).forEach(function ([key, value]) {
        node.setAttribute(key, value);
    });

    return node;
}

function getFallbackAnalysisData() {
    return {
        resultDesc: "已加载示例分析结果，你可以上传文件后继续联调真实接口。",
        metrics: [
            { label: "记录总数", value: "1,248", note: "样例数据已就绪" },
            { label: "异常条目", value: "18", note: "需要人工确认", level: "warning" },
            { label: "通过率", value: "96.4%", note: "整体状态稳定" },
            { label: "平均耗时", value: "1.8s", note: "接口响应正常" }
        ],
        chart: {
            labels: ["周一", "周二", "周三", "周四", "周五"],
            series: [120, 188, 156, 210, 174]
        },
        insights: [
            { title: "高峰出现在周四", desc: "示例数据中周四处理量最高，适合用来观察图表切换效果。" },
            { title: "异常值集中在少量记录", desc: "当前异常条目占比不高，适合作为告警样例。", level: "warning" },
            { title: "表格与图表已联动", desc: "后续接入真实分析接口后，这里会自动刷新。" }
        ],
        table: {
            columns: [
                { key: "name", label: "名称" },
                { key: "count", label: "数量" },
                { key: "status", label: "状态", type: "tag" }
            ],
            rows: [
                { name: "样例 A", count: 320, status: "ok" },
                { name: "样例 B", count: 278, status: "warn" },
                { name: "样例 C", count: 196, status: "ok" },
                { name: "样例 D", count: 84, status: "risk" }
            ]
        },
        statusMap: {
            ok: { label: "正常", level: "" },
            warn: { label: "关注", level: "warning" },
            risk: { label: "风险", level: "danger" }
        }
    };
}

function getFallbackPageConfig() {
    return {
        page: {
            title: "数据分析工作台",
            subtitle: "局部接入 Vue 的分析页面",
            statusText: "示例模式",
            backUrl: "/",
            backIcon: "←",
            backLabel: "返回首页"
        },
        upload: {
            title: "上传数据文件",
            desc: "拖拽或选择文件，结合筛选条件生成分析结果。",
            icon: "↑",
            dropTitle: "将文件拖到这里，或点击选择文件",
            dropMeta: "支持 CSV、Excel 等常见数据文件",
            accept: ".csv,.xlsx,.xls,.txt",
            fileSummary: {
                emptyTitle: "尚未选择文件",
                emptyMeta: "当前会先展示示例分析数据",
                selectedMeta: "大小 {size} · 类型 {type}",
                unknownType: "未知类型"
            }
        },
        filters: [
            {
                id: "dimensionSelect",
                name: "dimension",
                label: "分析维度",
                options: [
                    { value: "daily", label: "按日汇总" },
                    { value: "weekly", label: "按周汇总" },
                    { value: "monthly", label: "按月汇总" }
                ]
            },
            {
                id: "scopeSelect",
                name: "scope",
                label: "分析范围",
                options: [
                    { value: "all", label: "全部数据" },
                    { value: "core", label: "核心数据" },
                    { value: "abnormal", label: "异常数据" }
                ]
            }
        ],
        buttons: {
            analyze: "开始分析",
            reset: "重置",
            export: "导出结果"
        },
        steps: [
            { index: 1, title: "上传文件", desc: "拖入待分析文件或手动选择本地文件。" },
            { index: 2, title: "选择筛选条件", desc: "根据分析目标切换维度与范围。" },
            { index: 3, title: "查看结果", desc: "阅读指标、图表、洞察和明细表格。" }
        ],
        sections: {
            overview: {
                title: "分析概览",
                desc: "这里展示核心指标与结果摘要。"
            },
            chart: {
                title: "趋势图表",
                desc: "支持柱状图和折线图切换。",
                ariaLabel: "数据趋势图表"
            },
            insight: {
                title: "分析洞察",
                desc: "提取值得关注的变化和提示。"
            },
            table: {
                title: "明细结果",
                desc: "保留结构化数据，便于进一步核对。"
            }
        },
        chart: {
            defaultType: "bar",
            tabs: [
                { type: "bar", label: "柱状图" },
                { type: "line", label: "折线图" }
            ]
        },
        loadingText: "分析中...",
        messages: {
            analyzing: "正在根据当前文件和筛选条件生成分析结果..."
        },
        initialAnalysisData: getFallbackAnalysisData()
    };
}

function normalizePageConfig(config) {
    if (!config || typeof config !== "object") {
        return getFallbackPageConfig();
    }

    return {
        ...getFallbackPageConfig(),
        ...config,
        page: { ...getFallbackPageConfig().page, ...(config.page || {}) },
        upload: {
            ...getFallbackPageConfig().upload,
            ...(config.upload || {}),
            fileSummary: {
                ...getFallbackPageConfig().upload.fileSummary,
                ...((config.upload && config.upload.fileSummary) || {})
            }
        },
        buttons: { ...getFallbackPageConfig().buttons, ...(config.buttons || {}) },
        sections: {
            overview: {
                ...getFallbackPageConfig().sections.overview,
                ...((config.sections && config.sections.overview) || {})
            },
            chart: {
                ...getFallbackPageConfig().sections.chart,
                ...((config.sections && config.sections.chart) || {})
            },
            insight: {
                ...getFallbackPageConfig().sections.insight,
                ...((config.sections && config.sections.insight) || {})
            },
            table: {
                ...getFallbackPageConfig().sections.table,
                ...((config.sections && config.sections.table) || {})
            }
        },
        chart: {
            ...getFallbackPageConfig().chart,
            ...(config.chart || {})
        },
        messages: {
            ...getFallbackPageConfig().messages,
            ...(config.messages || {})
        },
        filters: Array.isArray(config.filters) ? config.filters : getFallbackPageConfig().filters,
        steps: Array.isArray(config.steps) ? config.steps : getFallbackPageConfig().steps,
        initialAnalysisData: config.initialAnalysisData || getFallbackPageConfig().initialAnalysisData
    };
}

function normalizeAnalysisData(data) {
    if (!data || typeof data !== "object") {
        return getFallbackAnalysisData();
    }

    return {
        ...getFallbackAnalysisData(),
        ...data,
        chart: {
            ...getFallbackAnalysisData().chart,
            ...(data.chart || {})
        },
        table: {
            ...getFallbackAnalysisData().table,
            ...(data.table || {})
        },
        metrics: Array.isArray(data.metrics) ? data.metrics : getFallbackAnalysisData().metrics,
        insights: Array.isArray(data.insights) ? data.insights : getFallbackAnalysisData().insights,
        statusMap: data.statusMap || getFallbackAnalysisData().statusMap
    };
}

const dataAnalysisVueApp = createApp({
    data: function () {
        return {
            pageConfig: getFallbackPageConfig(),
            analysisData: getFallbackAnalysisData(),
            chartType: "bar",
            selectedFile: null,
            filterValues: {},
            isAnalyzing: false,
            isDragging: false
        };
    },

    computed: {
        fileSummaryTitle: function () {
            if (!this.selectedFile) {
                return this.pageConfig.upload.fileSummary.emptyTitle;
            }

            return this.selectedFile.name;
        },

        fileSummaryMeta: function () {
            if (!this.selectedFile) {
                return this.pageConfig.upload.fileSummary.emptyMeta;
            }

            return this.pageConfig.upload.fileSummary.selectedMeta
                .replace("{size}", this.formatSize(this.selectedFile.size))
                .replace("{type}", this.selectedFile.type || this.pageConfig.upload.fileSummary.unknownType);
        }
    },

    methods: {
        formatSize: function (bytes) {
            if (!bytes) {
                return "";
            }

            const units = ["B", "KB", "MB", "GB"];
            const index = Math.min(
                Math.floor(Math.log(bytes) / Math.log(1024)),
                units.length - 1
            );

            return `${(bytes / Math.pow(1024, index)).toFixed(index ? 1 : 0)} ${units[index]}`;
        },

        tagMeta: function (value) {
            return (this.analysisData.statusMap || {})[value] || {};
        },

        initFilterValues: function () {
            const nextValues = {};

            this.pageConfig.filters.forEach(function (filter) {
                const firstOption = Array.isArray(filter.options) && filter.options.length > 0
                    ? filter.options[0].value
                    : "";

                nextValues[filter.name] = firstOption;
            });

            this.filterValues = nextValues;
        },

        loadPageConfig: async function () {
            try {
                const data = await requestJson(root.dataset.pageConfigUrl);
                this.pageConfig = normalizePageConfig(data);
            } catch (error) {
                this.pageConfig = getFallbackPageConfig();
            }

            this.chartType = this.pageConfig.chart.defaultType || "bar";
            this.analysisData = normalizeAnalysisData(this.pageConfig.initialAnalysisData);
            this.initFilterValues();
            document.title = this.pageConfig.page.title;

            await nextTick();
            this.renderChart();
        },

        runAnalysis: async function (formData) {
            try {
                const data = await requestJson(root.dataset.analysisUrl, {
                    method: "POST",
                    body: formData
                });

                return normalizeAnalysisData(data);
            } catch (error) {
                return getFallbackAnalysisData();
            }
        },

        handleFileChange: function (event) {
            const files = event.target.files || [];
            this.selectedFile = files[0] || null;
        },

        handleDrop: function (event) {
            this.isDragging = false;

            const files = event.dataTransfer.files || [];
            const file = files[0] || null;

            this.selectedFile = file;
        },

        setChartType: function (type) {
            this.chartType = type;
            this.$nextTick(this.renderChart);
        },

        handleAnalyze: async function () {
            const formData = new FormData();

            if (this.selectedFile) {
                formData.append("file", this.selectedFile);
            }

            Object.entries(this.filterValues).forEach(function ([key, value]) {
                formData.append(key, value);
            });

            this.isAnalyzing = true;
            this.analysisData = {
                ...this.analysisData,
                resultDesc: this.pageConfig.messages.analyzing
            };

            const data = await this.runAnalysis(formData);
            this.analysisData = data;
            this.isAnalyzing = false;

            await nextTick();
            this.renderChart();
        },

        resetAnalysis: async function () {
            this.selectedFile = null;
            this.analysisData = normalizeAnalysisData(this.pageConfig.initialAnalysisData);
            this.chartType = this.pageConfig.chart.defaultType || "bar";
            this.initFilterValues();

            if (this.$refs.fileInput) {
                this.$refs.fileInput.value = "";
            }

            await nextTick();
            this.renderChart();
        },

        appendChartText: function (svg, x, y, text, fill, fontWeight) {
            const node = svgEl("text", {
                x,
                y,
                "text-anchor": "middle",
                "font-size": 12,
                "font-weight": fontWeight,
                fill
            });

            node.textContent = text;
            svg.appendChild(node);
        },

        renderBarChart: function (svg, labels, values, max, width, height, padding, innerWidth, innerHeight) {
            const gap = 16;
            const barWidth = Math.max(24, (innerWidth - gap * (values.length - 1)) / values.length);
            const self = this;

            values.forEach(function (value, index) {
                const x = padding.left + index * (barWidth + gap);
                const barHeight = value / max * innerHeight;
                const y = padding.top + innerHeight - barHeight;

                svg.appendChild(svgEl("rect", {
                    x,
                    y,
                    width: Math.min(barWidth, width),
                    height: barHeight,
                    rx: 6,
                    fill: index < 2 ? "#2563eb" : "#7dd3fc"
                }));

                self.appendChartText(svg, x + barWidth / 2, y - 8, value, "#344054", 700);
                self.appendChartText(svg, x + barWidth / 2, height - 16, labels[index], "#667085", 400);
            });
        },

        renderLineChart: function (svg, labels, values, max, height, padding, innerWidth, innerHeight) {
            const points = values.map(function (value, index) {
                const x = padding.left + index * (innerWidth / Math.max(values.length - 1, 1));
                const y = padding.top + innerHeight - value / max * innerHeight;
                return [x, y, value];
            });

            const path = points.map(function (point, index) {
                return `${index ? "L" : "M"} ${point[0]} ${point[1]}`;
            }).join(" ");
            const areaPath = `${path} L ${points[points.length - 1][0]} ${padding.top + innerHeight} L ${points[0][0]} ${padding.top + innerHeight} Z`;
            const self = this;

            svg.appendChild(svgEl("path", {
                d: areaPath,
                fill: "#dbeafe",
                opacity: 0.75
            }));
            svg.appendChild(svgEl("path", {
                d: path,
                fill: "none",
                stroke: "#2563eb",
                "stroke-width": 3,
                "stroke-linecap": "round",
                "stroke-linejoin": "round"
            }));

            points.forEach(function ([x, y, value], index) {
                svg.appendChild(svgEl("circle", {
                    cx: x,
                    cy: y,
                    r: 5,
                    fill: "#ffffff",
                    stroke: "#2563eb",
                    "stroke-width": 3
                }));

                self.appendChartText(svg, x, y - 12, value, "#344054", 700);
                self.appendChartText(svg, x, height - 16, labels[index], "#667085", 400);
            });
        },

        renderChart: function () {
            const svg = this.$refs.chartSvg;
            const chart = this.analysisData.chart || {};

            if (!svg) {
                return;
            }

            if (!chart.labels || !chart.series || !chart.labels.length || !chart.series.length) {
                svg.innerHTML = "";
                return;
            }

            const labels = chart.labels;
            const values = chart.series;
            const width = svg.clientWidth || 760;
            const height = 290;
            const padding = { top: 18, right: 18, bottom: 42, left: 44 };
            const innerWidth = width - padding.left - padding.right;
            const innerHeight = height - padding.top - padding.bottom;
            const max = Math.max(...values, 1) * 1.18;

            svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
            svg.innerHTML = "";

            [0, 0.25, 0.5, 0.75, 1].forEach(function (ratio) {
                const y = padding.top + innerHeight * ratio;

                svg.appendChild(svgEl("line", {
                    x1: padding.left,
                    x2: width - padding.right,
                    y1: y,
                    y2: y,
                    stroke: "#e5e7eb",
                    "stroke-width": 1
                }));
            });

            if (this.chartType === "bar") {
                this.renderBarChart(svg, labels, values, max, width, height, padding, innerWidth, innerHeight);
                return;
            }

            this.renderLineChart(svg, labels, values, max, height, padding, innerWidth, innerHeight);
        }
    },

    mounted: function () {
        this.loadPageConfig();
        window.addEventListener("resize", this.renderChart);
    },

    beforeUnmount: function () {
        window.removeEventListener("resize", this.renderChart);
    }
});

dataAnalysisVueApp.config.compilerOptions.delimiters = ["[[", "]]"];
dataAnalysisVueApp.mount("#dataAnalysisApp");
