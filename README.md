# Chat2MD

AI Conversation Export System - Export chat sessions from various AI platforms to Markdown.

## Features

- Parse share links from multiple AI platforms (ChatGPT, Gemini, Doubao)
- Export conversations to well-formatted Markdown
- Download and embed images
- Batch export support
- RESTful API with FastAPI

## Architecture

See `docs/` for detailed architecture documentation.

## Setup

```bash
# Install dependencies
uv sync

# Run the application
uv run python -m app.main
```

## API Endpoints

- `POST /api/v1/export` - Export single conversation
- `POST /api/v1/export/batch` - Batch export
- `GET /api/v1/task/{task_id}` - Get task status
- `GET /api/v1/download/{task_id}` - Download exported files

## Testing

```bash
uv run pytest tests/
```