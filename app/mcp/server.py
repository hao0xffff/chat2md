"""MCP server for Chat2MD - exposes export as an MCP tool."""
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, JSONRPCError

from app.api.dependencies import container
from app.config.settings import settings
from app.domain.parser.registry import ParserRegistry

import app.infrastructure.parser  # noqa: F401


# Create the MCP server instance
server = Server("chat2md")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """
    List available tools from this server.

    Returns a list of Tool objects that describe the available functions.
    """
    return [
        Tool(
            name="export_chat_to_markdown",
            description="Export an AI chat share link (ChatGPT, Gemini, Doubao) to a Markdown file. "
                        "Parses the conversation, downloads images, and outputs a structured markdown document.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The AI platform share link URL. "
                                     "Examples: https://chatgpt.com/share/xxx, "
                                     "https://gemini.google.com/share/xxx"
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Optional output directory path. "
                                     "Defaults to the project's output directory."
                    },
                    "format": {
                        "type": "string",
                        "enum": ["ai_readable", "transcript", "compact"],
                        "description": "Markdown output format. Defaults to ai_readable."
                    },
                    "include_images": {
                        "type": "boolean",
                        "description": "Download and reference images. Defaults to true."
                    },
                    "include_metadata": {
                        "type": "boolean",
                        "description": "Include metadata and source fields. Defaults to true."
                    },
                    "create_index": {
                        "type": "boolean",
                        "description": "Create index.md. Defaults to true."
                    },
                    "create_manifest": {
                        "type": "boolean",
                        "description": "Create manifest.md. Defaults to true."
                    },
                    "create_messages": {
                        "type": "boolean",
                        "description": "Create messages.md. Defaults to true."
                    }
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="get_export_status",
            description="Get the status of an export task by task ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "The task ID returned from export_chat_to_markdown"
                    }
                },
                "required": ["task_id"]
            }
        ),
        Tool(
            name="list_supported_platforms",
            description="List all AI platforms currently supported for export.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """
    Handle tool calls from MCP clients.

    Args:
        name: The name of the tool to call.
        arguments: The arguments to pass to the tool.

    Returns:
        A list of TextContent objects with the results.
    """
    if name == "export_chat_to_markdown":
        return await _export_chat_to_markdown(arguments)
    elif name == "get_export_status":
        return await _get_export_status(arguments)
    elif name == "list_supported_platforms":
        return _list_supported_platforms()
    else:
        raise JSONRPCError(code=-32601, message=f"Unknown tool: {name}")


async def _export_chat_to_markdown(args: dict[str, Any]) -> list[TextContent]:
    """Execute the export tool."""
    url: str = args["url"]
    output_dir: str | None = args.get("output_dir")

    service = container.export_service()
    option_keys = {
        "format",
        "include_images",
        "include_metadata",
        "include_frontmatter",
        "create_index",
        "create_manifest",
        "create_messages",
        "file_basename",
    }
    options = {key: args[key] for key in option_keys if key in args}

    # Create task and execute
    task = await service.create_export_task(url, output_dir, options)
    result = await service.execute_export(task.id)

    if result.is_failed:
        return [TextContent(
            type="text",
            text=f"Export failed: {result.error}"
        )]

    return [TextContent(
        type="text",
        text=f"Successfully exported to: {result.output_path}\n"
             f"Messages: {result.message_count}, Images: {result.image_count}"
    )]


async def _get_export_status(args: dict[str, Any]) -> list[TextContent]:
    """Get export task status."""
    task_id: str = args["task_id"]

    service = container.task_service()
    try:
        status = await service.get_task_status(task_id)
        return [TextContent(
            type="text",
            text=f"Task {task_id}: {status.status}\n"
                 f"Progress: {status.progress}%\n"
                 f"Output: {status.output_path or 'N/A'}"
        )]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


def _list_supported_platforms() -> list[TextContent]:
    """List supported platforms."""
    lines = ["Supported platforms:"]
    for platform in ParserRegistry.available_platforms():
        if platform["enabled"] and platform["registered"]:
            patterns = ", ".join(platform["patterns"])
            lines.append(f"  - {platform['id']} ({patterns})")
    return [TextContent(
        type="text",
        text="\n".join(lines)
    )]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
