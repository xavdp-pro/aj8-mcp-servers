#!/usr/bin/env python3
"""
MCP WhatsApp Server for AJ8
Uses Baileys bridge for WhatsApp Web API
Supports: text messages, images, videos, documents, voice notes (ptt)
"""

import os
import json
import asyncio
import httpx
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

BAILEYS_URL = os.getenv("BAILEYS_URL", "http://localhost:3033")
DOWNLOADS_DIR = os.path.join(os.path.dirname(__file__), "downloads")

server = Server("whatsapp")


async def call_baileys(method: str, endpoint: str, data: dict = None) -> dict:
    """Call Baileys REST API"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{BAILEYS_URL}{endpoint}"
        if method == "GET":
            response = await client.get(url, params=data)
        else:
            response = await client.post(url, json=data)
        return response.json()


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="whatsapp_status",
            description="Get WhatsApp connection status and QR code if pending",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="whatsapp_send_message",
            description="Send a text message to a WhatsApp number or group",
            inputSchema={
                "type": "object",
                "properties": {
                    "phone": {
                        "type": "string",
                        "description": "Phone number with country code (e.g., 33612345678) or group JID"
                    },
                    "message": {
                        "type": "string",
                        "description": "Text message to send"
                    }
                },
                "required": ["phone", "message"]
            }
        ),
        Tool(
            name="whatsapp_send_media",
            description="Send media (image, video, audio, document) to WhatsApp",
            inputSchema={
                "type": "object",
                "properties": {
                    "phone": {
                        "type": "string",
                        "description": "Phone number with country code or group JID"
                    },
                    "media_path": {
                        "type": "string",
                        "description": "Local path to the media file"
                    },
                    "media_type": {
                        "type": "string",
                        "enum": ["image", "video", "audio", "document"],
                        "description": "Type of media"
                    },
                    "caption": {
                        "type": "string",
                        "description": "Optional caption for image/video"
                    }
                },
                "required": ["phone", "media_path", "media_type"]
            }
        ),
        Tool(
            name="whatsapp_send_voice",
            description="Send a voice note (PTT - Push To Talk) to WhatsApp",
            inputSchema={
                "type": "object",
                "properties": {
                    "phone": {
                        "type": "string",
                        "description": "Phone number with country code or group JID"
                    },
                    "audio_path": {
                        "type": "string",
                        "description": "Path to audio file (will be sent as voice note)"
                    }
                },
                "required": ["phone", "audio_path"]
            }
        ),
        Tool(
            name="whatsapp_list_chats",
            description="List all WhatsApp group chats",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="whatsapp_list_downloads",
            description="List all downloaded media files (images, voice notes, etc.)",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="whatsapp_get_voice_notes",
            description="Get all downloaded voice notes (.ogg files) for transcription",
            inputSchema={
                "type": "object",
                "properties": {
                    "chat_filter": {
                        "type": "string",
                        "description": "Optional: filter by chat ID substring"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="whatsapp_register_webhook",
            description="Register a webhook URL to receive incoming messages in real-time",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Webhook URL to receive POST requests with messages"
                    }
                },
                "required": ["url"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    try:
        if name == "whatsapp_status":
            result = await call_baileys("GET", "/status")
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "whatsapp_send_message":
            result = await call_baileys("POST", "/send", {
                "phone": arguments["phone"],
                "message": arguments["message"]
            })
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "whatsapp_send_media":
            result = await call_baileys("POST", "/send", {
                "phone": arguments["phone"],
                "mediaPath": arguments["media_path"],
                "mediaType": arguments["media_type"],
                "message": arguments.get("caption", "")
            })
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "whatsapp_send_voice":
            result = await call_baileys("POST", "/send", {
                "phone": arguments["phone"],
                "mediaPath": arguments["audio_path"],
                "mediaType": "audio"
            })
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "whatsapp_list_chats":
            result = await call_baileys("GET", "/chats")
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "whatsapp_list_downloads":
            files = []
            if os.path.exists(DOWNLOADS_DIR):
                for f in os.listdir(DOWNLOADS_DIR):
                    filepath = os.path.join(DOWNLOADS_DIR, f)
                    files.append({
                        "filename": f,
                        "path": filepath,
                        "size": os.path.getsize(filepath),
                        "is_voice": f.endswith('.ogg')
                    })
            return [TextContent(type="text", text=json.dumps(files, indent=2))]

        elif name == "whatsapp_get_voice_notes":
            voice_notes = []
            if os.path.exists(DOWNLOADS_DIR):
                for f in os.listdir(DOWNLOADS_DIR):
                    if f.endswith('.ogg'):
                        filepath = os.path.join(DOWNLOADS_DIR, f)
                        voice_notes.append({
                            "filename": f,
                            "path": filepath,
                            "size": os.path.getsize(filepath),
                            "ready_for_transcription": True
                        })
            return [TextContent(type="text", text=json.dumps(voice_notes, indent=2))]

        elif name == "whatsapp_register_webhook":
            result = await call_baileys("POST", "/webhook/register", {
                "url": arguments["url"]
            })
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except httpx.ConnectError:
        return [TextContent(type="text", text="Error: Cannot connect to Baileys server. Make sure it's running on port 3033")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
