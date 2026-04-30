# Agent guide — Meridian Stores AI Chatbot

This repo builds an **AI-powered customer support chatbot** for Meridian Electronics. The chatbot connects to an existing **MCP (Model Context Protocol) server** to handle product inquiries, order placement, order history lookups, and customer authentication.

**Architecture**: FastAPI backend (`backend/`) exposes a chat endpoint that uses an MCP client to call business tools. React frontend (`frontend/`) provides a chat UI. The backend connects to `https://order-mcp-74afyau24q-uc.a.run.app/mcp` (Streamable HTTP transport) and uses **OpenAI GPT-4o** for conversational AI.

## Project goal

Build a working **customer support chatbot prototype** that demonstrates:
1. **Product availability checks** (monitors, keyboards, printers, networking gear, accessories)
2. **Order placement** with validation
3. **Order history lookup** for returning customers
4. **Customer authentication** via email + 4-digit PIN

The prototype will be presented to leadership (engineering team + VP of Customer Experience).

## Layout

| Path | Role |
| --- | --- |
| `backend/src/meridian_stores/` | FastAPI app (`app.py`), chatbot endpoint, settings (`settings.py`) |
| `backend/src/meridian_stores/agents/` | Chatbot logic: MCP client, LLM orchestration, tool calling |
| `backend/src/meridian_stores/agents/chatbot.py` | Main chatbot class (`CustomerSupportBot`) |
| `backend/src/meridian_stores/agents/llm_clients.py` | OpenAI client with tool calling support (reusable) |
| `backend/src/meridian_stores/agents/system_prompt.py` | Customer support prompt templates |
| `backend/tests/` | Pytest for backend routes and chatbot logic |
| `frontend/src/components/` | React chat UI components |
| `frontend/src/hooks/useChat.ts` | API integration hook |
| `config/env.example` | Copy to `config/.env`; add `OPENAI_API_KEY` and `MCP_SERVER_URL` |
| `frontend/config/frontend.env.example` | Copy to `frontend/.env` for Vite dev |

## Conventions to preserve

- **API middleware order**: Exception handlers first, **CORS last** (outermost) — see `backend/src/meridian_stores/app.py`
- **Configuration**: Everything is **environment-driven**. Never hardcode API keys, MCP URLs, or deployment-specific values in code. Load from `settings.py`.
- **MCP transport**: Use `streamablehttp_client` from `mcp.client.streamable_http` with `Accept: application/json` header
- **Frontend API calls**: Dev uses Vite proxy (`/api/*`); production builds use `VITE_API_BASE_URL` (no trailing slash)
- **Error handling**: Return structured JSON errors: `{"error": {"code": "...", "message": "..."}}`
- **Tool calling**: Use `OpenAIClient` from `llm_clients.py` — it handles MCP tool conversion and execution loop

## Key environment variables

### Backend (`config/.env`)
```bash
# Required
OPENAI_API_KEY=sk-proj-...
MCP_SERVER_URL=https://order-mcp-74afyau24q-uc.a.run.app/mcp

# Optional overrides
PROJECT_NAME=meridian-stores
MERIDIAN_STORES_API_HOST=0.0.0.0
MERIDIAN_STORES_API_PORT=8000
MERIDIAN_STORES_CORS_ORIGINS=http://localhost:5173
```

### Frontend (`frontend/.env`)
```bash
VITE_API_PROXY_TARGET=http://127.0.0.1:8000
VITE_DEV_HOST=0.0.0.0
VITE_DEV_PORT=5173
```

Update `config/env.example` when adding new variables.

## Commands (from repo root unless noted)

**Backend dev**
```bash
cp config/env.example config/.env
# Add OPENAI_API_KEY to config/.env
cd backend && uv sync --group dev && uv run uvicorn meridian_stores.app:app --reload --host 0.0.0.0 --port 8000
```

**Backend tests**
```bash
cd backend && uv sync --group dev && uv run pytest
```

**Frontend dev**
```bash
cp frontend/config/frontend.env.example frontend/.env
cd frontend && npm install && npm run dev
```

**Docker Compose** (full stack, needs `config/.env` configured)
```bash
docker compose --env-file ./config/.env up --build
```

## Chatbot API

### Endpoint: `POST /api/chat`

**Request:**
```json
{
  "message": "Do you have any 27-inch monitors in stock?",
  "conversation_id": "optional-session-id",
  "customer_id": "optional-uuid-for-auth"
}
```

**Response:**
```json
{
  "response": "Yes, we have 3 models available: Dell UltraSharp U2723DE ($599.99, 15 in stock)...",
  "conversation_id": "abc-123",
  "metadata": {
    "tool_calls": ["search_products"],
    "tokens_used": 450
  }
}
```

**Error response:**
```json
{
  "error": {
    "code": "mcp_connection_failed",
    "message": "Could not connect to order management system"
  }
}
```

## MCP server tools

The MCP server exposes **8 tools** for order management:

### Product management
- `list_products(category?, is_active?)` — Browse inventory by category
- `get_product(sku)` — Get detailed info by SKU (e.g., "MON-0054")
- `search_products(query)` — Natural language search

### Customer management
- `get_customer(customer_id)` — Look up customer by UUID
- `verify_customer_pin(email, pin)` — Authenticate with email + 4-digit PIN

### Order management
- `list_orders(customer_id?, status?)` — View order history
- `get_order(order_id)` — Get order details with line items
- `create_order(customer_id, items[])` — Place new order
  - Items: `{sku: str, quantity: int, unit_price: str, currency: str}`
  - Validates inventory atomically
  - Returns order confirmation with ID

