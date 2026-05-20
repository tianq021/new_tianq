document.addEventListener('DOMContentLoaded', function () {
    const menuItems = document.querySelectorAll('.menu-item');
    const sections = document.querySelectorAll('.content-section');

    function showSection(targetId) {
        sections.forEach(function (section) {
            section.classList.remove('active');
        });

        menuItems.forEach(function (item) {
            item.classList.remove('active');
        });

        const targetSection = document.getElementById(targetId);
        const targetMenu = document.querySelector(`.menu-item[data-target="${targetId}"]`);

        if (targetSection) {
            targetSection.classList.add('active');
        }

        if (targetMenu) {
            targetMenu.classList.add('active');
        }
    }

    menuItems.forEach(function (item) {
        item.addEventListener('click', function (event) {
            event.preventDefault();

            const targetId = item.dataset.target;

            if (!targetId) {
                return;
            }

            showSection(targetId);

            history.replaceState(null, '', `#${targetId}`);
        });
    });

    const defaultTarget = location.hash ? location.hash.replace('#', '') : 'fastgpt-page';
    showSection(defaultTarget);
});