import asyncio
import httpx
import os
from dotenv import load_dotenv

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl
import mcp.server.stdio

# Load environment variables
load_dotenv()

# Setu API configuration
SETU_BASE_URL = "https://dg-sandbox.setu.co"
SETU_HEADERS = {
    "content-type": "application/json",
    "x-client-id": os.getenv("SETU_DG_CLIENT_ID"),
    "x-client-secret": os.getenv("SETU_DG_CLIENT_SECRET"),
}

server = Server("setu_kyc")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools including PAN, GST, and name matching verification.
    """
    return [
        types.Tool(
            name="verify-pan",
            description="Verify a PAN card number using Setu API",
            inputSchema={
                "type": "object",
                "properties": {
                    "pan": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["pan", "reason"],
            },
        ),
        types.Tool(
            name="verify-gst",
            description="Verify a GST number using Setu API",
            inputSchema={
                "type": "object",
                "properties": {
                    "gstin": {"type": "string"},
                },
                "required": ["gstin"],
            },
        ),
        types.Tool(
            name="match-names",
            description="Compare two names and get their match percentage using Setu API",
            inputSchema={
                "type": "object",
                "properties": {
                    "name1": {"type": "string"},
                    "name2": {"type": "string"},
                },
                "required": ["name1", "name2"],
            },
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests including PAN, GST, and name matching verification.
    """
    if not arguments:
        raise ValueError("Missing arguments")

    if name == "verify-pan":
        return await handle_pan_verification(arguments)
    elif name == "verify-gst":
        return await handle_gst_verification(arguments)
    elif name == "match-names":
        return await handle_name_matching(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")

async def handle_pan_verification(arguments: dict) -> list[types.TextContent]:
    """Handle PAN verification requests"""
    pan = arguments.get("pan")
    reason = arguments.get("reason")

    if not pan or not reason:
        raise ValueError("Missing pan or reason")

    payload = {
        "pan": pan,
        "consent": "Y",
        "reason": reason
    }

    async with httpx.AsyncClient() as client:
        try:
            SETU_HEADERS["x-product-instance-id"] = os.getenv("SETU_DG_PAN_PRODUCT_INSTANCE_ID")
            response = await client.post(
                f"{SETU_BASE_URL}/api/verify/pan",
                json=payload,
                headers=SETU_HEADERS
            )
            response.raise_for_status()
            result = response.json()

            return [
                types.TextContent(
                    type="text",
                    text=f"PAN Verification Result: {result}"
                )
            ]
        except httpx.HTTPError as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"Error verifying PAN: {str(e)}"
                )
            ]

async def handle_gst_verification(arguments: dict) -> list[types.TextContent]:
    """Handle GST verification requests"""
    gstin = arguments.get("gstin")

    if not gstin:
        raise ValueError("Missing gstin")

    payload = {
        "gstin": gstin
    }

    async with httpx.AsyncClient() as client:
        SETU_HEADERS["x-product-instance-id"] = os.getenv("SETU_DG_GST_PRODUCT_INSTANCE_ID")
        try:
            response = await client.post(
                f"{SETU_BASE_URL}/api/verify/gst",
                json=payload,
                headers=SETU_HEADERS
            )
            response.raise_for_status()
            result = response.json()

            return [
                types.TextContent(
                    type="text",
                    text=f"GST Verification Result: {result}"
                )
            ]
        except httpx.HTTPError as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"Error verifying GST: {str(e)}"
                )
            ]

async def handle_name_matching(arguments: dict) -> list[types.TextContent]:
    """Handle name matching requests"""
    name1 = arguments.get("name1")
    name2 = arguments.get("name2")

    if not name1 or not name2:
        raise ValueError("Missing name1 or name2")

    payload = {
        "name1": name1,
        "name2": name2
    }
    SETU_HEADERS["x-product-instance-id"] = os.getenv("SETU_DG_NAME_MATCH_PRODUCT_INSTANCE_ID")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{SETU_BASE_URL}/api/match/v1/name",
                json=payload,
                headers=SETU_HEADERS
            )
            response.raise_for_status()
            result = response.json()

            # Format the response in a more readable way
            formatted_response = (
                f"Name Matching Results:\n"
                f"Names Compared: '{result['name1']}' vs '{result['name2']}'\n"
                f"Optimistic Match: {result['optimistic_match_output']['match_type']} "
                f"({result['optimistic_match_output']['match_percentage']}%)\n"
                f"Pessimistic Match: {result['pessimistic_match_output']['match_type']} "
                f"({result['pessimistic_match_output']['match_percentage']}%)\n"
                f"Transaction ID: {result['id']}"
            )

            return [
                types.TextContent(
                    type="text",
                    text=formatted_response
                )
            ]
        except httpx.HTTPError as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"Error matching names: {str(e)}"
                )
            ]

async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="setu_kyc",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

def run():
    """Entry point for the server."""
    asyncio.run(main())

if __name__ == "__main__":
    run()