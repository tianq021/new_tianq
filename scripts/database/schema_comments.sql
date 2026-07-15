CREATE TABLE IF NOT EXISTS comments (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    page_key VARCHAR(100) NOT NULL,
    nickname VARCHAR(30) NOT NULL,
    content TEXT NOT NULL,
    like_count INT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_comments_page_created (page_key, created_at, id),
    INDEX idx_comments_page_hot (page_key, like_count, created_at, id)
);

CREATE TABLE IF NOT EXISTS comment_likes (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    comment_id BIGINT NOT NULL,
    visitor_key VARCHAR(128) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_comment_likes_comment_visitor (comment_id, visitor_key),
    INDEX idx_comment_likes_comment_id (comment_id),
    CONSTRAINT fk_comment_likes_comment
        FOREIGN KEY (comment_id) REFERENCES comments(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS comment_replies (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    comment_id BIGINT NOT NULL,
    nickname VARCHAR(30) NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_comment_replies_comment_created (comment_id, created_at, id),
    CONSTRAINT fk_comment_replies_comment
        FOREIGN KEY (comment_id) REFERENCES comments(id)
        ON DELETE CASCADE
);
