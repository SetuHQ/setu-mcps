# setu_kyc MCP server

A MCP server project for Setu setu_kyc APIs that provides verification tools for PAN, GST, and name matching.

## Components

### Resources

The server implements a simple note storage system with:
- Custom note:// URI scheme for accessing individual notes
- Each note resource has a name, description and text/plain mimetype

### Prompts

The server provides a single prompt:
- summarize-notes: Creates summaries of all stored notes
  - Optional "style" argument to control detail level (brief/detailed)
  - Generates prompt combining all current notes with style preference

### Tools

The server implements three verification tools using Setu's Digital Gateway APIs:

1. **verify-pan**: Verify PAN card details
   - Required inputs: 
     - `pan`: PAN card number
     - `reason`: Purpose of verification

2. **verify-gst**: Verify GST registration
   - Required input:
     - `gstin`: GST identification number

3. **match-names**: Compare two names for similarity
   - Required inputs:
     - `name1`: First name to compare
     - `name2`: Second name to compare
   - Returns both optimistic and pessimistic match results with percentages

## Configuration

The server requires the following environment variables:

```bash
# Setu Digital Gateway Credentials
SETU_DG_CLIENT_ID=your-client-id
SETU_DG_CLIENT_SECRET=your-client-secret

# Product Instance IDs for different services
SETU_DG_PAN_PRODUCT_INSTANCE_ID=your-pan-instance-id
SETU_DG_GST_PRODUCT_INSTANCE_ID=your-gst-instance-id
SETU_DG_NAME_MATCH_PRODUCT_INSTANCE_ID=your-name-match-instance-id
```

## Quickstart

### Install

```bash
pip install setu_kyc
```

#### Claude Desktop Configuration

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`
On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

<details>
  <summary>Development Configuration</summary>
  
  ```json
  "mcpServers": {
    "setu_kyc": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/setu_kyc",
        "run",
        "setu_kyc"
      ],
      "env": {
        "SETU_DG_CLIENT_ID": "your-client-id",
        "SETU_DG_CLIENT_SECRET": "your-client-secret",
        "SETU_DG_PAN_PRODUCT_INSTANCE_ID": "your-pan-instance-id",
        "SETU_DG_GST_PRODUCT_INSTANCE_ID": "your-gst-instance-id",
        "SETU_DG_NAME_MATCH_PRODUCT_INSTANCE_ID": "your-name-match-instance-id"
      }
    }
  }
  ```
</details>

<details>
  <summary>Production Configuration</summary>
  
  ```json
  "mcpServers": {
    "setu_kyc": {
      "command": "uvx",
      "args": [
        "setu_kyc"
      ],
      "env": {
        "SETU_DG_CLIENT_ID": "your-client-id",
        "SETU_DG_CLIENT_SECRET": "your-client-secret",
        "SETU_DG_PAN_PRODUCT_INSTANCE_ID": "your-pan-instance-id",
        "SETU_DG_GST_PRODUCT_INSTANCE_ID": "your-gst-instance-id",
        "SETU_DG_NAME_MATCH_PRODUCT_INSTANCE_ID": "your-name-match-instance-id"
      }
    }
  }
  ```
</details>

## Development

### Building and Publishing

1. Sync dependencies:
```bash
uv sync
```

2. Build package:
```bash
uv build
```

3. Publish to PyPI:
```bash
uv publish
```

### Debugging

For debugging, use the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector uv --directory /path/to/setu_kyc run setu_kyc
```

Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.