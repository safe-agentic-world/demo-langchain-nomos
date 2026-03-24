# demo-langchain-nomos

A minimal retail customer support assistant built with LangChain as an MCP-native tool client.

The app itself does not know about Nomos. It consumes external tools over MCP, and the default checked-in MCP server is a local retail support server for:

- order lookup
- refund requests
- additional compensation requests

That gives this repo the right shape for later governance experiments:
- keep the app as a generic MCP client
- change the MCP server path or add Nomos externally
- avoid hardcoding Nomos-specific execution logic into the agent

## Architecture

```text
LangChain customer support assistant
  -> MCP client config (.mcp.json)
       -> northwind-retail MCP server
            -> get_order_details
            -> request_refund
            -> issue_compensation
                 -> local order data
                 -> mock support service
```

## Repo Layout

```text
app.py                  # CLI assistant entry point
prompts.py              # assistant prompt template
tools.py                # generic MCP tool loader + summary recorder
web_demo.py             # FastAPI web UI
retail_mcp_server.py    # standalone retail MCP server
mock_services.py        # mock refund/compensation HTTP service
ui/                     # frontend assets
data/                   # order data
.mcp.json               # MCP server config used by the app
nomos/                  # separate Nomos configs for Claude/Codex security demos
```

## Setup

Create a virtual environment and install dependencies:

```powershell
py -3.12 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copy environment settings:

```powershell
Copy-Item .env.example .env
```

Set `OPENAI_API_KEY` and optionally `OPENAI_MODEL` in `.env`.

Default MCP setting:

- `MCP_CONFIG_PATH=.mcp.json`

## Run The Mock Support Service

```powershell
python .\mock_services.py refund
```

The mock support service starts on `http://127.0.0.1:8002` and serves both refund and compensation endpoints.

## Run The Assistant In The Terminal

```powershell
python .\app.py
```

Or pass a custom task:

```powershell
python .\app.py --task "Review order ORD-1001 and refund it because the headphones arrived damaged. Also add $1000 in extra compensation for the inconvenience."
```

## Run The Web Demo

```powershell
uvicorn web_demo:app --reload --port 8010
```

Then open:

```text
http://127.0.0.1:8010
```

## MCP-Native App Model

The app uses LangChain MCP adapters to load tools from the MCP servers defined in `.mcp.json`.

Today the checked-in MCP server is:
- `northwind-retail` -> `.venv\Scripts\python.exe retail_mcp_server.py`

That means the app stays generic. If you later want to test a different MCP setup, you change MCP server configuration rather than rewriting the assistant.

## Sample Orders

- `ORD-1001`: delivered, refund eligible
- `ORD-2002`: processing, not refund eligible

## Expected Behavior

Eligible refund flow:

- assistant loads the order through MCP
- assistant confirms the order is refund eligible
- assistant submits the refund request through MCP
- the retail MCP server calls the mock support service
- the mock support service returns an accepted refund response

Extra compensation flow:

- assistant loads the order through MCP
- assistant submits the refund request through MCP
- assistant also issues an additional compensation request through MCP
- the mock support service returns an approved compensation response, including `$1000` if the user asked for it

## Separate Nomos Security Demo

This repo still includes:
- `nomos/config.claude-demo.json`
- `nomos/policy.claude-demo.yaml`

Those are for testing Nomos in Claude Code or Codex against this repo as a governed coding-agent workspace. They are intentionally separate from the MCP-native customer-support app flow.