Use `session.list_tools()` to discover tools at runtime.

## Backend architecture

### Core components

**`chatbot.py`** — Main bot class
```python
class CustomerSupportBot:
    async def initialize_mcp_session()      # Connect to MCP server
    async def handle_message(...)           # Main entry point
    async def _run_llm_loop(...)           # LLM + tool calling loop
    async def _execute_tool(...)           # Call MCP tools
    async def close()                      # Cleanup
```

**`llm_clients.py`** — LLM abstraction (already exists)
- `OpenAIClient` handles chat completions with tools
- `convert_tools()` converts MCP tools to OpenAI format
- `complete()` calls OpenAI API with tool support

**`system_prompt.py`** — Prompt engineering
```python
CUSTOMER_SUPPORT_PROMPT = """
You are a helpful customer support agent for Meridian Electronics.
[Instructions for product search, orders, authentication...]
"""
```

**`conversation_manager.py`** — Session management
- In-memory dict for prototype (use Redis for production)
- Methods: `get_conversation()`, `add_message()`, `clear_conversation()`

**`app.py`** — FastAPI endpoint
```python
@app.post("/api/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    bot = CustomerSupportBot(config)
    await bot.initialize_mcp_session()
    response = await bot.handle_message(...)
    return ChatResponse(response=response, conversation_id=...)
```

## Frontend architecture

### Component hierarchy
```
App.tsx
└── ChatInterface.tsx
    ├── MessageList.tsx
    │   └── MessageBubble.tsx (multiple)
    ├── TypingIndicator.tsx
    └── ChatInput.tsx
```

### Key components

**`ChatInterface.tsx`** — Main container
- Manages conversation state with `useChat()` hook
- Handles send message action
- Displays messages and input

**`MessageBubble.tsx`** — Message display
- User messages: right-aligned
- Bot messages: left-aligned
- Minimal styling (black/white/gray)

**`ChatInput.tsx`** — Input UI
- Text input with Enter key support
- Send button (disabled while loading)
- Auto-focus and clear after send

**`useChat.ts` hook** — API logic
```typescript
function useChat() {
  const sendMessage = async (text: string) => {
    // POST to /api/chat
    // Update UI immediately
    // Show typing indicator
    // Add bot response when ready
  };
  return { messages, isLoading, sendMessage };
}
```

## Testing strategy

### Unit tests (`backend/tests/test_chatbot.py`)
- Test MCP tool conversion to OpenAI format
- Test tool execution with mocked MCP responses
- Test error handling (connection failures, invalid args)

### Integration tests (`backend/tests/test_app.py`)
- Test `/api/chat` endpoint success cases
- Test conversation continuity across messages
- Test error responses

### Manual testing scenarios

**Product search:**
```
User: "Do you have wireless keyboards?"
Bot: [calls search_products] "Yes, we have 5 models..."
```

**Order placement:**
```
User: "I want to order 2 monitors"
Bot: "I'll need to verify your identity. Email?"
User: "customer@example.com"
Bot: "Please provide your 4-digit PIN"
User: "1234"
Bot: [calls verify_customer_pin, then create_order]
Bot: "Order confirmed! Order ID: xxx-yyy, Total: $1,199.98"
```

**Order history:**
```
User: "Show my recent orders"
Bot: [authentication flow, then list_orders]
Bot: "You have 3 orders: [list with dates, totals, statuses]"
```

**Error handling:**
```
User: "Order 1000 monitors"
Bot: [gets InsufficientInventoryError]
Bot: "We only have 15 in stock. Would you like that quantity instead?"
```

## When changing behavior

- **Add API routes**: Update `app.py`, add tests in `backend/tests/`
- **Add env vars**: Extend `config/env.example`, document here, wire through `settings.py`
- **Add frontend components**: Keep in `frontend/src/components/`, import to `App.tsx`
- **Modify MCP integration**: Update `chatbot.py` and related modules
- **Change system prompt**: Edit `system_prompt.py` for easy tuning

## What not to do

- **Don't commit secrets**: Never commit `config/.env` or `frontend/.env` with real API keys
- **Don't hardcode MCP URL**: Always load from `settings.py` environment config
- **Don't skip error handling**: Every MCP call can fail; handle gracefully
- **Don't over-engineer**: Focus on working prototype first; polish comes later

## Demo preparation checklist

Before presenting to leadership:
- [ ] Demo product availability check with natural language query
- [ ] Demo order placement with customer authentication
- [ ] Demo order history lookup for returning customer
- [ ] Show error handling (graceful failure when MCP unavailable)
- [ ] Explain security model (PIN verification before sensitive operations)
- [ ] Discuss scalability considerations (Redis for state, rate limits, caching)
- [ ] Show multi-turn conversation context handling

## Next steps for production

**Scalability:**
- Replace in-memory dict with Redis for conversation state
- Add rate limiting per customer
- Implement response caching for common queries

**Security:**
- Use JWT tokens instead of simple conversation IDs
- Encrypt PINs in transit and at rest
- Add audit logging for all order operations

**Features:**
- Order tracking and shipment updates
- Product recommendations based on browsing
- Returns and refund handling
- Multi-language support

**Metrics:**
- Track resolution rate (% of inquiries resolved without human)
- Customer satisfaction scores
- Average conversation length
- Support ticket reduction percentage
