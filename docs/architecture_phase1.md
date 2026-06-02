# AI 会话导出系统 - 架构设计文档

**项目名称**: chat2md
**版本**: v1.0.0
**日期**: 2026-06-02

---

## 一、总体架构设计

### 1.1 架构概览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API Layer                                      │
│                    (FastAPI + Uvicorn + Pydantic)                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Application Layer                                 │
│              (Use Cases / Services / Task Management)                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌────────────────┼────────────────┐
                    ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Domain Layer                                      │
│         (Models / Parser Interfaces / Service Interfaces)                    │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│   │ Conversation│  │   Message   │  │ImageResource│  │ ExportTask  │       │
│   └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌────────────────┼────────────────┐
                    ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Infrastructure Layer                                │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────────────┐    │
│  │  Parsers   │  │ Downloader │  │  Exporter  │  │      Client        │    │
│  │ (Strategy) │  │            │  │ (Markdown) │  │ (HTTP/AIOHTTP)     │    │
│  └────────────┘  └────────────┘  └────────────┘  └────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 分层职责

| 层级 | 职责 | 模块 |
|------|------|------|
| **API Layer** | 接收HTTP请求，参数验证，路由分发 | `api/` |
| **Application Layer** | 编排业务用例，任务调度，结果组装 | `application/` |
| **Domain Layer** | 核心业务实体，接口定义，业务规则 | `domain/model/`, `domain/parser/`, `domain/service/` |
| **Infrastructure Layer** | 外部依赖实现，解析器实现，资源下载 | `infrastructure/parser/`, `infrastructure/downloader/`, `infrastructure/exporter/` |

---

## 二、领域模型设计

### 2.1 类图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Domain Models                                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│   Conversation   │       │     Message      │       │  ImageResource   │
├──────────────────┤       ├──────────────────┤       ├──────────────────┤
│ - id: str        │       │ - id: str        │       │ - id: str        │
│ - title: str     │◄──────│ - conversation_id│       │ - url: str       │
│ - platform: str  │  1..n │ - role: str      │       │ - local_path: str│
│ - created_at     │       │ - content: str   │       │ - filename: str  │
│ - exported_at    │       │ - created_at     │       │ - mime_type: str │
│ - messages: List │       │ - attachments: []│       │ - downloaded: bool│
│ - images: []    │       │ - images: []     │       └──────────────────┘
│ - metadata: Dict│       │ - metadata: Dict │
└──────────────────┘       └──────────────────┘
         │                         │
         │                         │ 1..n
         ▼                         ▼
┌──────────────────┐       ┌──────────────────┐
│   Attachment     │       │    ExportTask    │
├──────────────────┤       ├──────────────────┤
│ - id: str        │       │ - id: str        │
│ - message_id     │       │ - status: Enum   │
│ - name: str      │       │ - conversation_id│
│ - file_type: str │       │ - output_path: str│
│ - url: str       │       │ - progress: float │
│ - size: int      │       │ - error: str     │
│ - local_path: str│       │ - created_at     │
└──────────────────┘       │ - completed_at  │
                            └──────────────────┘

┌──────────────────┐
│   ExportResult   │
├──────────────────┤
│ - task_id: str   │
│ - output_dir: str│
│ - file_count: int│
│ - image_count: int│
│ - success: bool  │
│ - message: str  │
└──────────────────┘
```

### 2.2 领域模型详细设计

#### Conversation (会话聚合根)

```python
class Conversation:
    """会话聚合根 - 整个导出的核心实体"""
    def __init__(
        self,
        id: str,
        title: str,
        platform: Platform,
        created_at: datetime,
        messages: list[Message] = None,
        images: list[ImageResource] = None,
        metadata: dict = None
    ):
        self.id = id
        self.title = title
        self.platform = platform
        self.created_at = created_at
        self.exported_at = None  # 导出时设置
        self.messages = messages or []
        self.images = images or []
        self.metadata = metadata or {}

    def add_message(self, message: Message):
        self.messages.append(message)

    def add_image(self, image: ImageResource):
        self.images.append(image)

    def get_plain_text(self) -> str:
        """获取纯文本内容"""
        return "\n".join([msg.content for msg in self.messages])
