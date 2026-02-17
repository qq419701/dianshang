# 电商平台管理系统

> 京东通用交易 & 游戏点卡 & 阿奇索开放平台 — 对接管理系统

## 项目简介

本系统基于 Flask 框架开发，用于对接京东通用交易平台、京东游戏点卡平台和阿奇索开放平台，实现订单接收、充值处理、卡密管理、异步回调等核心业务功能。

## 功能特性

### 京东通用交易平台
- ✅ 提交充值 & 提取卡密接口（beginDistill）
- ✅ 生产反查接口（findDistill）
- ✅ 异步回调通知京东（/produce/result）
- ✅ AES-256 ECB 卡密加密
- ✅ MD5 签名验证

### 京东游戏点卡平台
- ✅ 提单校验接口（preCheck）
- ✅ 直充接单接口（directCharge）
- ✅ 直充订单查询（directQuery）
- ✅ 卡密接单接口（cardOrder）
- ✅ 卡密订单查询（cardQuery）
- ✅ 直充回调 & 卡密回调（GBK编码）

### 阿奇索开放平台（可选模块）
- ✅ 订单拉取
- ✅ 自动发货
- ✅ 发货状态查询
- ✅ 商品库存查询
- ✅ 未配置时不影响主流程

### 管理后台
- ✅ 中文管理界面
- ✅ 数据概览仪表盘
- ✅ 订单管理（搜索/筛选/分页）
- ✅ 系统配置（京东/阿奇索平台）
- ✅ 接口地址自动生成器
- ✅ 回调日志查看

### 安全特性
- ✅ 密钥 AES 加密存储
- ✅ 签名校验
- ✅ 前端密钥脱敏显示
- ✅ 环境变量配置（不硬编码）

## 技术栈

| 组件 | 技术 |
|------|------|
| 后端框架 | Python Flask |
| 数据库 | MySQL 5.7+ |
| ORM | Flask-SQLAlchemy |
| 加密 | cryptography（AES-256 ECB） |
| 部署 | Gunicorn + Nginx |
| 面板 | 宝塔面板 |

## 项目结构

```
├── app/                        # 应用代码目录
│   ├── __init__.py             # Flask 应用工厂
│   ├── models/                 # 数据库模型
│   │   ├── merchant_config.py  # 商户配置模型
│   │   ├── order.py            # 订单模型
│   │   └── callback_log.py     # 回调日志模型
│   ├── routes/                 # 路由控制器
│   │   ├── jd_general.py       # 京东通用交易路由
│   │   ├── jd_game.py          # 京东游戏点卡路由
│   │   ├── agiso.py            # 阿奇索平台路由
│   │   └── admin.py            # 后台管理路由
│   ├── services/               # 业务服务层
│   │   ├── jd_general_service.py
│   │   ├── jd_game_service.py
│   │   └── agiso_service.py
│   ├── utils/                  # 工具模块
│   │   ├── sign.py             # 签名工具
│   │   └── crypto.py           # 加密工具
│   ├── templates/              # 页面模板（中文界面）
│   └── static/                 # 静态资源
├── tests/                      # 单元测试
├── config.py                   # 应用配置
├── run.py                      # 启动入口
├── init_db.sql                 # 数据库初始化脚本
├── requirements.txt            # Python 依赖
├── .env.example                # 环境变量示例
├── 接口分析文档.md              # 接口分析文档
└── 宝塔面板部署教程.md           # 部署教程
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填写数据库和密钥配置
```

### 3. 初始化数据库

```bash
mysql -u root -p < init_db.sql
```

### 4. 启动应用

```bash
python run.py
```

### 5. 访问管理后台

浏览器访问 `http://localhost:5000/admin/`

## 部署

详细的宝塔面板部署教程请参阅 [宝塔面板部署教程.md](宝塔面板部署教程.md)

## 接口文档

详细的接口分析请参阅 [接口分析文档.md](接口分析文档.md)

## API 端点

### 京东通用交易（京东调用我方）
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/jd/general/beginDistill` | 提交充值/提取卡密 |
| POST | `/api/jd/general/findDistill` | 生产反查 |

### 京东游戏点卡（京东调用我方）
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/jd/game/preCheck` | 提单校验 |
| POST | `/api/jd/game/directCharge` | 直充接单 |
| POST | `/api/jd/game/directQuery` | 直充查询 |
| POST | `/api/jd/game/cardOrder` | 卡密接单 |
| POST | `/api/jd/game/cardQuery` | 卡密查询 |

### 阿奇索平台（可选模块）
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/agiso/pull` | 拉取待发货订单 |
| POST | `/api/agiso/deliver` | 自动发货 |
| POST | `/api/agiso/status` | 发货状态查询 |
| POST | `/api/agiso/stock` | 商品库存查询 |

### 管理后台
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin/` | 仪表盘首页 |
| GET | `/admin/orders` | 订单管理 |
| GET | `/admin/config` | 系统配置 |
| GET | `/admin/callbacks` | 回调日志 |

## 运行测试

```bash
python -m unittest tests.test_utils -v
```
