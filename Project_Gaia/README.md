# 🌍 Project Gaia - 盖亚计划

> 凡人财务自由防御系统

## 📖 项目简介

盖亚计划是一个智能化的财务监控系统，专为 2U2G 服务器优化，通过 AI 技术建立"数据-事件-逻辑"的永久关联，辅助用户在市场剧烈波动中做出冷静决策。

### 核心特性

- 🔍 **低功耗监控**: 60秒轮询 + 30分钟智能冷却
- 🤖 **AI 智能研判**: Gemini 3 Flash (哨兵) + Gemini 1.5 Pro (深度)
- 📊 **多资产支持**: 加密货币 (CCXT) + 传统金融 (Yahoo Finance)
- 💬 **实时推送**: Telegram Markdown 格式通知
- 🧠 **永久记忆**: SQLite 存储价格历史和事件归因
- 📋 **每日复盘**: 自动生成市场形势预演报告

## 🚀 快速开始

### 1. 安装依赖

```bash
cd Project_Gaia
pip install -r requirements.txt
```

### 2. 配置环境

编辑 `config/.env` 文件，填入你的 API Keys：

```env
GEMINI_API_KEY=your_gemini_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here
```

### 3. 配置监控资产

编辑 `config/assets.json` 文件，添加你要监控的资产：

```json
{
  "name": "比特币",
  "symbol": "BTC/USDT",
  "source": "binance",
  "threshold": 0.03,
  "level": "high",
  "enabled": true
}
```

**参数说明：**
- `name`: 资产名称
- `symbol`: 交易对/股票代码
- `source`: 数据源 (`binance`, `okx`, `yfinance` 等)
- `threshold`: 波动阈值 (0.03 = 3%)
- `level`: 告警级别 (`low`, `medium`, `high`)
- `enabled`: 是否启用

### 4. 运行系统

```bash
python main.py
```

## 📁 项目结构

```
Project_Gaia/
├── config/                 # 配置文件目录
│   ├── assets.json         # 监控资产配置
│   ├── .env                # 敏感信息 (API Keys)
│   └── assets_loader.py    # 配置加载器
├── core/                   # 核心逻辑模块
│   ├── fetcher.py          # 数据抓取引擎
│   ├── monitor.py          # 波动率算法与触发逻辑
│   └── brain.py            # Gemini API 调用与 AI 分析
├── database/               # 存储层
│   ├── models.py           # 数据库表结构定义
│   └── gaia_main.db        # SQLite 数据库文件 (运行后生成)
├── utils/                  # 工具类
│   ├── logger.py           # 日志记录
│   └── notifier.py         # Telegram 分发接口
├── logs/                   # 运行日志输出目录
├── requirements.txt        # 依赖包列表
├── main.py                 # 程序入口
└── README.md               # 项目文档
```

## 🔧 系统配置

### 环境变量

在 `config/.env` 中配置：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `GEMINI_API_KEY` | Gemini API 密钥 | - |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token | - |
| `TELEGRAM_CHAT_ID` | 接收消息的用户ID | - |
| `MONITOR_INTERVAL` | 监控轮询间隔 (秒) | 60 |
| `AI_COOLDOWN_PERIOD` | AI 分析冷却期 (秒) | 1800 |
| `DAILY_REPORT_TIME` | 每日复盘时间 | 22:30 |
| `LOG_LEVEL` | 日志级别 | INFO |

## 🔄 工作流程

### 1. 监控流程

```
60秒轮询
  ↓
抓取最新价格
  ↓
计算波动率
  ↓
是否超过阈值？
  ├─ 否 → 进入下一个循环
  └─ 是 → 检查冷却期
           ├─ 在冷却期 → 进入下一个循环
           └─ 未冷却 → 触发 AI 分析
                      ↓
                 推送 Telegram
                      ↓
                 记录事件到数据库
```

### 2. 每日复盘

每天北京时间 22:30 自动生成并发送市场形势预演报告。

## 🛡️ 安全性说明

1. **数据库安全**: SQLite 数据库存储在本地，不对外开放
2. **敏感信息**: API Keys 存储在 `.env` 文件中，已加入 `.gitignore`
3. **异常处理**: 所有核心模块都包含 try-except 异常捕获
4. **自动重启**: API 失败时系统会自动恢复，不会崩溃

## 📊 数据库结构

### price_history (价格历史表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| symbol | TEXT | 资产符号 |
| price | REAL | 价格 |
| volume | REAL | 交易量 |
| timestamp | DATETIME | 时间戳 |
| created_at | DATETIME | 创建时间 |

### event_log (事件日志表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| symbol | TEXT | 资产符号 |
| price | REAL | 价格 |
| volatility | REAL | 波动率 |
| alert_level | TEXT | 告警级别 |
| ai_analysis | TEXT | AI 分析结果 |
| news_summary | TEXT | 新闻摘要 |
| timestamp | DATETIME | 时间戳 |
| created_at | DATETIME | 创建时间 |

## 🔍 故障排查

### 1. 无法获取数据

- 检查网络连接
- 确认数据源是否可用
- 查看日志文件 (`logs/gaia_YYYYMMDD.log`)

### 2. Telegram 消息未收到

- 验证 Bot Token 和 Chat ID 是否正确
- 确认 Bot 已启动并添加了用户

### 3. AI 分析失败

- 检查 Gemini API Key 是否有效
- 确认 API 配额是否充足
- 查看日志中的详细错误信息

## 📝 技术栈

- **语言**: Python 3.10+
- **异步框架**: asyncio
- **数据抓取**: CCXT, yfinance
- **AI 引擎**: Google Gemini API
- **数据库**: SQLite
- **通知**: Telegram Bot API
- **日志**: Python logging

## 🎯 性能优化

- 异步并发抓取，避免阻塞
- 智能冷却机制，减少不必要的 AI 调用
- 数据库索引优化，提升查询速度
- 日志文件自动清理，防止磁盘占满

## 📄 许可证

本项目仅供学习和个人使用。

## ⚠️ 风险提示

市场有风险，投资需谨慎。本系统仅提供数据分析和参考，不构成任何投资建议。用户应根据自身情况做出决策，并承担相应风险。

---

✨ **盖亚计划 - 让数据说话，让决策理性**