```

#### Message (消息)

```python
class Message:
    """消息 - 属于Conversation"""
    def __init__(
        self,
        id: str,
        conversation_id: str,
        role: MessageRole,
        content: str,
        created_at: datetime = None,
        attachments: list[Attachment] = None,
        images: list[ImageResource] = None,
        metadata: dict = None
    ):
        self.id = id
        self.conversation_id = conversation_id
        self.role = role  # Enum: user, assistant, system
        self.content = content
        self.created_at = created_at
        self.attachments = attachments or []
        self.images = images or []
        self.metadata = metadata or {}

    @property
    def is_user(self) -> bool:
        return self.role == MessageRole.USER

    @property
    def is_assistant(self) -> bool:
        return self.role == MessageRole.ASSISTANT
```

#### ImageResource (图片资源)

```python
class ImageResource:
    """图片资源 - 被Message引用"""
    def __init__(
        self,
        id: str,
        url: str,
        filename: str = None,
        mime_type: str = None
    ):
        self.id = id
        self.url = url
        self.local_path = None  # 下载后设置
        self.filename = filename or self._generate_filename()
        self.mime_type = mime_type or self._infer_mime_type()
        self.downloaded = False

    def mark_downloaded(self, local_path: str):
        self.local_path = local_path
        self.downloaded = True
```

#### Attachment (附件)

```python
class Attachment:
    """附件 - 被Message引用"""
    def __init__(
        self,
        id: str,
        message_id: str,
        name: str,
        file_type: str,
        url: str,
        size: int = None
    ):
        self.id = id
        self.message_id = message_id
        self.name = name
        self.file_type = file_type
        self.url = url
        self.size = size
        self.local_path = None
```

#### ExportTask (导出任务)

```python
class ExportTask:
    """导出任务 - 用于跟踪异步导出状态"""
    class Status(Enum):
        PENDING = "pending"
        PARSING = "parsing"
        DOWNLOADING = "downloading"
        EXPORTING = "exporting"
        COMPLETED = "completed"
        FAILED = "failed"

    def __init__(
        self,
        id: str,
        conversation_id: str = None,
        status: Status = Status.PENDING
    ):
        self.id = id
        self.conversation_id = conversation_id
        self.status = status
        self.output_path = None
        self.progress = 0.0
        self.error = None
        self.created_at = datetime.now()
        self.completed_at = None

    def update_progress(self, progress: float, status: Status = None):
        self.progress = min(progress, 100.0)
        if status:
            self.status = status

    def mark_completed(self, output_path: str):
        self.status = self.Status.COMPLETED
        self.output_path = output_path
        self.progress = 100.0
        self.completed_at = datetime.now()

    def mark_failed(self, error: str):
        self.status = self.Status.FAILED
        self.error = error
        self.completed_at = datetime.now()
```

---

## 三、设计模式应用

### 3.1 策略模式 - 平台解析器

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Strategy Pattern - Parsers                           │
└─────────────────────────────────────────────────────────────────────────────┘

                        ┌─────────────────────┐
                        │ConversationParser   │  (Interface)
                        │   <<interface>>     │
                        ├─────────────────────┤
                        │ + parse(url)        │
                        │ + get_conversation()│
                        └──────────┬──────────┘
                                   │
           ┌───────────────────────┼───────────────────────┐
           │                       │                       │
           ▼                       ▼                       ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  ChatGPTParser   │    │  GeminiParser   │    │  DoubaoParser   │
├──────────────────┤    ├──────────────────┤    ├──────────────────┤
│ + parse(url)     │    │ + parse(url)     │    │ + parse(url)     │
│ + get_conversation()    │ + get_conversation()    │ + get_conversation()    │
└──────────────────┘    └──────────────────┘    └──────────────────┘
```

