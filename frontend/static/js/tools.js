document.addEventListener("DOMContentLoaded", function () {
    const menuItems = document.querySelectorAll(".tool-menu-item");
    const panels = document.querySelectorAll(".tool-panel");

    function scrollToPanel(targetPanel) {
        const content = targetPanel.closest(".content");

        if (content) {
            content.scrollTo({
                top: 0,
                behavior: "smooth"
            });
        }

        window.scrollTo({
            top: 0,
            behavior: "smooth",
        });
    }

    function showPanel(targetId, options) {
        const shouldScroll = options && options.scroll;

        menuItems.forEach(function (item) {
            item.classList.remove("active");
        });

        panels.forEach(function (panel) {
            panel.classList.remove("active");
        });

        const targetMenu = document.querySelector(
            `.tool-menu-item[data-target="${targetId}"]`
        );

        const targetPanel = document.getElementById(targetId);

        if (targetMenu) {
            targetMenu.classList.add("active");
        }

        if (targetPanel) {
            targetPanel.classList.add("active");

            if (shouldScroll) {
                window.setTimeout(function () {
                    scrollToPanel(targetPanel);
                }, 0);
            }
        }

        document.dispatchEvent(new CustomEvent("toolPanelShown", {
            detail: {
                targetId: targetId
            }
        }));
    }

    document.addEventListener("showToolPanel", function (event) {
        const targetId = event.detail && event.detail.targetId;

        if (!targetId) {
            return;
        }

        window.history.replaceState(null, "", window.location.pathname + window.location.search);
        showPanel(targetId, {
            scroll: true
        });
    });

    function showPanelFromHash() {
        const hashTarget = window.location.hash.replace("#", "");

        if (hashTarget && document.getElementById(hashTarget)) {
            showPanel(hashTarget, {
                scroll: true
            });
            return true;
        }

        return false;
    }

    window.addEventListener("hashchange", showPanelFromHash);

    menuItems.forEach(function (item) {
        item.addEventListener("click", function () {
            const targetId = item.dataset.target;

            if (!targetId) {
                return;
            }

            window.history.replaceState(null, "", window.location.pathname + window.location.search);
            showPanel(targetId, {
                scroll: true
            });
        });
    });

    const activeItem = document.querySelector(".tool-menu-item.active");

    if (window.location.hash) {
        window.history.replaceState(null, "", window.location.pathname + window.location.search);
    }

    if (activeItem) {
        showPanel(activeItem.dataset.target);
    } else if (menuItems.length > 0) {
        showPanel(menuItems[0].dataset.target);
    }
});

// 文字或数字哈希
document.addEventListener("DOMContentLoaded", function () {
    const textHashForms = document.querySelectorAll(".text-hash-form");

    textHashForms.forEach(function (form) {
        form.addEventListener("submit", async function (event) {
            event.preventDefault();

            const card = form.closest(".card");
            const input = form.querySelector(".hash-input");
            const lengthBox = card.querySelector(".text-hash-length");
            const md5Box = card.querySelector(".text-hash-md5");
            const sha1Box = card.querySelector(".text-hash-sha1");
            const sha256Box = card.querySelector(".text-hash-sha256");
            const sha512Box = card.querySelector(".text-hash-sha512");
            const messageBox = card.querySelector(".text-hash-message");
            const value = input.value;

            if (value.trim() === "") {
                messageBox.textContent = "请输入需要计算哈希值的内容";
                return;
            }

            messageBox.textContent = "正在计算...";
            lengthBox.textContent = "-";
            md5Box.textContent = "-";
            sha1Box.textContent = "-";
            sha256Box.textContent = "-";
            sha512Box.textContent = "-";
            console.info("开始计算文本哈希", {
                length: value.length
            });

            try {
                const response = await fetch("/api/hash", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        value: value
                    })
                });

                const data = await response.json();

                if (!data.success) {
                    messageBox.textContent = data.message || "计算失败";
                    return;
                }

                lengthBox.textContent = data.length;
                md5Box.textContent = data.md5;
                sha1Box.textContent = data.sha1;
                sha256Box.textContent = data.sha256;
                sha512Box.textContent = data.sha512;
                messageBox.textContent = "计算完成";
                console.info("文本哈希计算完成", {
                    length: data.length
                });
            } catch (error) {
                messageBox.textContent = "请求失败，请检查后端服务是否正常运行";
                console.error("文本哈希请求失败", error);
            }
        });
    });
});

// 随机数
document.addEventListener("DOMContentLoaded", function () {
    const randomButtons = document.querySelectorAll(".random-generate-btn");

    function generateRandomNumber(toolId) {
        const minInput = document.getElementById(`${toolId}-min`);
        const maxInput = document.getElementById(`${toolId}-max`);
        const resultInput = document.getElementById(`${toolId}-result`);

        if (!minInput || !maxInput || !resultInput) {
            return;
        }

        let min = parseInt(minInput.value, 10);
        let max = parseInt(maxInput.value, 10);

        if (Number.isNaN(min)) {
            min = 1;
            minInput.value = 1;
        }

        if (Number.isNaN(max)) {
            max = 100;
            maxInput.value = 100;
        }

        if (min > max) {
            const temp = min;
            min = max;
            max = temp;

            minInput.value = min;
            maxInput.value = max;
        }

        const randomNumber = Math.floor(Math.random() * (max - min + 1)) + min;
        resultInput.value = randomNumber;
    }

    randomButtons.forEach(function (button) {
        button.addEventListener("click", function () {
            generateRandomNumber(button.dataset.toolId);
        });
    });
});

