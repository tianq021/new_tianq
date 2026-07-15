CREATE TABLE IF NOT EXISTS app_users (
    id BIGINT NOT NULL AUTO_INCREMENT,
    username VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,
    display_name VARCHAR(100) NOT NULL DEFAULT '',
    enabled TINYINT(1) NOT NULL DEFAULT 1,
    last_login_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_app_users_username (username),
    INDEX idx_app_users_role_enabled (role, enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS user_ai_favorites (
    id BIGINT NOT NULL AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    tool_id BIGINT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_user_ai_favorites_user_tool (user_id, tool_id),
    INDEX idx_user_ai_favorites_user_created (user_id, created_at),
    CONSTRAINT fk_user_ai_favorites_user
        FOREIGN KEY (user_id) REFERENCES app_users(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_user_ai_favorites_tool
        FOREIGN KEY (tool_id) REFERENCES ai_tools(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS user_ai_chat_histories (
    id BIGINT NOT NULL AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    tool_id BIGINT NOT NULL,
    history_json JSON NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_user_ai_chat_histories_user_tool (user_id, tool_id),
    INDEX idx_user_ai_chat_histories_user_updated (user_id, updated_at),
    CONSTRAINT fk_user_ai_chat_histories_user
        FOREIGN KEY (user_id) REFERENCES app_users(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_user_ai_chat_histories_tool
        FOREIGN KEY (tool_id) REFERENCES ai_tools(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS user_ai_remote_chats (
    id BIGINT NOT NULL AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    profile_key VARCHAR(100) NOT NULL,
    remote_chat_id VARCHAR(250) NOT NULL,
    title VARCHAR(100) NOT NULL DEFAULT '新对话',
    messages_json JSON NULL,
    is_current TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_user_ai_remote_chats_user_profile_remote (user_id, profile_key, remote_chat_id),
    INDEX idx_user_ai_remote_chats_user_updated (user_id, updated_at),
    INDEX idx_user_ai_remote_chats_current (user_id, profile_key, is_current, updated_at),
    CONSTRAINT fk_user_ai_remote_chats_user
        FOREIGN KEY (user_id) REFERENCES app_users(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS user_feedback (
    id BIGINT NOT NULL AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_user_feedback_created (created_at, id),
    INDEX idx_user_feedback_user (user_id, created_at),
    CONSTRAINT fk_user_feedback_user
        FOREIGN KEY (user_id) REFERENCES app_users(id)
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
