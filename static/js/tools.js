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