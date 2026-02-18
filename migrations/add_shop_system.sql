-- ==============================================
--  店铺管理系统数据库变更脚本
--  功能：新增店铺表、修改订单表、完善通知配置表
--  使用方式：mysql -u root -p dianshang < add_shop_system.sql
-- ==============================================

USE `dianshang`;

-- ==============================================
--  1. 新增店铺表 (shops)
-- ==============================================
CREATE TABLE IF NOT EXISTS `shops` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '店铺ID',
  `merchant_id` BIGINT NOT NULL COMMENT '所属商户ID',
  `shop_name` VARCHAR(128) NOT NULL COMMENT '店铺名称',
  `shop_code` VARCHAR(64) COMMENT '店铺编码（自定义标识）',
  `biz_type` TINYINT NOT NULL COMMENT '业务类型：1=京东通用交易, 2=京东游戏点卡',
  
  -- 京东通用交易字段
  `vendor_id` BIGINT COMMENT '京东vendorId',
  
  -- 京东游戏点卡字段  
  `customer_id` BIGINT COMMENT '京东customerId',
  
  -- 公共配置字段
  `md5_secret` VARCHAR(255) COMMENT 'MD5签名密钥（AES加密）',
  `aes_secret` VARCHAR(255) COMMENT 'AES加密密钥（AES加密）',
  `our_api_url` VARCHAR(500) COMMENT '我方接口基础地址',
  `jd_callback_url` VARCHAR(500) COMMENT '京东回调地址',
  `jd_direct_callback_url` VARCHAR(500) COMMENT '京东直充回调地址',
  `jd_card_callback_url` VARCHAR(500) COMMENT '京东卡密回调地址',
  
  `is_enabled` TINYINT DEFAULT 1 COMMENT '启用状态：0=禁用, 1=启用',
  `remark` TEXT COMMENT '备注',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  UNIQUE KEY `uk_merchant_shop_code` (`merchant_id`, `shop_code`),
  INDEX `idx_merchant_id` (`merchant_id`),
  INDEX `idx_biz_type` (`biz_type`),
  FOREIGN KEY (`merchant_id`) REFERENCES `merchants`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='店铺配置表';

-- ==============================================
--  2. 修改订单表 - 添加店铺ID
-- ==============================================
ALTER TABLE `orders` 
ADD COLUMN `shop_id` BIGINT COMMENT '店铺ID' AFTER `merchant_id`,
ADD INDEX `idx_shop_id` (`shop_id`);

-- ==============================================
--  3. 完善通知配置表
-- ==============================================
ALTER TABLE `notification_configs` 
ADD COLUMN `notify_type` TINYINT COMMENT '通知类型：1=钉钉, 2=企业微信, 3=飞书' AFTER `merchant_id`,
ADD COLUMN `secret` VARCHAR(255) COMMENT '加签密钥（钉钉）' AFTER `webhook_url`,
ADD COLUMN `at_mobiles` JSON COMMENT '@ 的手机号列表' AFTER `secret`,
ADD COLUMN `trigger_events` JSON COMMENT '触发事件：["order_create", "order_success", "order_fail"]' AFTER `at_mobiles`,
ADD COLUMN `is_enabled` TINYINT DEFAULT 1 COMMENT '启用状态：0=禁用, 1=启用' AFTER `trigger_events`;

-- ==============================================
--  4. 更新说明
-- ==============================================
-- 执行完成后：
-- 1. 使用 scripts/migrate_to_shops.py 迁移历史数据
-- 2. 验证店铺和订单关联关系
-- 3. merchant_jd_config 表保留向后兼容，但标记为 deprecated
