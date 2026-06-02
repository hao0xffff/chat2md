# AI 会话导出系统 - 架构设计文档 (修订版)

**项目名称**: chat2md
**版本**: v1.0.0
**日期**: 2026-06-02
**状态**: 第二阶段

---

## 一、调整说明

| 调整项 | 原设计 | 新设计 | 原因 |
|--------|--------|--------|------|
| ExportTask | Domain Layer | Application Layer | 任务管理属于应用层职责 |
| Builder模式 | ConversationBuilder | 删除 | 直接构造函数足够简洁 |
| ParserFactory | 工厂模式 | ParserRegistry | 注册表模式更灵活，支持运行时注册 |
| Message | 数据结构 | Block结构 | 更灵活地表示不同类型内容块 |
| ParserContext | 无 | 新增 | 在解析流程中传递上下文数据 |
| Exporter | 抽象类 | 统一接口强调 | 清晰接口定义 |
| Repository | 无 | 新增接口层 | 依赖倒置，解耦数据存储 |
| KnowledgeDocument | 无 | 新增领域模型 | 代表导出的知识文档实体 |

---

## 二、核心领域模型调整

### 2.1 Block 结构 (替代 Message)

```python
class Block:
    """内容块 - 替代原来的Message"""
    class Type(Enum):
        TEXT = "text"
        CODE = "code"
        TABLE = "table"
        IMAGE = "image"
        QUOTE = "quote"
        LIST = "list"

    def __init__(
        self,
        id: str,
        block_type: Type,
        content: str = None,
        language: str = None,      # for CODE
        headers: list = None,     # for TABLE
        rows: list[list] = None,  # for TABLE
        image_url: str = None,   # for IMAGE
        alt_text: str = None,     # for IMAGE
        level: int = None,        # for QUOTE (引用层级)
        items: list = None,      # for LIST
        metadata: dict = None
    ):
        self.id = id
        self.block_type = block_type
        self.content = content
        self.language = language
        self.headers = headers
        self.rows = rows
        self.image_url = image_url
        self.alt_text = alt_text
        self.level = level
        self.items = items
        self.metadata = metadata or {}
```

### 2.2 ParserContext

```python
@dataclass
class ParserContext:
    """解析器上下文 - 贯穿整个解析流程"""
    url: str
    raw_html: str = None
    raw_data: dict = None
    platform: Platform = None
    conversation_id: str = None
    title: str = None
    created_at: datetime = None
    blocks: list[Block] = field(default_factory=list)
    images: list[ImageResource] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def add_block(self, block: Block):
        self.blocks.append(block)

    def add_image(self, image: ImageResource):
        self.images.append(image)
```

### 2.3 KnowledgeDocument

```python
class KnowledgeDocument:
    """知识文档 - 导出的最终产物"""
    def __init__(
        self,
        id: str,
        title: str,
        platform: Platform,
        conversation_id: str,
        blocks: list[Block] = None,
        images: list[ImageResource] = None,
        metadata: dict = None
    ):
        self.id = id
        self.title = title
        self.platform = platform
        self.conversation_id = conversation_id
        self.blocks = blocks or []
        self.images = images or []
        self.metadata = metadata or {}
        self.created_at = datetime.now()

    @property
    def user_blocks(self) -> list[Block]:
        """获取用户消息块"""
        return [b for b in self.blocks if b.block_type == Block.Type.TEXT and b.metadata.get("role") == "user"]

    @property
    def assistant_blocks(self) -> list[Block]:
        """获取助手消息块"""
        return [b for b in self.blocks if b.block_type == Block.Type.TEXT and b.metadata.get("role") == "assistant"]

    def add_block(self, block: Block):
        self.blocks.append(block)

    def add_image(self, image: ImageResource):
        self.images.append(image)
```

---

## 三、模块职责 (修订版)

### 3.1 Domain Layer (`app/domain/`)

```
domain/
├── model/
│   ├── __init__.py
│   ├── conversation.py      # Conversation 聚合根
│   ├── block.py             # Block 内容块
│   ├── image_resource.py   # ImageResource
│   ├── attachment.py       # Attachment
│   └── knowledge_document.py # KnowledgeDocument
│
├── parser/
│   ├── __init__.py
│   ├── interface.py         # ConversationParser 接口
│   ├── registry.py          # ParserRegistry (替代Factory)
│   ├── context.py           # ParserContext
│   └── base.py              # BaseParser 模板方法
│
├── repository/
│   ├── __init__.py
│   └── interfaces.py        # Repository 接口定义
│   │                         # - ConversationRepository
│   │                         # - ExportTaskRepository
│   │                         # - ImageRepository
│
└── service/
    ├── __init__.py
    └── interfaces.py         # Service 接口定义
                                # - ExporterInterface
                                # - DownloaderInterface
```

