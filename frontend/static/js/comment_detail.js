document.addEventListener("DOMContentLoaded", function () {
    const detailCard = document.querySelector(".comment-detail-card[data-comment-id]");
    const likeBtn = document.getElementById("commentDetailLike");
    const message = document.getElementById("commentDetailMessage");
    const replyForm = document.getElementById("commentReplyForm");
    const replyContent = document.getElementById("commentReplyContent");
    const replyMessage = document.getElementById("commentReplyMessage");
    const replyList = document.getElementById("commentReplyList");
    const replySummary = document.getElementById("commentReplySummary");
    const replyCount = document.getElementById("commentReplyCount");

    if (!detailCard || !likeBtn) {
        return;
    }

    const commentId = detailCard.dataset.commentId;
    const pageKey = detailCard.dataset.pageKey || "tools";
    const clientId = (
        window.crypto && typeof window.crypto.randomUUID === "function"
            ? window.crypto.randomUUID()
            : `${Date.now()}-${Math.random().toString(16).slice(2)}`
    );

    likeBtn.addEventListener("click", async function () {
        try {
            likeBtn.disabled = true;
            likeBtn.textContent = "处理中...";

            const response = await fetch(`/api/comments/${commentId}/like`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    page_key: pageKey,
                    client_id: clientId
                })
            });

            const data = await response.json();

            if (!data.success) {
                message.textContent = data.message || "操作失败";
                likeBtn.textContent = likeBtn.dataset.oldText || "👍 0";
                likeBtn.disabled = false;
                return;
            }

            const nextText = `👍 ${data.like_count}`;
            likeBtn.textContent = nextText;
            likeBtn.dataset.oldText = nextText;
            likeBtn.classList.toggle("liked", Boolean(data.liked));
            message.textContent = data.message || "操作成功";
            likeBtn.disabled = false;
        } catch (error) {
            message.textContent = "操作失败，请检查后端服务";
            likeBtn.textContent = likeBtn.dataset.oldText || "👍 0";
            likeBtn.disabled = false;
        }
    });

    async function loadReplies() {
        if (!replyList) {
            return;
        }

        replyList.innerHTML = `<div class="comment-thread-empty">正在加载回复...</div>`;

        try {
            const response = await fetch(`/api/comments/${commentId}/replies`);
            const data = await response.json();

            if (!data.success) {
                replyList.innerHTML = `<div class="comment-thread-empty">${data.message || "回复加载失败"}</div>`;
                return;
            }

            renderReplies(data.replies || []);
        } catch (error) {
            replyList.innerHTML = `<div class="comment-thread-empty">回复加载失败，请检查后端服务</div>`;
        }
    }

    function renderReplies(replies) {
        const total = replies.length;
        replyCount.textContent = `${total} 条`;
        replySummary.textContent = total > 0 ? `共 ${total} 条回复` : "暂无回复";

        if (total === 0) {
            replyList.innerHTML = `<div class="comment-thread-empty">还没有回复。</div>`;
            return;
        }

        replyList.innerHTML = "";
        replies.forEach(function (reply, index) {
            const item = document.createElement("div");
            item.className = "comment-reply-item";

            const meta = document.createElement("div");
            meta.className = "comment-reply-meta";

            const author = document.createElement("strong");
            author.textContent = reply.nickname || "匿名用户";

            const floor = document.createElement("span");
            floor.textContent = `#${index + 1}`;

            const replyId = document.createElement("span");
            replyId.textContent = `ID ${reply.id || ""}`;

            const time = document.createElement("span");
            time.textContent = reply.created_at || "";

            meta.appendChild(author);
            meta.appendChild(floor);
            meta.appendChild(replyId);
            meta.appendChild(time);

            const content = document.createElement("div");
            content.className = "comment-reply-content";
            content.textContent = reply.content || "";

            item.appendChild(meta);
            item.appendChild(content);
            replyList.appendChild(item);
        });
    }

    if (replyForm) {
        replyForm.addEventListener("submit", async function (event) {
            event.preventDefault();

            const content = replyContent.value.trim();
            if (!content) {
                replyMessage.textContent = "回复内容不能为空";
                return;
            }

            replyMessage.textContent = "正在发布...";

            try {
                const response = await fetch(`/api/comments/${commentId}/replies`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        content: content
                    })
                });
                const data = await response.json();

                if (!data.success) {
                    replyMessage.textContent = data.message || "发布失败";
                    return;
                }

                replyContent.value = "";
                replyMessage.textContent = "回复成功";
                await loadReplies();
            } catch (error) {
                replyMessage.textContent = "发布失败，请检查后端服务";
            }
        });
    }

    loadReplies();
});