### 3.2 工厂模式 - 解析器工厂

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Factory Pattern                                      │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────┐
                    │    ParserFactory    │
                    ├─────────────────────┤
                    │ + create_parser(url)│
                    │ - _detect_platform()│
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ ConversationParser │
                    │   <<interface>>    │
                    └─────────────────────┘

    URL Pattern Matching:
    - chatgpt.com/*  → ChatGPTParser
    - gemini.google/* → GeminiParser
    - doubao.com/*   → DoubaoParser
```

### 3.3 模板方法模式 - 基础解析器

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Template Method Pattern                                   │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────┐
                    │     BaseParser      │
                    │  <<abstract>>       │
                    ├─────────────────────┤
                    │ # fetch_page(url)   │ ← Template Method
                    │ # extract_data()   │   (定义骨架)
                    │ # transform_model()│
                    │ # download_resources()
                    ├─────────────────────┤
                    │ + parse(url)        │ ← 最终方法
                    │ + get_conversation()│
                    └──────────┬──────────┘
                               │
           ┌───────────────────┼───────────────────┐
           │                   │                   │
           ▼                   ▼                   ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  ChatGPTParser   │  │  GeminiParser    │  │  DoubaoParser    │
├──────────────────┤  ├──────────────────┤  ├──────────────────┤
│ # fetch_page()  │  │ # fetch_page()  │  │ # fetch_page()  │
│ # extract_data()│  │ # extract_data()│  │ # extract_data()│
│ # transform_model()  │ # transform_model()  │ # transform_model()  │
└──────────────────┘  └──────────────────┘  └──────────────────┘

Parse Flow:
1. fetch_page(url)     → 获取HTML
2. extract_data(html)   → 提取JSON/结构化数据
3. transform_model()   → 转换为Conversation
4. download_resources() → 下载图片等资源
```

### 3.4 建造者模式 - 复杂对象构建

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Builder Pattern                                       │
└─────────────────────────────────────────────────────────────────────────────┘

              ┌─────────────────────┐
              │  ConversationBuilder│
              ├─────────────────────┤
              │ + reset()           │
              │ + set_id()          │
              │ + set_title()       │
              │ + set_platform()    │
              │ + add_message()     │
              │ + add_image()       │
              │ + build(): Conv     │
              └─────────────────────┘

              ┌─────────────────────┐
              │   MessageBuilder    │
              ├─────────────────────┤
              │ + reset()           │
              │ + set_id()          │
              │ + set_role()        │
              │ + set_content()     │
              │ + add_image()       │
              │ + build(): Message  │
              └─────────────────────┘

Usage:
builder = ConversationBuilder()
conversation = (builder
    .reset()
    .set_id("conv_123")
    .set_title("设计讨论")
    .set_platform(Platform.CHATGPT)
    .add_message(msg1)
    .add_message(msg2)
    .add_image(img1)
    .build())
```

### 3.5 适配器模式 - 数据结构适配

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Adapter Pattern                                        │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
    │  ChatGPT    │    │   Gemini    │    │   Doubao    │
    │  Raw Data   │    │  Raw Data   │    │  Raw Data   │
    │  (JSON)     │    │   (JSON)    │    │   (JSON)   │
    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘
           │                   │                   │
           ▼                   ▼                   ▼
    ┌─────────────────────────────────────────────────────┐
    │              PlatformDataAdapter                    │
    │  <<interface>> - adapt_to_conversation(raw)         │
    └─────────────────────────────────────────────────────┘
           │
           ▼
    ┌─────────────────────┐
    │    Conversation     │
    │   (Domain Model)   │
    └─────────────────────┘
```

---

## 四、核心接口设计

### 4.1 Parser 接口

```python
from abc import ABC, abstractmethod
from domain.model import Conversation

class ConversationParser(ABC):
    """解析器接口 - 策略模式"""

    @abstractmethod
    async def parse(self, url: str) -> Conversation:
        """解析分享链接，返回会话"""
        pass

    @abstractmethod
    async def fetch_page(self, url: str) -> str:
        """获取页面内容"""
        pass

    @abstractmethod
    def extract_data(self, html: str) -> dict:
        """从页面提取数据"""
        pass

    @abstractmethod
    def transform_to_model(self, data: dict) -> Conversation:
        """转换为目标模型"""
        pass
```

### 4.2 Exporter 接口

```python
from abc import ABC, abstractmethod
from pathlib import Path
from domain.model import Conversation

class MarkdownExporter(ABC):
    """导出器接口"""

    @abstractmethod
    async def export(
        self,
        conversation: Conversation,
        output_dir: Path,
        include_images: bool = True
    ) -> ExportResult:
        """导出会话到Markdown"""
        pass

    @abstractmethod
    def format_message(self, message: Message) -> str:
        """格式化消息为Markdown"""
        pass

    @abstractmethod
    def format_code_block(self, code: str, language: str) -> str:
        """格式化代码块"""
        pass

    @abstractmethod
    def format_table(self, table_data: list[list[str]]) -> str:
        """格式化表格"""
        pass
```

### 4.3 Downloader 接口

```python
from abc import ABC, abstractmethod
from domain.model import ImageResource

class ResourceDownloader(ABC):
    """资源下载器接口"""

    @abstractmethod
    async def download(self, resource: ImageResource, output_dir: Path) -> ImageResource:
        """下载资源"""
        pass

    @abstractmethod
    async def download_batch(
        self,
        resources: list[ImageResource],
        output_dir: Path,
        progress_callback: callable = None
    ) -> list[ImageResource]:
        """批量下载"""
        pass
```

---

## 五、时序图

### 5.1 单个导出时序图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Export Conversation Sequence                            │
└─────────────────────────────────────────────────────────────────────────────┘

  Client       API Layer    App Layer    ParserFactory   Parser     Domain
    │             │           │              │            │           │
    │─POST /export─►         │              │            │           │
    │             │─create──►│              │            │           │
    │             │          │─get_parser──►│            │           │
    │             │          │              │─detect────►│           │
    │             │          │◄──────────────│            │           │
    │             │          │─parse(url)──►│            │           │
    │             │          │              │─fetch_page─►│         │
    │             │          │              │◄─html──────│           │
    │             │          │              │─extract───►│           │
    │             │          │              │◄─data─────│           │
    │             │          │              │─transform─►│          │
    │             │          │◄─Conversation─┤           │           │
    │             │          │─download────►│            │           │
    │             │          │◄─resources──│            │           │
    │             │          │─export──────►│           │           │
    │             │          │◄─ExportResult│           │           │
    │◄────────────│          │              │            │           │
    │  response   │          │              │            │           │
```

### 5.2 批量导出时序图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Batch Export Sequence                                     │
└─────────────────────────────────────────────────────────────────────────────┘

  Client        API Layer      App Layer      TaskManager
    │              │             │                │
    │─POST /batch──►             │                │
    │              │─create────►│                │
    │              │             │─create_tasks──►│
    │              │◄────────────│                │
    │◄─────────────│             │                │
    │  task_ids    │             │                │
    │              │             │                │
    │              │             │◄─async loop────│
    │              │             │   for each url │
    │              │             │   - parse       │
    │              │             │   - download   │
    │              │             │   - export     │
    │              │             │                │
```

---

## 六、模块职责

### 6.1 API Layer (`app/api/`)

| 模块 | 职责 | 公开接口 |
|------|------|----------|
| `routes.py` | 路由定义 | `POST /export`, `POST /export/batch`, `GET /task/{id}`, `GET /download/{id}` |
| `schemas.py` | Pydantic模型 | `ExportRequest`, `BatchExportRequest`, `ExportResponse`, `TaskResponse` |
| `dependencies.py` | 依赖注入 | `get_exporter`, `get_parser_factory` |

### 6.2 Application Layer (`app/application/`)

| 模块 | 职责 | 公开接口 |
|------|------|----------|
| `export_service.py` | 导出服务编排 | `export_conversation()`, `batch_export()` |
| `task_service.py` | 任务管理 | `create_task()`, `get_task_status()`, `update_task()` |

### 6.3 Domain Layer (`app/domain/`)

| 模块 | 职责 | 公开接口 |
|------|------|----------|
| `model/` | 领域模型 | `Conversation`, `Message`, `ImageResource`, `Attachment`, `ExportTask` |
| `parser/` | 解析器接口 | `ConversationParser`, `ParserFactory` |
| `service/` | 领域服务接口 | `Exporter`, `Downloader` |
| `value_objects.py` | 值对象 | `Platform`, `MessageRole` |

### 6.4 Infrastructure Layer (`app/infrastructure/`)

| 模块 | 职责 | 公开接口 |
|------|------|----------|
| `parser/chatgpt.py` | ChatGPT解析器 | `ChatGPTParser` |
| `parser/gemini.py` | Gemini解析器 | `GeminiParser` |
| `parser/doubao.py` | 豆包解析器 | `DoubaoParser` |
| `parser/base.py` | 基础解析器 | `BaseParser` |
| `downloader/` | 资源下载器 | `AiohttpDownloader` |
| `exporter/` | Markdown导出器 | `MarkdownExporterImpl` |
| `client/` | HTTP客户端 | `HttpClient` |

### 6.5 Common Layer (`app/common/`)

| 模块 | 职责 | 公开接口 |
|------|------|----------|
| `exceptions.py` | 异常体系 | `BusinessException`, `ParserException`, etc. |
| `logging.py` | 日志配置 | `get_logger()` |
| `utils.py` | 工具函数 | `generate_id()`, `sanitize_filename()` |

---

## 七、项目目录结构

```
chat2md/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── schemas.py
│   │   └── dependencies.py
│   │
│   ├── application/
│   │   ├── __init__.py
│   │   ├── export_service.py
│   │   └── task_service.py
│   │
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── model/
│   │   │   ├── __init__.py
│   │   │   ├── conversation.py
│   │   │   ├── message.py
│   │   │   ├── image_resource.py
│   │   │   ├── attachment.py
│   │   │   └── export_task.py
│   │   ├── parser/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── interface.py
│   │   │   ├── factory.py
│   │   │   └── registry.py
│   │   ├── service/
│   │   │   ├── __init__.py
│   │   │   └── interfaces.py
│   │   └── value_objects.py
│   │
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── parser/
│   │   │   ├── __init__.py
│   │   │   ├── chatgpt.py
│   │   │   ├── gemini.py
│   │   │   ├── doubao.py
│   │   │   └── adapters/
│   │   │       ├── __init__.py
│   │   │       ├── chatgpt_adapter.py
│   │   │       ├── gemini_adapter.py
│   │   │       └── doubao_adapter.py
│   │   ├── downloader/
│   │   │   ├── __init__.py
│   │   │   ├── aiohttp_downloader.py
│   │   │   └── file_downloader.py
│   │   ├── exporter/
│   │   │   ├── __init__.py
│   │   │   └── markdown_exporter.py
│   │   └── client/
│   │       ├── __init__.py
│   │       └── http_client.py
│   │
│   ├── common/
│   │   ├── __init__.py
│   │   ├── exceptions.py
│   │   ├── logging.py
│   │   └── utils.py
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   │
│   └── main.py
│
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── domain/
│   │   │   ├── __init__.py
│   │   │   ├── test_conversation.py
│   │   │   └── test_message.py
│   │   ├── parser/
│   │   │   ├── __init__.py
│   │   │   ├── test_base_parser.py
│   │   │   ├── test_chatgpt_parser.py
│   │   │   └── test_factory.py
│   │   └── exporter/
│   │       ├── __init__.py
│   │       └── test_markdown_exporter.py
│   │
│   └── integration/
│       ├── __init__.py
│       ├── test_export_api.py
│       └── test_parsers.py
│
├── output/                    # 导出文件输出目录
├── static/
│   └── css/
│       └── style.css
├── templates/
│   └── index.html
│
├── pyproject.toml
├── uv.lock
├── README.md
├── CLAUDE.md
└── .env.example
```

---

## 八、异常体系设计

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Exception Hierarchy                                 │
└─────────────────────────────────────────────────────────────────────────────┘

                         ┌───────────────┐
                         │BusinessException│
                         │  <<abstract>> │
                         └───────┬───────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         ▼                       ▼                       ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  ParserException │    │DownloadException │    │ ExportException │
├──────────────────┤    ├──────────────────┤    ├──────────────────┤
│ - parser_type    │    │ - resource_url   │    │ - output_path   │
│ - url            │    │ - status_code    │    │ - file_count    │
└──────────────────┘    └──────────────────┘    └──────────────────┘
         │
         ▼
┌──────────────────┐
│ PlatformNotSupported│
├──────────────────┤
│ - url            │
│ - supported: [] │
└──────────────────┘
```

```python
# common/exceptions.py

class BusinessException(Exception):
    """业务异常基类"""
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code or "BUSINESS_ERROR"
        super().__init__(self.message)

class ParserException(BusinessException):
    """解析器异常"""
    def __init__(self, message: str, parser_type: str = None, url: str = None):
        super().__init__(message, code="PARSER_ERROR")
        self.parser_type = parser_type
        self.url = url

class PlatformNotSupportedException(ParserException):
    """平台不支持"""
    def __init__(self, url: str, supported_platforms: list[str]):
        super().__init__(
            f"Platform not supported: {url}",
            url=url
        )
        self.supported_platforms = supported_platforms

class DownloadException(BusinessException):
    """下载异常"""
    def __init__(self, message: str, resource_url: str = None, status_code: int = None):
        super().__init__(message, code="DOWNLOAD_ERROR")
        self.resource_url = resource_url
        self.status_code = status_code

class ExportException(BusinessException):
    """导出异常"""
    def __init__(self, message: str, output_path: str = None):
        super().__init__(message, code="EXPORT_ERROR")
        self.output_path = output_path
```

---

## 九、日志设计

### 9.1 日志格式

使用 `structlog` 实现结构化日志:

```python
# 输出示例
{
    "event": "export_started",
    "task_id": "task_123",
    "platform": "chatgpt",
    "url": "https://chatgpt.com/share/xxx",
    "timestamp": "2026-06-02T10:30:00Z"
}
```

### 9.2 日志分级

| 层级 | 场景 | 字段 |
|------|------|------|
| `export_started` | 开始导出 | `task_id`, `platform`, `url` |
| `parse_started` | 开始解析 | `parser_type`, `url` |
| `parse_completed` | 解析完成 | `parser_type`, `message_count` |
| `download_started` | 开始下载 | `resource_count`, `url` |
| `download_progress` | 下载进度 | `current`, `total`, `percentage` |
| `download_completed` | 下载完成 | `local_path`, `filename` |
| `export_completed` | 导出完成 | `output_dir`, `file_count` |
| `error` | 错误 | `error_type`, `error_message`, `traceback` |

---

## 十、技术栈选型

| 组件 | 选型 | 理由 |
|------|------|------|
| Web框架 | FastAPI | 异步支持好，类型安全，OpenAPI内置 |
| HTTP客户端 | aiohttp | 异步HTTP，支持连接池 |
| HTML解析 | BeautifulSoup4 | 成熟的HTML解析库 |
| Markdown | mistune | 轻量级，插件化 |
| 图片下载 | aiofiles + aiohttp | 异步文件IO |
| 任务队列 | 内存/Redis | 前期内存，后期可扩展Redis |
| 配置管理 | pydantic-settings | 类型安全的环境变量 |
| 日志 | structlog | 结构化日志 |
| 测试 | pytest + pytest-asyncio | 异步测试支持 |

---

**第一阶段文档结束 - 等待确认后继续第二阶段**

如需调整架构或补充内容，请告知。