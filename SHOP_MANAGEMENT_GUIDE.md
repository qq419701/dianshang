# 店铺管理系统实施指南

## 概述
本系统实现了完整的店铺管理功能，支持商户下多店铺运营、统计报表和通知增强。

## 部署步骤

### 1. 数据库迁移
```bash
# 执行数据库变更脚本
mysql -u root -p dianshang < migrations/add_shop_system.sql
```

### 2. 数据迁移
```bash
# 迁移现有配置数据到店铺表
cd /path/to/dianshang
python scripts/migrate_to_shops.py
```

### 3. 重启应用
```bash
# 重启Flask应用
systemctl restart dianshang
# 或使用gunicorn
pkill -f gunicorn && gunicorn -c gunicorn_config.py run:app
```

## 功能验证

### 1. 店铺管理
- 访问 `/merchant/` 查看商户列表
- 点击"查看店铺"进入商户详情页
- 测试新增、编辑、删除店铺功能

### 2. 统计报表
- 访问 `/statistics/` 查看统计报表
- 选择商户和日期范围
- 查看商户统计、店铺明细和图表

### 3. 订单筛选
- 访问 `/admin/orders` 查看订单列表
- 测试按商户、店铺筛选功能

### 4. 通知功能
- 在商户详情页配置钉钉/企业微信机器人
- 测试订单通知功能

## 权限说明

### 超级管理员
- 可以查看所有商户和店铺
- 可以创建、编辑、删除任何店铺
- 可以查看解密后的密钥信息

### 操作员（商户角色）
- 只能查看自己商户的店铺
- 只能管理自己商户的店铺
- 密钥信息显示为掩码

## API端点

### 店铺管理
- `GET /shop/list/<merchant_id>` - 获取店铺列表
- `GET /shop/detail/<shop_id>` - 获取店铺详情
- `POST /shop/create` - 创建店铺
- `POST /shop/update/<shop_id>` - 更新店铺
- `POST /shop/delete/<shop_id>` - 删除店铺

### 统计报表
- `GET /statistics/` - 统计页面
- `GET /statistics/merchant/<merchant_id>` - 商户统计
- `GET /statistics/shops/<merchant_id>` - 店铺统计
- `GET /statistics/chart/<merchant_id>` - 图表数据

## 数据模型

### Shop (店铺表)
- `id` - 店铺ID
- `merchant_id` - 所属商户
- `shop_name` - 店铺名称
- `shop_code` - 店铺编码（唯一）
- `biz_type` - 业务类型（1=通用交易, 2=游戏点卡）
- `vendor_id` - 京东vendorId（通用交易）
- `customer_id` - 京东customerId（游戏点卡）
- 密钥字段（AES加密存储）
- 回调地址配置

### Order (订单表更新)
- 新增 `shop_id` 字段关联店铺

### NotificationConfig (通知配置增强)
- 新增 `notify_type` - 通知类型（钉钉/企业微信）
- 新增 `secret` - 加签密钥
- 新增 `at_mobiles` - @手机号列表
- 新增 `trigger_events` - 触发事件

## 安全措施

1. **密钥加密**：MD5和AES密钥使用系统AES密钥加密存储
2. **权限控制**：基于角色的访问控制（RBAC）
3. **数据隔离**：操作员只能访问自己商户的数据
4. **SQL注入防护**：使用SQLAlchemy ORM参数化查询
5. **XSS防护**：模板自动转义用户输入

## 故障排查

### 店铺加载失败
- 检查Flask应用日志：`tail -f /var/log/dianshang/app.log`
- 验证数据库连接：`mysql -u root -p dianshang -e "SELECT COUNT(*) FROM shops;"`

### 统计数据不准确
- 检查订单是否关联到店铺：`SELECT COUNT(*) FROM orders WHERE shop_id IS NULL;`
- 重新运行迁移脚本：`python scripts/migrate_to_shops.py`

### 通知发送失败
- 检查webhook地址是否正确
- 验证钉钉/企业微信密钥配置
- 查看通知日志表：`SELECT * FROM notification_logs ORDER BY create_time DESC LIMIT 10;`

## 性能优化

1. **数据库索引**
   - shops表：merchant_id, biz_type
   - orders表：shop_id

2. **统计缓存**
   - 考虑使用Redis缓存统计结果
   - 设置合理的缓存过期时间

3. **分页查询**
   - 所有列表页面都支持分页
   - 默认每页20条记录

## 后续优化建议

1. **批量操作**：支持批量导入/导出店铺配置
2. **数据导出**：统计数据支持导出Excel
3. **更多图表**：增加趋势图、饼图等
4. **实时监控**：WebSocket实时推送订单状态
5. **移动端**：响应式设计优化移动端体验

## 联系支持

如有问题，请查看：
- 项目文档：README.md
- 部署文档：DEPLOYMENT.md
- 接口文档：接口分析文档.md
