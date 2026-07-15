document.addEventListener("DOMContentLoaded", function () {
    const commentForm = document.getElementById("commentForm");
    const commentContent = document.getElementById("commentContent");
    const commentMessage = document.getElementById("commentMessage");
    const commentList = document.getElementById("commentList");
    const commentSort = document.getElementById("commentSort");
    const commentPrev = document.getElementById("commentPrev");
    const commentNext = document.getElementById("commentNext");
    const commentPageInfo = document.getElementById("commentPageInfo");

    if (!commentForm || !commentList) {
        return;
    }

    const PAGE_KEY = commentForm.dataset.pageKey || "tools";
    const PAGE_SIZE = Number(commentForm.dataset.pageSize || 10);
    const shouldAutoload = commentForm.dataset.autoload === "true";

    let currentPage = 1;
    let currentSort = "time";
    let totalPages = 1;
    let hasLoadedComments = false;
    let realtimeReloadTimer = null;
    const clientId = (
        window.crypto && typeof window.crypto.randomUUID === "function"
            ? window.crypto.randomUUID()
            : `${Date.now()}-${Math.random().toString(16).slice(2)}`
    );

    async function loadComments() {
        commentList.innerHTML = `<p class="comment-empty">正在加载评论...</p>`;
        console.info("开始加载评论", {
            page: currentPage,
            sort: currentSort
        });

        try {
            const url =
                `/api/comments?page_key=${PAGE_KEY}` +
                `&page=${currentPage}` +
                `&page_size=${PAGE_SIZE}` +
                `&sort=${currentSort}`;

            const response = await fetch(url);
            const data = await response.json();

            if (!data.success) {
                commentList.innerHTML = `<p class="comment-empty">评论加载失败</p>`;
                return;
            }

            totalPages = data.total_pages || 1;
            renderComments(data.comments || []);
            renderPagination(data.page || 1, totalPages, data.total || 0);
            hasLoadedComments = true;
            console.info("评论加载完成", {
                page: data.page || 1,
                total: data.total || 0
            });
        } catch (error) {
            commentList.innerHTML = `<p class="comment-empty">评论加载失败，请检查后端服务</p>`;
            console.error("评论加载失败", error);
        }
    }

    function renderComments(comments) {
    commentList.innerHTML = "";

    if (comments.length === 0) {
        commentList.innerHTML = `<p class="comment-empty">暂无评论，来写第一条吧。</p>`;
        return;
    }

    comments.forEach(function (comment) {
        const detailUrl = buildCommentDetailUrl(comment.id);
        const item = document.createElement("div");
        item.className = "comment-item comment-item-clickable";
        item.tabIndex = 0;
        item.setAttribute("role", "link");
        item.setAttribute("aria-label", "进入评论");
        item.addEventListener("click", function () {
            window.location.href = detailUrl;
        });
        item.addEventListener("keydown", function (event) {
            if (event.key === "Enter") {
                window.location.href = detailUrl;
            }
        });

        const header = document.createElement("div");
        header.className = "comment-item-header";

        const userBox = document.createElement("div");
        userBox.className = "comment-user-box";

        const avatar = document.createElement("div");
        avatar.className = "comment-avatar";
        avatar.textContent = (comment.nickname || "匿").slice(0, 1);

        const nameTimeBox = document.createElement("div");

        const name = document.createElement("div");
        name.className = "comment-name";
        name.textContent = comment.nickname || "匿名用户";

        const time = document.createElement("div");
        time.className = "comment-time";
        time.textContent = `${comment.created_at || ""} · ID ${comment.id || ""}`;

        nameTimeBox.appendChild(name);
        nameTimeBox.appendChild(time);

        userBox.appendChild(avatar);
        userBox.appendChild(nameTimeBox);

        const likeBtn = document.createElement("button");
        likeBtn.type = "button";
        likeBtn.className = "comment-like-btn";
        likeBtn.textContent = `👍 ${comment.like_count || 0}`;
        likeBtn.dataset.oldText = likeBtn.textContent;

        likeBtn.addEventListener("click", function (event) {
            event.stopPropagation();
            likeComment(comment.id, likeBtn);
        });

        header.appendChild(userBox);
        header.appendChild(likeBtn);

        const content = document.createElement("div");
        content.className = "comment-content comment-content-preview";
        content.textContent = comment.content || "";

        item.appendChild(header);
        item.appendChild(content);

        commentList.appendChild(item);
    });
}

    function buildCommentDetailUrl(commentId) {
        const from = window.location.pathname === "/tools" ? "tools" : "user";
        return `/comments/${commentId}?page_key=${encodeURIComponent(PAGE_KEY)}&from=${from}`;
    }

    function renderPagination(page, pages, total) {
        currentPage = page;
        totalPages = Math.max(pages, 1);

        commentPageInfo.textContent = `第 ${currentPage} 页 / 共 ${totalPages} 页，共 ${total} 条`;

        commentPrev.disabled = currentPage <= 1;
        commentNext.disabled = currentPage >= totalPages;
    }

    async function likeComment(commentId, likeBtn) {
    try {
        likeBtn.disabled = true;
        likeBtn.textContent = "处理中...";

        const response = await fetch(`/api/comments/${commentId}/like`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                page_key: PAGE_KEY,
                client_id: clientId
            })
        });

        const data = await response.json();

        if (!data.success) {
            commentMessage.textContent = data.message || "操作失败";
            likeBtn.disabled = false;
            likeBtn.textContent = likeBtn.dataset.oldText || "👍 0";
            return;
        }

        likeBtn.textContent = `👍 ${data.like_count}`;
        likeBtn.dataset.oldText = `👍 ${data.like_count}`;

        if (data.liked) {
            likeBtn.classList.add("liked");
        } else {
            likeBtn.classList.remove("liked");
        }

        commentMessage.textContent = data.message || "操作成功";
        likeBtn.disabled = false;

    } catch (error) {
        commentMessage.textContent = "操作失败，请检查后端服务";
        likeBtn.disabled = false;
        likeBtn.textContent = likeBtn.dataset.oldText || "👍 0";
    }
}

    commentForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const content = commentContent.value.trim();

        if (!content) {
            commentMessage.textContent = "评论内容不能为空";
            return;
        }

        commentMessage.textContent = "正在发布...";

        try {
            const response = await fetch("/api/comments", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    page_key: PAGE_KEY,
                    content: content,
                    client_id: clientId
                })
            });

            const data = await response.json();

            if (!data.success) {
                commentMessage.textContent = data.message || "发布失败";
                return;
            }

            commentContent.value = "";
            commentMessage.textContent = "发布成功";

            currentPage = 1;
            currentSort = "time";
            commentSort.value = "time";

            await loadComments();
        } catch (error) {
            commentMessage.textContent = "发布失败，请检查后端服务";
        }
    });

    commentSort.addEventListener("change", function () {
        currentSort = commentSort.value;
        currentPage = 1;
        loadComments();
    });

    commentPrev.addEventListener("click", function () {
        if (currentPage > 1) {
            currentPage -= 1;
            loadComments();
        }
    });

    commentNext.addEventListener("click", function () {
        if (currentPage < totalPages) {
            currentPage += 1;
            loadComments();
        }
    });

    document.addEventListener("toolPanelShown", function (event) {
        if (event.detail && event.detail.targetId === "comments-panel" && !hasLoadedComments) {
            loadComments();
        }
    });

    if (shouldAutoload) {
        loadComments();
    }

    if (typeof window.EventSource === "function") {
        const eventsUrl = `/api/comments/events?page_key=${encodeURIComponent(PAGE_KEY)}`;
        const eventSource = new EventSource(eventsUrl);

        eventSource.addEventListener("comment-update", function (event) {
            try {
                const update = JSON.parse(event.data);
                if (update.client_id === clientId || !hasLoadedComments) {
                    return;
                }

                window.clearTimeout(realtimeReloadTimer);
                realtimeReloadTimer = window.setTimeout(loadComments, 150);
            } catch (error) {
                console.error("评论实时消息解析失败", error);
            }
        });

        eventSource.addEventListener("error", function () {
            console.warn("评论实时连接暂时中断，浏览器将自动重连");
        });

        window.addEventListener("beforeunload", function () {
            eventSource.close();
        });
    }
});