### 3.2 Application Layer (`app/application/`)

```
application/
├── __init__.py
├── export_service.py       # 导出服务编排
├── task_service.py          # 任务管理 (ExportTask放在这里)
├── dto.py                   # Data Transfer Objects
└── mapper.py                # Domain <-> DTO 映射
```

### 3.3 Infrastructure Layer (`app/infrastructure/`)

```
infrastructure/
├── parser/                  # 解析器实现 (策略)
│   ├── __init__.py
│   ├── chatgpt.py
│   ├── gemini.py
│   ├── doubao.py
│   └── adapters/           # 数据适配器
│       ├── chatgpt_adapter.py
│       ├── gemini_adapter.py
│       └── doubao_adapter.py
│
├── repository/             # Repository 实现
│   ├── __init__.py
│   ├── in_memory_conversation_repo.py
│   └── in_memory_task_repo.py
│
├── exporter/               # 导出器实现
│   ├── __init__.py
│   └── markdown_exporter.py
│
├── downloader/             # 下载器实现
│   ├── __init__.py
│   └── aiohttp_downloader.py
│
└── client/                 # HTTP客户端
    ├── __init__.py
    └── http_client.py
```

---

## 四、ParserRegistry 设计

```python
class ParserRegistry:
    """
    解析器注册表 - 替代 ParserFactory
    支持运行时注册解析器，更灵活
    """
    _instance = None
    _parsers: dict[str, type[ConversationParser]] = {}

    @classmethod
    def get_instance(cls) -> "ParserRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def register(cls, platform: Platform, parser_class: type[ConversationParser]):
        """注册解析器"""
        cls._parsers[platform.value] = parser_class

    @classmethod
    def get(cls, platform: Platform) -> type[ConversationParser]:
        """获取解析器类"""
        if platform.value not in cls._parsers:
            raise PlatformNotSupportedException(platform)
        return cls._parsers[platform.value]

    @classmethod
    def detect_platform(cls, url: str) -> Platform:
        """根据URL检测平台"""
        url_lower = url.lower()
        if "chatgpt.com" in url_lower:
            return Platform.CHATGPT
        elif "gemini.google" in url_lower or "gemini.google.com" in url_lower:
            return Platform.GEMINI
        elif "doubao.com" in url_lower:
            return Platform.DOUBAN
        raise PlatformNotSupportedException(url, [p.value for p in Platform])

    @classmethod
    def create_parser(cls, url: str) -> ConversationParser:
        """创建解析器实例"""
        platform = cls.detect_platform(url)
        parser_class = cls.get(platform)
        return parser_class()
```

**自动注册装饰器**：

```python
# 使用装饰器自动注册
def register_parser(platform: Platform):
    def decorator(cls: type[ConversationParser]):
        ParserRegistry.register(platform, cls)
        return cls
    return decorator

# 使用示例
@register_parser(Platform.CHATGPT)
class ChatGPTParser(BaseParser):
    ...
```

---

## 五、Repository 接口设计

```python
from abc import ABC, abstractmethod
from domain.model import Conversation, ExportTask, ImageResource

class ConversationRepository(ABC):
    """会话仓储接口"""
    @abstractmethod
    async def save(self, conversation: Conversation) -> Conversation:
        pass

    @abstractmethod
    async def find_by_id(self, id: str) -> Conversation | None:
        pass

    @abstractmethod
    async def find_by_platform_id(self, platform: str, platform_conversation_id: str) -> Conversation | None:
        pass

class ExportTaskRepository(ABC):
    """导出任务仓储接口"""
    @abstractmethod
    async def save(self, task: ExportTask) -> ExportTask:
        pass

    @abstractmethod
    async def find_by_id(self, id: str) -> ExportTask | None:
        pass

    @abstractmethod
    async def update_status(self, id: str, status: ExportTask.Status, **kwargs) -> ExportTask | None:
        pass

    @abstractmethod
    async def find_pending(self, limit: int = 10) -> list[ExportTask]:
        pass

class ImageRepository(ABC):
    """图片资源仓储接口"""
    @abstractmethod
    async def save(self, image: ImageResource) -> ImageResource:
        pass

    @abstractmethod
    async def find_by_id(self, id: str) -> ImageResource | None:
        pass

    @abstractmethod
    async def find_by_conversation_id(self, conversation_id: str) -> list[ImageResource]:
        pass
```

