document.addEventListener("DOMContentLoaded", function () {
    const menuItems = document.querySelectorAll(".tool-menu-item");
    const panels = document.querySelectorAll(".tool-panel");

    function showPanel(targetId) {
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
        }
    }

    menuItems.forEach(function (item) {
        item.addEventListener("click", function () {
            const targetId = item.dataset.target;

            if (!targetId) {
                return;
            }

            showPanel(targetId);
        });
    });

    const activeItem = document.querySelector(".tool-menu-item.active");

    if (activeItem) {
        showPanel(activeItem.dataset.target);
    } else if (menuItems.length > 0) {
        showPanel(menuItems[0].dataset.target);
    }
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
            md5Box.value = "";
            sha1Box.value = "";
            sha256Box.value = "";
            sha512Box.value = "";

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
                md5Box.value = data.md5;
                sha1Box.value = data.sha1;
                sha256Box.value = data.sha256;
                sha512Box.value = data.sha512;
                messageBox.textContent = "计算完成";
            } catch (error) {
                messageBox.textContent = "请求失败，请检查后端服务是否正常运行";
            }
        });
    });
});