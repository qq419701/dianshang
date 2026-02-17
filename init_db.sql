-- ==============================================
--  数据库初始化脚本
--  功能：创建数据库和所有业务表
--  使用方式：mysql -u root -p < init_db.sql
-- ==============================================

-- 创建数据库（如不存在）
CREATE DATABASE IF NOT EXISTS `dianshang` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE `dianshang`;

-- ==============================================
--  商户京东配置表
--  存储商户的京东通用交易和游戏点卡平台配置
-- ==============================================
CREATE TABLE IF NOT EXISTS `merchant_jd_config` (
    `id`                      BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    `merchant_id`             BIGINT NOT NULL COMMENT '商户ID',
    `biz_type`                TINYINT NOT NULL COMMENT '业务类型：1=通用交易, 2=游戏点卡',
    `vendor_id`               BIGINT COMMENT '京东vendorId（通用交易）',
    `customer_id`             BIGINT COMMENT '京东customerId（游戏点卡）',
    `md5_secret`              VARCHAR(255) COMMENT 'MD5签名密钥（AES加密存储）',
    `aes_secret`              VARCHAR(255) COMMENT 'AES加密密钥（AES加密存储）',
    `our_api_url`             VARCHAR(500) COMMENT '我方接口基础地址',
    `jd_callback_url`         VARCHAR(500) COMMENT '京东回调地址',
    `jd_direct_callback_url`  VARCHAR(500) COMMENT '京东直充回调地址',
    `jd_card_callback_url`    VARCHAR(500) COMMENT '京东卡密回调地址',
    `is_enabled`              TINYINT DEFAULT 1 COMMENT '启用开关：0=禁用, 1=启用',
    `create_time`             DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`             DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY `uk_merchant_biz` (`merchant_id`, `biz_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商户京东配置表';

-- ==============================================
--  阿奇索开放平台配置表
--  可选模块 — 按商户独立配置
-- ==============================================
CREATE TABLE IF NOT EXISTS `agiso_config` (
    `id`                    BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    `merchant_id`           BIGINT NOT NULL UNIQUE COMMENT '商户ID',
    `host`                  VARCHAR(255) COMMENT '阿奇索API网关地址',
    `port`                  INT COMMENT '端口',
    `app_id`                VARCHAR(128) COMMENT '应用ID',
    `app_secret`            VARCHAR(255) COMMENT '应用密钥（AES加密存储）',
    `access_token`          VARCHAR(500) COMMENT '授权令牌（AES加密存储）',
    `general_trade_route`   VARCHAR(255) COMMENT '通用交易路由',
    `game_card_route`       VARCHAR(255) COMMENT '点卡路由',
    `is_enabled`            TINYINT DEFAULT 0 COMMENT '启用开关：0=禁用, 1=启用',
    `create_time`           DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`           DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='阿奇索开放平台配置表';

-- ==============================================
--  订单主表
--  存储所有来自京东平台的订单（通用交易 + 游戏点卡）
-- ==============================================
CREATE TABLE IF NOT EXISTS `orders` (
    `id`              BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    `merchant_id`     BIGINT NOT NULL COMMENT '商户ID',
    `biz_type`        TINYINT NOT NULL COMMENT '业务类型：1=通用交易, 2=游戏点卡',
    `order_no`        VARCHAR(64) NOT NULL COMMENT '我方订单号',
    `jd_order_no`     VARCHAR(64) NOT NULL COMMENT '京东订单号',
    `order_status`    TINYINT NOT NULL COMMENT '订单状态：0=成功, 1=充值中, 2=失败, 3=生产中, 4=异常',
    `operation_mode`  TINYINT DEFAULT 0 COMMENT '操作方式：0=自动, 1=手动',
    `amount`          BIGINT COMMENT '订单金额（单位：分）',
    `quantity`        INT COMMENT '数量',
    `sku_id`          VARCHAR(64) COMMENT '商品SKU',
    `ware_no`         VARCHAR(64) COMMENT '商品编码',
    `produce_account` VARCHAR(255) COMMENT '充值账号',
    `product_info`    TEXT COMMENT '卡密信息（AES加密存储）',
    `notify_url`      VARCHAR(500) COMMENT '回调地址',
    `pay_time`        DATETIME COMMENT '支付时间',
    `remark`          VARCHAR(500) COMMENT '备注',
    `create_time`     DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`     DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY `uk_jd_order_biz` (`jd_order_no`, `biz_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单主表';

-- ==============================================
--  京东回调记录表
--  记录所有与京东之间的回调交互
-- ==============================================
CREATE TABLE IF NOT EXISTS `jd_callbacks` (
    `id`                  BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    `order_id`            BIGINT NOT NULL COMMENT '订单ID',
    `callback_type`       TINYINT NOT NULL COMMENT '回调类型：1=通用交易回调, 2=直充回调, 3=卡密回调',
    `callback_direction`  TINYINT COMMENT '回调方向：1=京东调我方, 2=我方调京东',
    `request_params`      TEXT COMMENT '请求参数（脱敏后存储）',
    `response_data`       TEXT COMMENT '响应数据（脱敏后存储）',
    `result_code`         VARCHAR(32) COMMENT '结果码',
    `result_message`      VARCHAR(500) COMMENT '结果信息',
    `retry_count`         INT DEFAULT 0 COMMENT '重试次数',
    `create_time`         DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='京东回调记录表';

-- ==============================================
--  阿奇索调用日志表
--  记录与阿奇索平台之间所有API调用的日志
-- ==============================================
CREATE TABLE IF NOT EXISTS `agiso_logs` (
    `id`              BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    `merchant_id`     BIGINT NOT NULL COMMENT '商户ID',
    `api_name`        VARCHAR(128) COMMENT '接口名称',
    `request_data`    TEXT COMMENT '请求数据（脱敏后存储）',
    `response_data`   TEXT COMMENT '响应数据（脱敏后存储）',
    `result_code`     VARCHAR(32) COMMENT '结果码',
    `result_message`  VARCHAR(500) COMMENT '结果信息',
    `create_time`     DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='阿奇索调用日志表';
