# 聊两毛的

**chat to markdown** 是一个把 AI 聊天分享链接导出为 Markdown 文档包的工具。它提供后端 API、MCP 服务和可视化页面，适合接入个人知识库、RAG 流程、Agent 工作流或自动化归档任务。

## 核心能力

- 后端接口：FastAPI 提供单条导出、批量导出、任务查询、结果下载、平台配置查询。
- MCP 服务：可被 Claude、Codex、LangGraph 等 MCP Client 调用。
- 可视化页面：打开首页即可粘贴链接、配置导出路径和 Markdown 输出结构。
- 可配置导出：支持输出目录、格式、图片、Frontmatter、index、manifest、messages 文件开关。
- 可配置链接种类：通过环境变量配置启用平台和 URL 匹配规则。
- AI 可读文档包：默认输出 `index.md`、`conversation.md`、`messages.md`、`manifest.md` 和图片目录。

## 当前平台

| 平台 | 默认状态 | 链接匹配 |
| --- | --- | --- |
| ChatGPT | 启用 | `chatgpt.com/share` |
| Gemini | 启用 | `gemini.google.com/share`, `g.co/gemini/share` |
| Doubao | 已注册但默认未启用 | `doubao.com/share` |

Doubao 解析器仍是骨架实现，默认未启用，避免导出时产生伪成功。

## 安装与启动

```bash
pip install -e .
python -m app.main
```

访问：

- Web UI: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health

如果使用 Playwright 解析真实分享页，需要安装浏览器：

```bash
playwright install chromium
```

## 后端 API

### 单条导出

```bash
curl -X POST http://localhost:8000/api/v1/export \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://chatgpt.com/share/xxx",
    "output_dir": "./output",
    "format": "ai_readable",
    "include_images": true,
    "include_metadata": true,
    "include_frontmatter": true,
    "create_index": true,
    "create_messages": true,
    "create_manifest": true,
    "file_basename": "conversation"
  }'
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
    "output_dir": "./output"
  }'
```

### 查询任务

```bash
curl http://localhost:8000/api/v1/task/{task_id}
```

### 下载或查看结果

```bash
curl http://localhost:8000/api/v1/download/{task_id}
```

### 查看运行配置

```bash
curl http://localhost:8000/api/v1/config
curl http://localhost:8000/api/v1/platforms
```

## MCP 服务

启动：

```bash
python -m app.mcp.server
```

MCP 配置示例：

```json
{
  "mcpServers": {
    "chat-to-markdown": {
      "command": "python",
      "args": ["-m", "app.mcp.server"],
      "cwd": "D:/python_proj/chat2md"
    }
  }
}
```

工具：

- `export_chat_to_markdown`: 导出聊天链接为 Markdown 文档包。
- `get_export_status`: 查询导出任务状态。
- `list_supported_platforms`: 查看当前启用且可用的平台。

## 导出结果

默认输出目录：

```text
output/
  Conversation_Title/
    index.md
    conversation.md
    messages.md
    manifest.md
    images/
```

文件说明：

- `index.md`: 给人和 Agent 快速定位文件、来源和统计信息。
- `conversation.md`: 完整对话正文，带 Frontmatter、平台、来源、消息编号和 block id。
- `messages.md`: 每条消息独立分节，适合向量化和检索切片。
- `manifest.md`: 导出选项、文件清单、图片清单等机器可读信息。
- `images/`: 下载后的图片资源。

## 配置

创建 `.env`：

```env
OUTPUT_DIR=./output
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

# 可选代理。为空时不强制代理。
HTTP_PROXY=http://127.0.0.1:7890

# 平台和匹配规则。pydantic-settings 支持 JSON 风格复杂类型。
ENABLED_PLATFORMS=["chatgpt","gemini"]
PLATFORM_URL_PATTERNS={"chatgpt":["chatgpt.com/share"],"gemini":["gemini.google.com/share","g.co/gemini/share"],"doubao":["doubao.com/share"]}

# 默认导出选项
DEFAULT_EXPORT_FORMAT=ai_readable
DEFAULT_INCLUDE_IMAGES=true
DEFAULT_INCLUDE_METADATA=true
DEFAULT_INCLUDE_FRONTMATTER=true
DEFAULT_CREATE_INDEX=true
DEFAULT_CREATE_MANIFEST=true
DEFAULT_CREATE_MESSAGES=true
```

## 测试

```bash
pytest tests/
```

如果本机装了 `uv`：

```bash
uv run pytest tests/
```