---

## 六、Exporter 接口设计

```python
from abc import ABC, abstractmethod
from pathlib import Path
from domain.model import KnowledgeDocument
from domain.service.interfaces import ExportResult

class ExporterInterface(ABC):
    """导出器统一接口"""
    @abstractmethod
    async def export(
        self,
        document: KnowledgeDocument,
        output_dir: Path,
        include_images: bool = True
    ) -> ExportResult:
        """导出会话文档"""
        pass

    @abstractmethod
    async def export_batch(
        self,
        documents: list[KnowledgeDocument],
        output_dir: Path,
        progress_callback: callable = None
    ) -> list[ExportResult]:
        """批量导出"""
        pass

class DownloaderInterface(ABC):
    """下载器统一接口"""
    @abstractmethod
    async def download(
        self,
        resource: ImageResource,
        output_dir: Path,
        overwrite: bool = False
    ) -> ImageResource:
        """下载单个资源"""
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

## 七、统一导出流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Unified Export Flow                                       │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────┐
                    │      ExportService  │
                    │   (Application)     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   ParserRegistry    │
                    │   (detect platform) │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   BaseParser.parse   │
                    │   <<template>>       │
                    ├─────────────────────┤
                    │ 1. fetch_page()     │
                    │ 2. extract_data()   │
                    │ 3. transform()      │
                    │ 4. download()       │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   ParserContext     │
                    │   (accumulated)     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │KnowledgeDocument    │
                    │   (Domain Model)    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   MarkdownExporter  │
                    │   (Infrastructure)  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   ExportResult      │
                    │   (output_path)     │
                    └─────────────────────┘
```

---

## 八、修订后项目目录结构

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
│   │   ├── task_service.py
│   │   ├── dto.py
│   │   └── mapper.py
│   │
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── model/
│   │   │   ├── __init__.py
│   │   │   ├── conversation.py
│   │   │   ├── block.py
│   │   │   ├── image_resource.py
│   │   │   ├── attachment.py
│   │   │   └── knowledge_document.py
│   │   ├── parser/
│   │   │   ├── __init__.py
│   │   │   ├── interface.py
│   │   │   ├── registry.py
│   │   │   ├── context.py
│   │   │   └── base.py
│   │   ├── repository/
│   │   │   ├── __init__.py
│   │   │   └── interfaces.py
│   │   └── service/
│   │       ├── __init__.py
│   │       └── interfaces.py
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
│   │   ├── repository/
│   │   │   ├── __init__.py
│   │   │   ├── in_memory_conversation_repo.py
│   │   │   └── in_memory_task_repo.py
│   │   ├── exporter/
│   │   │   ├── __init__.py
│   │   │   └── markdown_exporter.py
│   │   ├── downloader/
│   │   │   ├── __init__.py
│   │   │   └── aiohttp_downloader.py
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
│   │   │   ├── test_block.py
│   │   │   └── test_knowledge_document.py
│   │   ├── parser/
│   │   │   ├── __init__.py
│   │   │   ├── test_base_parser.py
│   │   │   ├── test_registry.py
│   │   │   └── test_chatgpt_parser.py
│   │   └── exporter/
│   │       ├── __init__.py
│   │       └── test_markdown_exporter.py
│   │
│   └── integration/
│       ├── __init__.py
│       ├── test_export_api.py
│       └── test_parsers.py
│
├── output/
├── static/
├── templates/
│
├── pyproject.toml
├── uv.lock
├── README.md
├── CLAUDE.md
└── .env.example
```

---

## 九、API 设计

### 9.1 请求/响应 DTO

```python
# schemas.py

class ExportRequest(BaseModel):
    url: str = Field(..., description="AI平台分享链接")

    class Config:
        json_schema_extra = {
            "example": {"url": "https://chatgpt.com/share/abc123"}
        }

