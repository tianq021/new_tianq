document.addEventListener("DOMContentLoaded", function () {
    const categoryItems = document.querySelectorAll(".category-menu-item");

    categoryItems.forEach(function (item) {
        item.addEventListener("click", function () {
            categoryItems.forEach(function (menuItem) {
                menuItem.classList.remove("active");
            });

            item.classList.add("active");
        });
    });

    document.querySelectorAll(".clickable-card").forEach(function (card) {
        function openCard() {
            const url = card.dataset.url;

            if (url) {
                window.open(url, "_blank", "noopener");
            }
        }

        card.addEventListener("click", function (event) {
            if (event.target.closest("a")) {
                return;
            }

            openCard();
        });

        card.addEventListener("keydown", function (event) {
            if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                openCard();
            }
        });
    });
});
