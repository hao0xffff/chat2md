# Chat2MD 使用指南

AI 会话导出工具 - 将 ChatGPT、Gemini、豆包等平台的分享链接导出为 Markdown 知识文档。

---

## 目录

- [快速开始](#快速开始)
- [Web UI 使用](#web-ui-使用)
- [API 接口](#api-接口)
- [MCP 服务](#mcp-服务)
- [命令行使用](#命令行使用)
- [项目结构](#项目结构)
- [配置说明](#配置说明)

---

## 快速开始

### 1. 安装依赖

```bash
cd d:/python_proj/chat2md
pip install -e .
```

### 2. 启动服务

```bash
python -m app.main
```

访问 **http://localhost:8000** 打开 Web UI。

### 3. 导出对话

在 Web UI 中输入分享链接，点击"开始导出"。

---

## Web UI 使用

访问 `http://localhost:8000` 打开 Web 界面。

### 功能特性

- **三大平台支持** - ChatGPT、Gemini、豆包，带平台图标
- **输出目录可选** - 留空使用默认 `output/` 目录
- **批量导出** - 多个链接用换行分隔
- **实时状态** - 自动轮询任务进度
- **暗色主题** - 深色护眼界面

### 界面预览

```
┌─────────────────────────────────────────────┐
│  📦 Chat2MD                                │
│  将 AI 会话导出为 Markdown 知识文档        │
├─────────────────────────────────────────────┤
│  [ChatGPT]  [Gemini]  [豆包]               │
├─────────────────────────────────────────────┤
│  分享链接: ________________________________ │
│  输出目录: [可选]  批量模式: [单选]        │
│  [========== 开始导出 ==========]           │
├─────────────────────────────────────────────┤
│  导出任务                              2    │
│  ┌──────────────────────────────────────┐  │
│  │ ⏳ https://chatgpt.com/share/xxx    │  │
│  │  status: parsing  progress: 10%     │  │
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

---

## API 接口

服务启动后访问 **http://localhost:8000/docs** 查看 Swagger 文档。

### 基础接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/export` | POST | 单个导出 |
| `/api/v1/export/batch` | POST | 批量导出 |
| `/api/v1/task/{task_id}` | GET | 查询任务状态 |
| `/api/v1/download/{task_id}` | GET | 下载结果 |
| `/api/v1/health` | GET | 健康检查 |

### 单个导出

```bash
curl -X POST http://localhost:8000/api/v1/export \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://chatgpt.com/share/6a1e7a13-04a4-8324-9d3e-d16d2357e6d4",
    "output_dir": "/tmp/exports"
  }'
```

响应：
```json
{
  "task_id": "abc123",
  "status": "pending",
  "message": "Export task created"
}
```

### 批量导出

```bash
curl -X POST http://localhost:8000/api/v1/export/batch \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://chatgpt.com/share/xxx",
      "https://gemini.google.com/share/yyy"
    ],
    "output_dir": "/tmp/exports"
  }'
```

### 查询状态

```bash
curl http://localhost:8000/api/v1/task/{task_id}
```

响应：
```json
{
  "task_id": "abc123",
  "status": "completed",
  "progress": 100,
  "output_path": "output/Skill定义与组成",
  "message_count": 8,
  "image_count": 0
}
```

---

## MCP 服务

Chat2MD 可作为 MCP (Model Context Protocol) 服务使用，集成到 LangGraph 等 Agent 框架中。

### 启动 MCP 服务

```bash
cd d:/python_proj/chat2md
python -m app.mcp.server
```

### 可用工具

#### 1. export_chat_to_markdown

导出 AI 会话到 Markdown 文件。

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `url` | string | 是 | AI 平台分享链接 URL |
| `output_dir` | string | 否 | 输出目录路径 |

**示例：**
```python
from app.mcp.server import call_tool

result = await call_tool("export_chat_to_markdown", {
    "url": "https://chatgpt.com/share/6a1e7a13-04a4-8324-9d3e-d16d2357e6d4",
    "output_dir": "/tmp/exports"
})
```

#### 2. get_export_status

查询导出任务状态。

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `task_id` | string | 是 | 任务 ID |

**示例：**
```python
result = await call_tool("get_export_status", {
    "task_id": "abc123"
})
```

#### 3. list_supported_platforms

列出所有支持的 AI 平台。

**参数：** 无

**示例：**
```python
result = await call_tool("list_supported_platforms", {})
```

### LangGraph 集成示例

```python
from app.mcp.server import list_tools, call_tool

async def use_chat2md():
    # 获取可用工具
    tools = await list_tools()

    # 导出对话
    result = await call_tool("export_chat_to_markdown", {
        "url": "https://gemini.google.com/share/8908a46e4ac2",
        "output_dir": "./output"
    })

    print(result[0].text)
    # 输出: Successfully exported to: output/direct_access_to_Google_AI
    #       Messages: 48, Images: 0
```

### MCP 服务发现配置

在 Claude Code 或其他 MCP Client 中配置：

```json
{
  "mcpServers": {
    "chat2md": {
      "command": "python",
      "args": ["-m", "app.mcp.server"],
      "cwd": "d:/python_proj/chat2md"
    }
  }
}
```

---

## 命令行使用

### 直接调用导出服务

```python
import asyncio
from app.infrastructure.parser.chatgpt import ChatGPTParser
from app.infrastructure.exporter.markdown_exporter import MarkdownExporter
from app.domain.model.knowledge_document import KnowledgeDocument
from pathlib import Path

async def main():
    # 1. 解析对话
    parser = ChatGPTParser()
    url = "https://chatgpt.com/share/6a1e7a13-04a4-8324-9d3e-d16d2357e6d4"
    conversation = await parser.parse(url)
    print(f"解析完成: {len(conversation.blocks)} 条消息")

    # 2. 转换为知识文档
    doc = KnowledgeDocument(
        id=conversation.id,
        title=conversation.title or "Untitled",
        platform=conversation.platform,
        conversation_id=conversation.id,
        blocks=list(conversation.blocks),
        images=list(conversation.images),
        metadata=conversation.metadata,
    )

    # 3. 导出 Markdown
    exporter = MarkdownExporter()
    result = await exporter.export(doc, Path("output"))
    print(f"导出结果: {result.output_path}")

asyncio.run(main())
```

---

## 项目结构

```
chat2md/
├── app/
│   ├── api/                    # API 层
│   │   ├── routes.py           # API 路由
│   │   ├── schemas.py          # 请求/响应 schema
│   │   └── dependencies.py    # 依赖注入容器
│   ├── application/            # 应用层
│   │   ├── export_service.py   # 导出服务（编排工作流）
│   │   ├── export_task.py      # 任务模型
│   │   └── task_service.py     # 任务服务
│   ├── domain/                 # 领域层
│   │   ├── model/              # 领域模型
│   │   │   ├── conversation.py
│   │   │   ├── block.py
│   │   │   ├── image_resource.py
│   │   │   └── knowledge_document.py
│   │   ├── parser/             # 解析器
│   │   │   ├── base.py         # 基础解析器（模板方法）
│   │   │   ├── registry.py     # 注册表
│   │   │   └── interface.py    # 解析器接口
│   │   └── service/            # 领域服务接口
│   ├── infrastructure/         # 基础设施层
│   │   ├── parser/             # 解析器实现
│   │   │   ├── chatgpt.py      # ChatGPT 解析器
│   │   │   ├── gemini.py       # Gemini 解析器
│   │   │   ├── doubao.py       # 豆包解析器
│   │   │   ├── playwright_parser.py
│   │   │   └── gemini_playwright_parser.py
│   │   ├── exporter/           # 导出器
│   │   │   └── markdown_exporter.py
│   │   ├── downloader/          # 下载器
│   │   │   └── aiohttp_downloader.py
│   │   └── client/             # HTTP 客户端
│   │       └── http_client.py
│   ├── mcp/                    # MCP 服务层
│   │   └── server.py           # MCP 服务器
│   ├── config/                 # 配置
│   │   └── settings.py
│   ├── common/                 # 公共组件
│   │   ├── exceptions.py
│   │   ├── logging.py
│   │   └── utils.py
│   └── main.py                # FastAPI 入口
├── templates/                 # 模板
│   └── index.html             # Web UI
├── static/                    # 静态文件
├── output/                    # 导出输出目录
├── docs/                      # 文档
│   └── USAGE.md              # 本文档
├── pyproject.toml
└── README.md
```

---

## 配置说明

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OUTPUT_DIR` | `output` | 默认输出目录 |
| `HTTP_PROXY` | `http://127.0.0.1:7890` | HTTP 代理（用于访问海外 AI 平台） |
| `HTTP_TIMEOUT` | `30` | HTTP 请求超时（秒） |
| `MAX_CONCURRENT_DOWNLOADS` | `10` | 最大并发下载数 |

### 配置文件

创建 `.env` 文件：

```bash
OUTPUT_DIR=./output
HTTP_PROXY=http://127.0.0.1:7890
LOG_LEVEL=INFO
```

---

## 支持的平台

| 平台 | URL 格式 | 状态 |
|------|----------|------|
| ChatGPT | `https://chatgpt.com/share/xxx` | ✅ 已实现 |
| Gemini | `https://gemini.google.com/share/xxx` | ✅ 已实现 |
| 豆包 | `https://doubao.com/share/xxx` | 🔧 骨架 |

---

## 架构设计

Chat2MD 采用 DDD (领域驱动设计) + 模块化单体架构：

```
┌─────────────────────────────────────────────────┐
│                   API Layer                      │
│              (FastAPI + Web UI)                  │
├─────────────────────────────────────────────────┤
│                Application Layer                 │
│         (ExportService, TaskService)             │
├─────────────────────────────────────────────────┤
│                  Domain Layer                    │
│   (Conversation, Block, Parser Interfaces)      │
├─────────────────────────────────────────────────┤
│               Infrastructure Layer              │
│    (Playwright Parsers, MarkdownExporter)       │
└─────────────────────────────────────────────────┘
```

### 设计模式

1. **策略模式** - 每个平台独立的解析器
2. **模板方法模式** - `BaseParser` 定义统一解析流程
3. **注册表模式** - `ParserRegistry` 运行时自动注册解析器
4. **适配器模式** - 统一的数据结构转换

---

## 常见问题

### Q: 导出时图片无法下载？

A: ChatGPT 分享链接中的用户上传图片需要登录态才能访问，公开分享页面只显示占位符。这是 ChatGPT 分享机制的限制，不是代码问题。

### Q: 代理无法连接？

A: 确保本地代理服务运行中，或通过环境变量 `HTTP_PROXY` 配置代理。

### Q: Gemini 解析失败？

A: Gemini 页面需要较长的加载时间，代码中默认等待 5 秒。如果仍失败，检查网络连接和代理设置。

### Q: 如何查看详细日志？

A: 启动服务时设置 `LOG_LEVEL=DEBUG`：

```bash
LOG_LEVEL=DEBUG python -m app.main
```

---

## License

MIT License