CREATE TABLE IF NOT EXISTS ai_tools (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    tool_key VARCHAR(100) NOT NULL UNIQUE,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    page_intro TEXT,
    source VARCHAR(30) NOT NULL DEFAULT 'local',
    type VARCHAR(50) NOT NULL DEFAULT 'link',
    category VARCHAR(50) DEFAULT '',
    url TEXT,
    icon VARCHAR(100) DEFAULT '',
    enabled TINYINT(1) NOT NULL DEFAULT 1,
    is_default TINYINT(1) NOT NULL DEFAULT 0,
    sort_order INT NOT NULL DEFAULT 100,
    config_json JSON NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_ai_tools_source_enabled (source, enabled),
    INDEX idx_ai_tools_category (category),
    INDEX idx_ai_tools_sort (sort_order)
);

CREATE TABLE IF NOT EXISTS ai_tool_keywords (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    tool_id BIGINT NOT NULL,
    keyword VARCHAR(100) NOT NULL,
    weight INT NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_ai_tool_keyword (tool_id, keyword),
    INDEX idx_ai_tool_keywords_keyword (keyword),
    CONSTRAINT fk_ai_tool_keywords_tool
        FOREIGN KEY (tool_id) REFERENCES ai_tools(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ai_chat_profiles (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    profile_key VARCHAR(100) NOT NULL UNIQUE,
    tool_key VARCHAR(100) DEFAULT NULL,
    name VARCHAR(100) NOT NULL,
    mode VARCHAR(30) NOT NULL DEFAULT 'chat',
    api_key TEXT NULL,
    api_key_env VARCHAR(100) DEFAULT NULL,
    chat_id VARCHAR(100) NOT NULL,
    system_prompt TEXT,
    tool_source VARCHAR(30) DEFAULT NULL,
    require_json TINYINT(1) NOT NULL DEFAULT 0,
    enabled TINYINT(1) NOT NULL DEFAULT 1,
    config_json JSON NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_ai_chat_profiles_tool_key (tool_key),
    INDEX idx_ai_chat_profiles_mode_enabled (mode, enabled),
    INDEX idx_ai_chat_profiles_tool_source (tool_source)
);

CREATE TABLE IF NOT EXISTS api_endpoint_meta (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    endpoint VARCHAR(150) NOT NULL UNIQUE,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS feature_explanations (
    page_key VARCHAR(100) NOT NULL,
    title VARCHAR(200) NOT NULL DEFAULT '功能解释',
    content TEXT NOT NULL,
    enabled TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (page_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
