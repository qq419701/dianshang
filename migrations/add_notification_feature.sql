-- ==============================================
--  通知提醒功能数据库变更脚本
--  功能：店铺增加通知配置、订单增加通知记录、新增通知日志表
--  使用方式：mysql -u root -p dianshang < migrations/add_notification_feature.sql
-- ==============================================

USE `dianshang`;

-- ==============================================
--  1. 店铺表添加通知配置字段
-- ==============================================
ALTER TABLE `shops`
ADD COLUMN `notify_enabled` TINYINT DEFAULT 0 COMMENT '是否启用订单通知：0=否 1=是',
ADD COLUMN `dingtalk_webhook` VARCHAR(500) COMMENT '钉钉机器人Webhook地址',
ADD COLUMN `dingtalk_secret` VARCHAR(500) COMMENT '钉钉机器人加签密钥',
ADD COLUMN `wecom_webhook` VARCHAR(500) COMMENT '企业微信机器人Webhook地址';

-- ==============================================
--  2. 订单表添加通知记录字段
-- ==============================================
ALTER TABLE `orders`
ADD COLUMN `notified` TINYINT DEFAULT 0 COMMENT '是否已发送通知：0=否 1=是',
ADD COLUMN `notify_send_time` DATETIME COMMENT '通知发送时间';

-- ==============================================
--  3. 更新说明
-- ==============================================
-- 执行完成后：
-- 1. 店铺编辑页面新增通知配置区（钉钉/企业微信）
-- 2. 新订单创建时自动触发通知（根据店铺配置）
-- 3. 通知日志记录在 notification_logs 表中
