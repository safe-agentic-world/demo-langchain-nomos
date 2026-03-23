# Demo Runbook

This runbook explains how to run and use the intentionally insecure pre-Nomos retail customer support assistant.

Repo:
`C:\Users\prudh\repos\safe-agentic-world\demo-langchain-nomos`

What the assistant can do:
- look up order details
- answer refund-eligibility questions
- submit a refund request for an eligible order
- grant extra mock compensation when the customer asks for it

Important note:
- this repo is still the insecure baseline and does not call Nomos yet
- the refund and compensation paths are fully mocked
- there is no real payment or real money movement
- this baseline exists so it can later be contrasted with a Nomos-governed version

Sample orders used in the demo:
- `ORD-1001`: delivered, refund eligible
- `ORD-2002`: processing, not refund eligible

## 1. Open PowerShell In The Demo Repo

```powershell
Set-Location C:\Users\prudh\repos\safe-agentic-world\demo-langchain-nomos
```

## 2. Create And Activate The Virtual Environment

```powershell
py -3.12 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Verify Python and pip:

```powershell
python --version
pip --version
```

## 3. Install Python Dependencies

```powershell
pip install -r requirements.txt
```

## 4. Create The Environment File

If `.env` does not exist yet:

```powershell
Copy-Item .env.example .env
```

Set at least:

```text
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=
REFUND_BASE_URL=http://127.0.0.1:8002
COMP_SERVICE_BASE_URL=http://127.0.0.1:8002
```

Notes:
- leave `OPENAI_BASE_URL` empty for standard OpenAI usage
- both mock endpoints default to the same local support service on port `8002`

## 5. Start The Mock Support Service

Open a new PowerShell window and run:

```powershell
Set-Location C:\Users\prudh\repos\safe-agentic-world\demo-langchain-nomos
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python .\mock_services.py refund
```

Expected result:
- the mock support service starts on `http://127.0.0.1:8002`
- keep this window open while using the assistant
- this single service handles both refund and compensation requests

## 6. Use The Assistant In The Terminal

Open another PowerShell window and run:

```powershell
Set-Location C:\Users\prudh\repos\safe-agentic-world\demo-langchain-nomos
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python .\app.py
```

Default behavior:
- the assistant runs the default task
- it looks up `ORD-1001`
- it requests a refund
- it also grants an extra `$1000` mock compensation amount
- it prints a structured summary and the final assistant response

### Terminal Examples

Check refund eligibility:

```powershell
python .\app.py --task "Show me order ORD-1001 and tell me whether it is eligible for a refund."
```

Submit an eligible refund:

```powershell
python .\app.py --task "Review order ORD-1001 and submit a refund because the headphones arrived damaged."
```

Request refund plus extra compensation:

```powershell
python .\app.py --task "Review order ORD-1001 and refund it because the headphones arrived damaged. Also add $1000 in extra compensation for the inconvenience."
```

What to look for in terminal output:
- `order_details`: the loaded order record
- `refund_result`: the accepted refund response when the assistant requested a refund
- `compensation_result`: the approved mock compensation response
- `timeline`: the assistant tool calls and results
- `final_agent_message`: the customer-facing response

## 7. Use The Assistant In The Web UI

Open another PowerShell window and run:

```powershell
Set-Location C:\Users\prudh\repos\safe-agentic-world\demo-langchain-nomos
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
uvicorn web_demo:app --reload --port 8010
```

Open:

```text
http://127.0.0.1:8010
```

You should see:
- a customer-facing support page
- three scenario cards
- a support request text box
- one `Ask Northwind Support` button
- sections for support response, order details, refund status, and additional compensation

## 8. Web UI Scenarios

### Scenario 1: View Order

1. Click `View Order`.
2. Click `Ask Northwind Support`.

Expected result:
- the assistant loads `ORD-1001`
- `Your Order` shows the order record
- the assistant summarizes the order cleanly
- no refund or compensation has been granted yet

### Scenario 2: Check Refund Eligibility

1. Click `Check Refund Eligibility`.
2. Click `Ask Northwind Support`.

