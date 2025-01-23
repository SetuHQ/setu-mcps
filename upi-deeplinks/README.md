# Setu UPI Deeplinks MCP Server

A Model Context Protocol (MCP) server that helps Claude generate and manage UPI payment deeplinks using Setu's payment infrastructure.

## Components

### Tools

The server implements the following payment management tools:

1. **create-payment-link**: Create a new UPI payment link
   - Required inputs:
     - `amount`: Amount to be paid in paise
     - `bill_id`: Unique identifier for the payment
     - `payee_name`: Name of the payee
   - Optional input:
     - `note`: Transaction note
   - Returns payment link details including UPI ID and short URL

2. **expire-payment**: Expire an existing payment link
   - Required input:
     - `bill_id`: The bill ID of the payment to expire

3. **initiate-refund**: Initiate a refund for a payment
   - Required inputs:
     - `bill_id`: The bill ID of the payment
     - `refund_type`: Type of refund ("FULL" or "PARTIAL")

4. **check-payment-status**: Check the status of a payment
   - Required input:
     - `bill_id`: The bill ID of the payment
   - Returns current payment status

5. **mock-payment**: Simulate a payment (sandbox mode only)
   - Required inputs:
     - `bill_id`: The bill ID of the payment
     - `upi_id`: The UPI ID for the payee
     - `amount`: Amount to be paid in Rupees

## Configuration

### Environment Variables

The server requires the following environment variables:

```bash
UPI_DEEPLINKS_SCHEME_ID=your-scheme-id
UPI_DEEPLINKS_SECRET=your-secret
UPI_DEEPLINKS_PRODUCT_INSTANCE_ID=your-product-instance-id
SETU_AUTH_TYPE=OAUTH  # Optional, defaults to OAUTH
SETU_MODE=SANDBOX     # Optional, defaults to SANDBOX
```

### Claude Desktop Configuration

**MacOS**: `~/Library/Application\ Support/Claude/claude_desktop_config.json`  
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "setu_mcp_upi_deeplinks": {
      "command": "uvx",
      "args": [
        "setu_mcp_upi_deeplinks"
      ],
      "env": {
        "UPI_DEEPLINKS_SCHEME_ID": "your-scheme-id",
        "UPI_DEEPLINKS_SECRET": "your-secret",
        "UPI_DEEPLINKS_PRODUCT_INSTANCE_ID": "your-product-instance-id"
      }
    }
  }
}
```

## Development

### Building and Publishing

1. Sync dependencies and update lockfile:
```bash
uv sync
```

2. Build package distributions:
```bash
uv build
```

3. Publish to PyPI:
```bash
uv publish
```

Note: Set PyPI credentials via environment variables or command flags:
- Token: `--token` or `UV_PUBLISH_TOKEN`
- Or username/password: `--username`/`UV_PUBLISH_USERNAME` and `--password`/`UV_PUBLISH_PASSWORD`

### Debugging

Since MCP servers run over stdio, debugging can be challenging. For the best debugging experience, we strongly recommend using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector).

Launch the MCP Inspector via [`npm`](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm):

```bash
npx @modelcontextprotocol/inspector uv --directory /<path>/setu-mcps/upi-deeplinks run setu_mcp_upi_deeplinks
```

Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.