// 接受后端的哈希值，在通过js放在页面
document.addEventListener("DOMContentLoaded", function () {
    const fileHashForms = document.querySelectorAll(".file-hash-form");

    fileHashForms.forEach(function (form) {
        form.addEventListener("submit", async function (event) {
            event.preventDefault();

            const card = form.closest(".card");
            const fileInput = form.querySelector('input[name="file"]');

            const filenameBox = card.querySelector(".hash-filename");
            const sizeBox = card.querySelector(".hash-size");
            const md5Box = card.querySelector(".hash-md5");
            const sha1Box = card.querySelector(".hash-sha1");
            const sha256Box = card.querySelector(".hash-sha256");
            const sha512Box = card.querySelector(".hash-sha512");
            const messageBox = card.querySelector(".hash-message");

            if (!fileInput.files || fileInput.files.length === 0) {
                messageBox.textContent = "请先选择文件";
                return;
            }

            const formData = new FormData();
            formData.append("file", fileInput.files[0]);

            messageBox.textContent = "正在计算...";
            md5Box.textContent = "-";
            sha1Box.textContent = "-";
            sha256Box.textContent = "-";
            sha512Box.textContent = "-";
            console.info("开始计算文件哈希", {
                filename: fileInput.files[0].name,
                size: fileInput.files[0].size
            });

            try {
                const response = await fetch("/api/file_hash", {
                    method: "POST",
                    body: formData
                });

                const data = await response.json();

                if (!data.success) {
                    messageBox.textContent = data.message || "计算失败";
                    return;
                }

                filenameBox.textContent = data.filename;
                sizeBox.textContent = data.size + " 字节";
                md5Box.textContent = data.md5;
                sha1Box.textContent = data.sha1;
                sha256Box.textContent = data.sha256;
                sha512Box.textContent = data.sha512;
                messageBox.textContent = "计算完成";
                console.info("文件哈希计算完成", {
                    filename: data.filename,
                    size: data.size
                });
            } catch (error) {
                messageBox.textContent = "请求失败，请检查后端服务是否正常运行";
                console.error("文件哈希请求失败", error);
            }
        });
    });
});

// Base64 编码/解码
document.addEventListener("DOMContentLoaded", function () {
    const base64Forms = document.querySelectorAll(".base64-form");

    function encodeBase64(value) {
        const bytes = new TextEncoder().encode(value);
        let binary = "";

        bytes.forEach(function (byte) {
            binary += String.fromCharCode(byte);
        });

        return window.btoa(binary);
    }

    function decodeBase64(value) {
        const normalizedValue = value.replace(/\s+/g, "");
        const binary = window.atob(normalizedValue);
        const bytes = Uint8Array.from(binary, function (char) {
            return char.charCodeAt(0);
        });

        return new TextDecoder().decode(bytes);
    }

    function setMessage(messageBox, message, isError) {
        messageBox.textContent = message;
        messageBox.classList.toggle("error", Boolean(isError));
    }

    base64Forms.forEach(function (form) {
        const input = form.querySelector(".base64-input");
        const output = form.querySelector(".base64-output");
        const encodeButton = form.querySelector(".base64-encode-btn");
        const decodeButton = form.querySelector(".base64-decode-btn");
        const clearButton = form.querySelector(".base64-clear-btn");
        const copyButton = form.querySelector(".base64-copy-btn");
        const messageBox = form.querySelector(".base64-message");

        encodeButton.addEventListener("click", function () {
            const value = input.value;

            if (value === "") {
                setMessage(messageBox, "请输入需要编码的内容", true);
                return;
            }

            output.value = encodeBase64(value);
            setMessage(messageBox, "编码完成", false);
        });

        decodeButton.addEventListener("click", function () {
            const value = input.value;

            if (value.trim() === "") {
                setMessage(messageBox, "请输入需要解码的 Base64 内容", true);
                return;
            }

            try {
                output.value = decodeBase64(value);
                setMessage(messageBox, "解码完成", false);
            } catch (error) {
                output.value = "";
                setMessage(messageBox, "解码失败，请检查 Base64 内容是否正确", true);
                console.error("Base64 解码失败", error);
            }
        });

        clearButton.addEventListener("click", function () {
            input.value = "";
            output.value = "";
            setMessage(messageBox, "已清空", false);
            input.focus();
        });

        copyButton.addEventListener("click", async function () {
            if (output.value === "") {
                setMessage(messageBox, "暂无可复制的结果", true);
                return;
            }

            try {
                await navigator.clipboard.writeText(output.value);
                setMessage(messageBox, "结果已复制", false);
            } catch (error) {
                output.select();
                document.execCommand("copy");
                setMessage(messageBox, "结果已复制", false);
            }
        });
    });
});