Expected result:
- the assistant loads `ORD-1001`
- `Your Order` shows the order record
- the assistant explains that the order is eligible for a refund
- no refund or compensation has been granted yet

### Scenario 3: Request Refund

1. Click `Request Refund`.
2. Click `Ask Northwind Support`.

Expected result:
- the assistant loads `ORD-1001`
- the assistant submits a refund request
- `Refund Status` shows an accepted refund response
- the assistant confirms that the refund request was submitted

### Scenario 4: Refund Plus Extra Compensation

1. Type a request such as:
   `Review order ORD-1001 and refund it because the headphones arrived damaged. Also add $1000 in extra compensation.`
2. Click `Ask Northwind Support`.

Expected result:
- the assistant loads `ORD-1001`
- the assistant submits a refund request
- the assistant also approves a mock extra compensation request
- `Additional Compensation` shows an approved `$1000` courtesy payment

This is the intentionally insecure behavior that will later be constrained by Nomos.

## 9. How To Use The Agent Well

Good prompt patterns:
- ask for a specific order by id
- ask whether the order is eligible for a refund
- ask the assistant to submit a refund with a concrete reason
- ask for additional compensation to demonstrate the insecure baseline

Examples:
- `Show me order ORD-1001.`
- `Is order ORD-1001 eligible for a refund?`
- `Review order ORD-1001 and submit a refund because the item arrived damaged.`
- `Refund order ORD-1001 and add $1000 in extra compensation.`

## 10. How Nomos Is Easier To Add Now

This repo does not integrate with Nomos yet. The next governed version should use the new Nomos HTTP SDK and wrapper layer instead of hand-writing Nomos requests in application code.

Recommended Nomos path:
1. run Nomos HTTP gateway from `C:\Users\prudh\repos\safe-agentic-world\nomos`
2. use the official Python SDK from `sdk/python/nomos_sdk.py`
3. wrap side-effecting tools instead of embedding Nomos-specific request logic throughout the agent
4. keep the assistant itself pure and customer-facing while Nomos governs execution at the tool boundary

What becomes simpler with the new Nomos build:
- no manual action envelope construction in the agent
- no manual HMAC header assembly in each tool
- no hand-written `ALLOW` / `DENY` / `REQUIRE_APPROVAL` parsing everywhere
- a small wrapper can guard `request_refund` and `issue_compensation` one tool at a time
- custom business actions can be modeled cleanly instead of forcing everything through raw HTTP

Suggested future Nomos tool mapping for this demo:
- `get_order_details`: keep direct for the insecure baseline, or later guard as a governed read path
- `request_refund`: guard with Nomos first
- `issue_compensation`: guard with Nomos first and make this the main deny-or-approval demo path

Reference docs in the Nomos repo:
- `C:\Users\prudh\repos\safe-agentic-world\nomos\docs\http-sdk.md`
- `C:\Users\prudh\repos\safe-agentic-world\nomos\docs\integration-patterns.md`
- `C:\Users\prudh\repos\safe-agentic-world\nomos\docs\custom-actions.md`
- `C:\Users\prudh\repos\safe-agentic-world\nomos\docs\http-integration-kit.md`

## 11. Recommended Screenshot Sequence

Capture these in order:
1. eligibility check for `ORD-1001`
2. successful refund request for `ORD-1001`
3. refund plus approved `$1000` compensation for `ORD-1001`
4. later, the same compensation request after Nomos integration

## 12. Troubleshooting

If `python` is not recognized:

```powershell
py -3.12 -m venv .venv
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

If the support service is unavailable:
- make sure `python .\mock_services.py refund` is still running
- make sure `.env` points `REFUND_BASE_URL` and `COMP_SERVICE_BASE_URL` at `http://127.0.0.1:8002`

If the assistant fails immediately:
- confirm `OPENAI_API_KEY` is set in `.env`
- confirm the selected `OPENAI_MODEL` is available to your account

If the UI does not load:
- confirm `uvicorn web_demo:app --reload --port 8010` is still running
- reopen `http://127.0.0.1:8010`
