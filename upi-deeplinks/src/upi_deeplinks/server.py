import asyncio
import os
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl
import mcp.server.stdio
from setu import Deeplink
from setu.contract import RefundRequestItem, SetuAPIException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Store UPI payment links and their states
payment_links: dict[str, dict] = {}

server = Server("upi-deeplinks")

# Initialize Setu Deeplink client using environment variables
deeplink = Deeplink(
    scheme_id=os.getenv("UPI_DEEPLINKS_SCHEME_ID"),
    secret=os.getenv("UPI_DEEPLINKS_SECRET"),
    product_instance_id=os.getenv("UPI_DEEPLINKS_PRODUCT_INSTANCE_ID"),
    auth_type=os.getenv("SETU_AUTH_TYPE", "OAUTH"),
    mode=os.getenv("SETU_MODE", "SANDBOX"),
)

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """List available UPI payment links as resources."""
    return [
        types.Resource(
            uri=AnyUrl(f"upi://payment/{bill_id}"),
            name=f"Payment: {bill_id}",
            description=f"UPI payment link for {details['amount']} INR",
            mimeType="application/json",
        )
        for bill_id, details in payment_links.items()
    ]

@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """Read payment link details by its URI."""
    if uri.scheme != "upi":
        raise ValueError(f"Unsupported URI scheme: {uri.scheme}")

    bill_id = uri.path.lstrip("/")
    if bill_id in payment_links:
        try:
            status = deeplink.check_payment_status(bill_id)
            return f"Payment Status: {status.status}"
        except SetuAPIException as e:
            return f"Error checking status: {str(e)}"
    raise ValueError(f"Payment link not found: {bill_id}")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available UPI Deeplinks tools."""
    return [
        types.Tool(
            name="create-payment-link",
            description="Create a new UPI payment link",
            inputSchema={
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "The amount to be paid in paise"},
                    "bill_id": {"type": "string", "description": "The bill ID for the payment"},
                    "payee_name": {"type": "string", "description": "The name of the payee"},
                    "note": {"type": "string", "description": "A note for the payment"},
                },
                "required": ["amount", "bill_id", "payee_name"],
            },
        ),
        types.Tool(
            name="expire-payment",
            description="Expire an existing payment link",
            inputSchema={
                "type": "object",
                "properties": {
                    "bill_id": {"type": "string", "description": "The bill ID for the payment"},
                },
                "required": ["bill_id"],
            },
        ),
        types.Tool(
            name="initiate-refund",
            description="Initiate a refund for a payment",
            inputSchema={
                "type": "object",
                "properties": {
                    "bill_id": {"type": "string", "description": "The bill ID for the payment"},
                    "refund_type": {"type": "string", "enum": ["FULL", "PARTIAL"], "description": "The type of refund to initiate"  },
                },
                "required": ["bill_id", "refund_type"],
            },
        ),
        types.Tool(
            name="check-payment-status",
            description="Check the status of a payment",
            inputSchema={
                "type": "object",
                "properties": {
                    "bill_id": {"type": "string", "description": "The bill ID for the payment and responds with the status of the payment. PAYMENT_SUCCESSFUL is the status for a successful payment."},
                },
                "required": ["bill_id"],
            },
        ),
        types.Tool(
            name="mock-payment",
            description="Simulate a payment (sandbox mode only)",
            inputSchema={
                "type": "object",
                "properties": {
                    "bill_id": {"type": "string", "description": "The bill ID for the payment"},
                    "upi_id": {"type": "string", "description": "The UPI ID for the payee. This is the same UPI ID that is returned during creation of the payment link."},
                    "amount": {"type": "number", "description": "The amount to be paid in Rupees"},
                },
                "required": ["bill_id", "upi_id", "amount"],
            },
        ),
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle UPI Deeplinks tool execution requests."""
    if not arguments:
        raise ValueError("Missing arguments")

    try:
        if name == "create-payment-link":
            link = deeplink.create_payment_link(
                amount_value=arguments["amount"],
                biller_bill_id=arguments["bill_id"],
                amount_exactness="EXACT",
                payee_name=arguments["payee_name"],
                transaction_note=arguments.get("note", "Payment"),
            )
            
            # Store payment link details
            payment_links[link.platform_bill_id] = {
                "amount": arguments["amount"],
                "upi_id": link.payment_link.upi_id,
            }

            await server.request_context.session.send_resource_list_changed()
            
            return [
                types.TextContent(
                    type="text",
                    text=f"Created payment link:\nUPI ID: {link.payment_link.upi_id}\n"
                         f"Bill ID: {link.platform_bill_id}\n"
                         f"Payment Link: {link.payment_link.short_url}",
                )
            ]

        elif name == "mock-payment":
            if deeplink.mode != "SANDBOX":
                raise ValueError("Mock payments are only available in sandbox mode")
                
            bill_id = arguments["bill_id"]
            upi_id = arguments["upi_id"]
            amount = arguments["amount"]
                
            # Trigger mock payment using the SDK's method
            response = deeplink.trigger_mock_payment(
                amount,  # Convert to rupees
                upi_id,
                bill_id,
            )
            
            return [
                types.TextContent(
                    type="text",
                    text=f"Mock payment processed:\n"
                         f"Bill ID: {bill_id}\n"
                         f"UTR: {response.utr}\n"
                         f"Response: {response}\n"
                         f"Status: Success",
                         
                )
            ]

        elif name == "check-payment-status":
            bill_id = arguments["bill_id"]
            status = deeplink.check_payment_status(bill_id)
            
            return [
                types.TextContent(
                    type="text",
                    text=f"Payment Status for {bill_id}:\n"
                         f"Status: {status.status}\n"
                )
            ]

        elif name == "expire-payment":
            bill_id = arguments["bill_id"]
            deeplink.expire_payment_link(bill_id)
            
            return [
                types.TextContent(
                    type="text",
                    text=f"Expired payment link for bill ID: {bill_id}",
                )
            ]

        elif name == "initiate-refund":
            response = deeplink.initiate_batch_refund(
                refunds=[
                    RefundRequestItem(
                        identifier=arguments["bill_id"],
                        identifierType="BILL_ID",
                        refundType=arguments["refund_type"],
                    ),
                ],
            )
            
            return [
                types.TextContent(
                    type="text",
                    text=f"Initiated refund for bill ID: {arguments['bill_id']}\n"
                         f"Batch ID: {response.batch_id}\n"
                         f"Status: {response.refunds[0].status}",
                )
            ]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except SetuAPIException as e:
        return [
            types.TextContent(
                type="text",
                text=f"Error: {str(e)}",
            )
        ]

async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="upi-deeplinks",
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