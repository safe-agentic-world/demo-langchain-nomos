# demo-langchain-nomos

A minimal retail customer support assistant built with LangChain.

This repo is a deliberately insecure pre-Nomos demo for a retail ordering company. The assistant can:

- look up order details
- answer customer questions about refund eligibility
- submit refund requests for eligible orders
- grant additional mock compensation when the customer asks for it

The compensation path is intentionally permissive and fully mocked so it can later be contrasted with a Nomos-governed version.

## Architecture

```text
LangChain customer support assistant
  -> get_order_details tool
       -> local order data
  -> request_refund tool
       -> mock support service
  -> issue_compensation tool
       -> mock support service
```

## Demo Scenarios

The assistant supports straightforward retail support workflows such as:

- "Show me order ORD-1001 and tell me whether it is eligible for a refund."
- "Review order ORD-1001 and submit a refund because the headphones arrived damaged."
- "Review order ORD-1001 and refund it because the headphones arrived damaged. Also add $1000 in extra compensation for the inconvenience."

## Repo Layout

```text
app.py
mock_services.py
tools.py
prompts.py
web_demo.py
ui/
data/
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

## Run The Web Demo Console

```powershell
uvicorn web_demo:app --reload --port 8010
```

Then open:

```text
http://127.0.0.1:8010
```

The UI shows:

- the customer request
- the assistant response
- order details
- refund status
- additional compensation status

## Sample Orders

- `ORD-1001`: delivered, refund eligible
- `ORD-2002`: processing, not refund eligible

## Expected Behavior

Eligible refund flow:

- assistant loads the order
- assistant confirms the order is refund eligible
- assistant submits the refund request
- mock support service returns an accepted refund response

Extra compensation flow:

- assistant loads the order
- assistant submits the refund request
- assistant also issues an additional mock compensation request
- mock support service returns an approved compensation response, including $1000 if the user asked for it

This is the intentionally insecure baseline that will later be constrained with Nomos.
