#!/usr/bin/env python3
"""
MCP SMS Partner Server for AJ8
API SMS française - https://www.smspartner.fr/
Documentation: https://docpartner.dev/
"""

import os
import json
import asyncio
import httpx
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

API_BASE_URL = "https://api.smspartner.fr/v1"
API_KEY = os.getenv("SMS_PARTNER_API_KEY", "")

server = Server("sms-partner")


async def api_request(method: str, endpoint: str, data: dict = None) -> dict:
    """Make API request to SMS Partner"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{API_BASE_URL}{endpoint}"
        
        if method == "GET":
            params = {"apiKey": API_KEY}
            if data:
                params.update(data)
            response = await client.get(url, params=params)
        else:
            payload = {"apiKey": API_KEY}
            if data:
                payload.update(data)
            response = await client.post(url, json=payload)
        
        return response.json()


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="sms_send",
            description="Envoyer un SMS à un numéro de téléphone français ou international",
            inputSchema={
                "type": "object",
                "properties": {
                    "phone": {
                        "type": "string",
                        "description": "Numéro de téléphone avec indicatif pays (ex: 33612345678 pour France)"
                    },
                    "message": {
                        "type": "string",
                        "description": "Contenu du SMS (160 caractères max pour 1 SMS, sinon concaténation)"
                    },
                    "sender": {
                        "type": "string",
                        "description": "Nom de l'expéditeur (11 caractères max, lettres/chiffres)",
                        "default": "AJ8"
                    }
                },
                "required": ["phone", "message"]
            }
        ),
        Tool(
            name="sms_send_bulk",
            description="Envoyer un SMS à plusieurs numéros en une seule requête",
            inputSchema={
                "type": "object",
                "properties": {
                    "phones": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Liste de numéros de téléphone avec indicatif pays"
                    },
                    "message": {
                        "type": "string",
                        "description": "Contenu du SMS"
                    },
                    "sender": {
                        "type": "string",
                        "description": "Nom de l'expéditeur (11 caractères max)",
                        "default": "AJ8"
                    }
                },
                "required": ["phones", "message"]
            }
        ),
        Tool(
            name="sms_credits",
            description="Vérifier le solde de crédits SMS disponibles",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="sms_status",
            description="Vérifier le statut d'un SMS envoyé par son ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_id": {
                        "type": "string",
                        "description": "ID du message retourné lors de l'envoi"
                    }
                },
                "required": ["message_id"]
            }
        ),
        Tool(
            name="sms_history",
            description="Récupérer l'historique des SMS envoyés",
            inputSchema={
                "type": "object",
                "properties": {
                    "from_date": {
                        "type": "string",
                        "description": "Date de début (format: dd/MM/yyyy)"
                    },
                    "to_date": {
                        "type": "string",
                        "description": "Date de fin (format: dd/MM/yyyy)"
                    },
                    "page": {
                        "type": "integer",
                        "description": "Numéro de page pour pagination",
                        "default": 1
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="sms_stop_list",
            description="Récupérer la liste des numéros en STOP (désabonnés)",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="sms_add_stop",
            description="Ajouter un numéro à la liste STOP (désabonnement)",
            inputSchema={
                "type": "object",
                "properties": {
                    "phone": {
                        "type": "string",
                        "description": "Numéro de téléphone à ajouter en STOP"
                    }
                },
                "required": ["phone"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    if not API_KEY:
        return [TextContent(type="text", text="Error: SMS_PARTNER_API_KEY not configured")]
    
    try:
        if name == "sms_send":
            result = await api_request("POST", "/send", {
                "phoneNumbers": arguments["phone"],
                "message": arguments["message"],
                "sender": arguments.get("sender", "AJ8"),
                "gamme": 1
            })
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]

        elif name == "sms_send_bulk":
            phones = ",".join(arguments["phones"])
            result = await api_request("POST", "/send", {
                "phoneNumbers": phones,
                "message": arguments["message"],
                "sender": arguments.get("sender", "AJ8"),
                "gamme": 1
            })
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]

        elif name == "sms_credits":
            result = await api_request("GET", "/me")
            if "credits" in result:
                return [TextContent(type="text", text=f"Crédits SMS disponibles: {result['credits']}\n\nDétails:\n{json.dumps(result, indent=2, ensure_ascii=False)}")]
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]

        elif name == "sms_status":
            result = await api_request("GET", "/message-status", {
                "messageId": arguments["message_id"]
            })
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]

        elif name == "sms_history":
            params = {}
            if "from_date" in arguments:
                params["from"] = arguments["from_date"]
            if "to_date" in arguments:
                params["to"] = arguments["to_date"]
            if "page" in arguments:
                params["page"] = arguments["page"]
            
            result = await api_request("GET", "/sms/list", params)
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]

        elif name == "sms_stop_list":
            result = await api_request("GET", "/stop-sms/list")
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]

        elif name == "sms_add_stop":
            result = await api_request("POST", "/stop-sms/add", {
                "phoneNumber": arguments["phone"]
            })
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except httpx.ConnectError:
        return [TextContent(type="text", text="Error: Cannot connect to SMS Partner API")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