class BatchExportRequest(BaseModel):
    urls: list[str] = Field(..., min_length=1, max_length=100)

    class Config:
        json_schema_extra = {
            "example": {"urls": [
                "https://chatgpt.com/share/abc123",
                "https://gemini.google.com/share/xyz789"
            ]}
        }

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str  # pending, parsing, downloading, exporting, completed, failed
    progress: float
    output_path: str | None = None
    error: str | None = None
    created_at: datetime
    completed_at: datetime | None = None

class ExportResponse(BaseModel):
    task_id: str
    status: str
    message: str

class DownloadResponse(BaseModel):
    task_id: str
    output_dir: str
    file_count: int
    image_count: int
    download_url: str  # 用于下载的临时URL或路径
```

### 9.2 API 路由

```python
# routes.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.api.schemas import (
    ExportRequest,
    BatchExportRequest,
    ExportResponse,
    TaskStatusResponse,
    DownloadResponse
)
from app.application.export_service import ExportService
from app.application.task_service import TaskService

router = APIRouter(prefix="/api/v1", tags=["export"])

@router.post("/export", response_model=ExportResponse)
async def export_conversation(
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    export_service: ExportService = Depends()
):
    """导出单个会话"""
    task = await export_service.create_export_task(request.url)
    background_tasks.add_task(export_service.execute_export, task.id)
    return ExportResponse(
        task_id=task.id,
        status=task.status.value,
        message="Export task created"
    )

@router.post("/export/batch", response_model=list[ExportResponse])
async def batch_export(
    request: BatchExportRequest,
    background_tasks: BackgroundTasks,
    export_service: ExportService = Depends()
):
    """批量导出多个会话"""
    tasks = await export_service.create_batch_export_tasks(request.urls)
    for task in tasks:
        background_tasks.add_task(export_service.execute_export, task.id)
    return [
        ExportResponse(task_id=t.id, status=t.status.value, message="Export task created")
        for t in tasks
    ]

@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    task_service: TaskService = Depends()
):
    """获取任务状态"""
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskStatusResponse(
        task_id=task.id,
        status=task.status.value,
        progress=task.progress,
        output_path=task.output_path,
        error=task.error,
        created_at=task.created_at,
        completed_at=task.completed_at
    )

@router.get("/download/{task_id}")
async def download_export(
    task_id: str,
    task_service: TaskService = Depends()
):
    """下载导出的文件"""
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != ExportTask.Status.COMPLETED:
        raise HTTPException(status_code=400, detail="Export not completed")
    # 返回文件或目录的下载链接
    return {"download_url": f"/files/{task.output_path}"}
```

### 9.3 OpenAPI 文档

```yaml
# 自动生成自 FastAPI
paths:
  /api/v1/export:
    post:
      summary: 导出单个会话
      tags: [export]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                url:
                  type: string
                  description: AI平台分享链接
      responses:
        '200':
          description: 任务创建成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ExportResponse'

  /api/v1/export/batch:
    post:
      summary: 批量导出会话
      tags: [export]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                urls:
                  type: array
                  items:
                    type: string
                  maxItems: 100
      responses:
        '200':
          description: 批量任务创建成功

  /api/v1/task/{task_id}:
    get:
      summary: 获取任务状态
      tags: [export]
      parameters:
        - name: task_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: 任务状态

  /api/v1/download/{task_id}:
    get:
      summary: 下载导出文件
      tags: [export]
      responses:
        '200':
          description: 下载链接
```

---

## 十、关键接口定义速查表

| 接口 | 层级 | 职责 |
|------|------|------|
| `ConversationParser.parse()` | Domain/Parser | 解析URL，返回Conversation |
| `ParserRegistry.create_parser()` | Domain/Parser | 根据URL创建解析器 |
| `ExporterInterface.export()` | Domain/Service | 导出KnowledgeDocument |
| `DownloaderInterface.download()` | Domain/Service | 下载ImageResource |
| `ConversationRepository` | Domain/Repository | 会话存储抽象 |
| `ExportTaskRepository` | Application | 任务存储抽象 |

---

**第二阶段文档结束**

主要变更：
- ExportTask 移至 Application 层
- 删除 Builder 模式，改用直接构造
- 引入 ParserRegistry 注册表模式
- Message 改为 Block 结构（支持 TEXT/CODE/TABLE/IMAGE/QUOTE/LIST）
- 新增 ParserContext 贯穿解析流程
- 新增 Repository 接口层（依赖倒置）
- 新增 KnowledgeDocument 领域模型

请确认后继续第三阶段：代码实现。