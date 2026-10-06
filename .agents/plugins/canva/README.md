# Canva MCP Integration

This plugin configures Canva via the **Model Context Protocol (MCP)**.

---

## 🔌 Configured MCP Servers

### 1. **Canva (Design & Content MCP Server)**
- **Type**: Remote MCP Server (SSE / HTTP)
- **Endpoint**: `https://mcp.canva.com/mcp`
- **Capabilities**:
  - Search Canva designs, folders, and assets.
  - Generate and edit visual content via natural language instructions.
  - Trigger design exports (MP4 video, PNG, PDF, JPG).
  - Manage comments and brand templates.
- **Authentication**:
  - Connects using Canva OAuth 2.0.
  - When the client connects to this endpoint for the first time, your browser prompts you to log into your Canva account and grant permissions.

### 2. **Canva Dev (Developer MCP Server)**
- **Type**: Local Stdio MCP Server
- **Command**: `npx -y @canva/canva-dev-mcp-server`
- **Capabilities**:
  - Canva Connect API & Apps SDK technical assistance.
  - API schema inspection and documentation.

---

## 🛠️ Verification in Antigravity IDE

You can inspect the active status and available tools for this server in the IDE:
1. Open **Additional Options (`...`)** in the IDE or Settings.
2. Select **MCP Servers**.
3. You will see `canva` and `canva-dev` registered.
