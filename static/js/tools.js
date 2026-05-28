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

        targetPanel.scrollIntoView({
            behavior: "smooth",
            block: "start"
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

        window.location.hash = targetId;
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

            window.location.hash = targetId;
            showPanel(targetId, {
                scroll: true
            });
        });
    });

    const activeItem = document.querySelector(".tool-menu-item.active");

    if (showPanelFromHash()) {
        return;
    } else if (activeItem) {
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
function generateRandomNumber(toolId) {
    const minInput = document.getElementById(`${toolId}-min`);
    const maxInput = document.getElementById(`${toolId}-max`);
    const resultInput = document.getElementById(`${toolId}-result`);

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
