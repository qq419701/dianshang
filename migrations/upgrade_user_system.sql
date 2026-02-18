-- ==============================================
--  数据库升级脚本 - 用户认证系统
--  功能：添加用户、角色、商户、通知、操作日志相关表
--  使用方式：mysql -u root -p dianshang < migrations/upgrade_user_system.sql
-- ==============================================

USE `dianshang`;

-- ==============================================
--  商户表
-- ==============================================
CREATE TABLE IF NOT EXISTS `merchants` (
    `id`              BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    `name`            VARCHAR(128) NOT NULL COMMENT '商户名称',
    `code`            VARCHAR(64) UNIQUE COMMENT '商户代码',
    `contact_name`    VARCHAR(128) COMMENT '联系人姓名',
    `contact_mobile`  VARCHAR(32) COMMENT '联系人手机',
    `contact_email`   VARCHAR(128) COMMENT '联系人邮箱',
    `status`          SMALLINT DEFAULT 1 COMMENT '状态：0=禁用, 1=启用',
    `remark`          TEXT COMMENT '备注',
    `create_time`     DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`     DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商户表';

-- ==============================================
--  角色表
-- ==============================================
CREATE TABLE IF NOT EXISTS `roles` (
    `id`          BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    `name`        VARCHAR(64) NOT NULL UNIQUE COMMENT '角色名称',
    `code`        VARCHAR(64) NOT NULL UNIQUE COMMENT '角色代码',
    `description` VARCHAR(255) COMMENT '角色描述',
    `permissions` TEXT COMMENT '权限列表（JSON格式）',
    `status`      SMALLINT DEFAULT 1 COMMENT '状态：0=禁用, 1=启用',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色表';

-- ==============================================
--  用户表
-- ==============================================
CREATE TABLE IF NOT EXISTS `users` (
    `id`                BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    `username`          VARCHAR(64) NOT NULL UNIQUE COMMENT '用户名',
    `password_hash`     VARCHAR(255) NOT NULL COMMENT '密码哈希',
    `real_name`         VARCHAR(128) COMMENT '真实姓名',
    `email`             VARCHAR(128) COMMENT '邮箱',
    `mobile`            VARCHAR(32) COMMENT '手机号',
    `role_id`           BIGINT COMMENT '角色ID',
    `merchant_id`       BIGINT COMMENT '商户ID',
    `status`            SMALLINT DEFAULT 1 COMMENT '状态：0=禁用, 1=启用',
    `last_login_time`   DATETIME COMMENT '最后登录时间',
    `last_login_ip`     VARCHAR(64) COMMENT '最后登录IP',
    `create_time`       DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`       DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (`role_id`) REFERENCES `roles`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`merchant_id`) REFERENCES `merchants`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- ==============================================
--  站内消息表
-- ==============================================
CREATE TABLE IF NOT EXISTS `notifications` (
    `id`            BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    `user_id`       BIGINT COMMENT '用户ID',
    `title`         VARCHAR(255) NOT NULL COMMENT '消息标题',
    `content`       TEXT COMMENT '消息内容',
    `type`          SMALLINT COMMENT '消息类型：1=系统, 2=订单, 3=配置, 4=警告',
    `related_type`  VARCHAR(32) COMMENT '关联类型',
    `related_id`    BIGINT COMMENT '关联ID',
    `is_read`       SMALLINT DEFAULT 0 COMMENT '已读状态：0=未读, 1=已读',
    `read_time`     DATETIME COMMENT '阅读时间',
    `create_time`   DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    INDEX `idx_user_read` (`user_id`, `is_read`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='站内消息表';

-- ==============================================
--  通知配置表
-- ==============================================
CREATE TABLE IF NOT EXISTS `notification_configs` (
    `id`              BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    `merchant_id`     BIGINT COMMENT '商户ID',
    `scene`           VARCHAR(64) NOT NULL COMMENT '通知场景',
    `enable_email`    SMALLINT DEFAULT 0 COMMENT '启用邮件：0=禁用, 1=启用',
    `email_to`        VARCHAR(512) COMMENT '邮件接收人（多个用逗号分隔）',
    `enable_webhook`  SMALLINT DEFAULT 0 COMMENT '启用Webhook：0=禁用, 1=启用',
    `webhook_url`     VARCHAR(512) COMMENT 'Webhook地址',
    `enable_site_msg` SMALLINT DEFAULT 1 COMMENT '启用站内信：0=禁用, 1=启用',
    `create_time`     DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`     DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY `uk_merchant_scene` (`merchant_id`, `scene`),
    FOREIGN KEY (`merchant_id`) REFERENCES `merchants`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='通知配置表';

-- ==============================================
--  通知日志表
-- ==============================================
CREATE TABLE IF NOT EXISTS `notification_logs` (
    `id`            BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    `merchant_id`   BIGINT COMMENT '商户ID',
    `scene`         VARCHAR(64) COMMENT '通知场景',
    `channel`       VARCHAR(32) COMMENT '发送渠道：email/webhook/site_msg',
    `to_address`    VARCHAR(512) COMMENT '接收地址',
    `title`         VARCHAR(255) COMMENT '标题',
    `content`       TEXT COMMENT '内容',
    `status`        SMALLINT COMMENT '状态：0=失败, 1=成功',
    `error_message` TEXT COMMENT '错误信息',
    `create_time`   DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX `idx_merchant_scene` (`merchant_id`, `scene`),
    INDEX `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='通知日志表';

-- ==============================================
--  操作日志表
-- ==============================================
CREATE TABLE IF NOT EXISTS `operation_logs` (
    `id`             BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    `user_id`        BIGINT COMMENT '用户ID',
    `username`       VARCHAR(64) COMMENT '用户名',
    `operation`      VARCHAR(128) COMMENT '操作名称',
    `module`         VARCHAR(64) COMMENT '操作模块',
    `method`         VARCHAR(16) COMMENT '请求方法',
    `path`           VARCHAR(255) COMMENT '请求路径',
    `ip_address`     VARCHAR(64) COMMENT 'IP地址',
    `user_agent`     VARCHAR(512) COMMENT 'User-Agent',
    `request_data`   TEXT COMMENT '请求数据',
    `response_data`  TEXT COMMENT '响应数据',
    `status`         SMALLINT COMMENT '状态：0=失败, 1=成功',
    `error_message`  TEXT COMMENT '错误信息',
    `create_time`    DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE SET NULL,
    INDEX `idx_user_id` (`user_id`),
    INDEX `idx_module` (`module`),
    INDEX `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='操作日志表';

-- ==============================================
--  添加外键约束到现有表
-- ==============================================

-- 为 merchant_jd_config 表添加外键（如果不存在）
SET @exist := (SELECT COUNT(*) FROM information_schema.KEY_COLUMN_USAGE 
               WHERE TABLE_SCHEMA = 'dianshang' 
               AND TABLE_NAME = 'merchant_jd_config' 
               AND CONSTRAINT_NAME = 'fk_merchant_jd_config_merchant');

SET @sqlstmt := IF(@exist > 0, 
    'SELECT "外键已存在，跳过" AS msg',
    'ALTER TABLE `merchant_jd_config` ADD CONSTRAINT `fk_merchant_jd_config_merchant` 
     FOREIGN KEY (`merchant_id`) REFERENCES `merchants`(`id`) ON DELETE CASCADE'
);

PREPARE stmt FROM @sqlstmt;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ==============================================
--  插入初始数据
-- ==============================================

-- 插入默认商户
INSERT IGNORE INTO `merchants` (`id`, `name`, `code`, `status`) 
VALUES (1, '默认商户', 'default', 1);

-- 插入默认角色
INSERT IGNORE INTO `roles` (`id`, `name`, `code`, `description`, `permissions`, `status`) VALUES
(1, '超级管理员', 'super_admin', '拥有所有权限', '["*:*"]', 1),
(2, '管理员', 'admin', '商户管理、订单管理、配置管理', '["merchant:*", "order:*", "config:*", "user:view"]', 1),
(3, '操作员', 'operator', '订单查看和处理', '["order:view", "order:update"]', 1),
(4, '查看者', 'viewer', '只读权限', '["order:view", "config:view"]', 1);

-- 注意：默认管理员账号需要在Python中创建，因为密码需要加密
-- 执行方式：python3 scripts/create_admin.py

-- ==============================================
--  完成提示
-- ==============================================
SELECT '数据库升级完成！' AS 'Status';
SELECT '请执行 Python 脚本创建管理员账号：python3 scripts/create_admin.py' AS 'Next Step';
