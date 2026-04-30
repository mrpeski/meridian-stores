---
📋 FINAL IMPLEMENTATION PLAN
Executive Summary
You're building an AI chatbot for Meridian Electronics customer support. I've analyzed the codebase, tested the MCP server, and created a detailed 24-task implementation plan. Based on your preferences:
- ✅ OpenAI API key available
- ✅ Using gpt-4o model
- ✅ Deleting old game agent code
- ✅ Minimal UI styling
- ✅ No additional demo scenarios needed
Phase 1: Preparation & Cleanup ⚙️
Task 1: Update AGENTS.md
File: /Users/olayinka/ai_bootcamp/meridian-stores/AGENTS.md
Action: Replace entire content with the chatbot-focused guide I drafted above
Why: Gives future developers (and AI assistants) clear guidance on the chatbot architecture, conventions, and workflows
---

Task 2: Delete legacy game agent code
Files to delete:

- backend/src/meridian_stores/agents/agent.py (612 lines of game logic)
- backend/src/meridian_stores/agents/agent_config.py (game-specific config)
- backend/src/meridian_stores/agents/config.py (hardcoded game values)
- backend/src/meridian_stores/agents/main.py (if exists)
- backend/src/meridian_stores/agents/mcp.http (HTTP test file)
- backend/src/meridian_stores/agents/requirements.txt (duplicate deps)
- backend/src/meridian_stores/agents/available_tools.json (static tool list)
  Keep:
- backend/src/meridian_stores/agents/llm_clients.py ✅ (reusable OpenAI client)
  Why: Clean slate for chatbot implementation, remove confusion

---

Phase 2: Backend Configuration ⚙️
Task 3: Update settings.py
File: backend/src/meridian_stores/settings.py
Add fields to Settings class:

# After existing fields, add

openai_api_key: str = Field(
default="",
description="OpenAI API key for chatbot LLM",
)
mcp_server_url: str = Field(
default="<https://order-mcp-74afyau24q-uc.a.run.app/mcp>",
description="MCP server URL for order management tools",
)
chatbot_model: str = Field(
default="gpt-4o",
description="OpenAI model to use for chatbot",
)
Why: Environment-driven configuration following existing conventions

---

Task 4: Update config/env.example
File: config/env.example
Add to end of file:

# AI Chatbot configuration

MERIDIAN_STORES_OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE
MERIDIAN_STORES_MCP_SERVER_URL=<https://order-mcp-74afyau24q-uc.a.run.app/mcp>
MERIDIAN_STORES_CHATBOT_MODEL=gpt-4o
Why: Template for developers to set up their local environment

---

Phase 3: Backend Chatbot Core 🤖
Task 5: Create chatbot_config.py
File: backend/src/meridian_stores/agents/chatbot_config.py
from dataclasses import dataclass
@dataclass
class ChatbotConfig:
"""Configuration for the customer support chatbot."""
mcp_server_url: str
openai_api_key: str
model: str = "gpt-4o"
max_tokens: int = 2000
temperature: float = 0.7

    @property
    def mcp_headers(self) -> dict:
        """Headers for MCP HTTP requests."""
        return {"Accept": "application/json"}

## Why: Clean separation of chatbot config from main settings

Task 6: Create system_prompt.py
File: backend/src/meridian_stores/agents/system_prompt.py
CUSTOMER_SUPPORT_PROMPT = """You are a helpful customer support agent for Meridian Electronics, a company that sells computer products including monitors, keyboards, printers, networking gear, and accessories.
Your responsibilities:

1. Help customers find products using search_products() or list_products()
2. Check product details and inventory with get_product(sku)
3. Assist with order placement using create_order() (ONLY after customer authentication)
4. Look up order history with list_orders() (ONLY after customer authentication)
5. Answer product questions clearly and professionally
   AUTHENTICATION REQUIREMENTS:

- ALWAYS verify customer identity with verify_customer_pin(email, pin) before:
  - Placing orders (create_order)
  - Viewing order history (list_orders, get_order)
  - Accessing customer information (get_customer)
- For new inquiries (product search, general questions), NO authentication needed
  IMPORTANT GUIDELINES:
- Be friendly, professional, and concise
- Always confirm order details before calling create_order()
- If inventory is insufficient, offer alternative quantities or products
- Handle errors gracefully and explain issues in plain language
- Never make up product information - always use tools to fetch real data
- Ask clarifying questions if customer requests are ambiguous
  CONVERSATION FLOW:

1. Greet customers warmly
2. Understand their need (browse, order, check history)
3. Use appropriate tools to help
4. Confirm actions before executing (especially orders)
5. Provide clear confirmation messages with relevant details"""
   Why: Clear, comprehensive system prompt with security rules and workflow guidance

---

Task 7: Create conversation_manager.py
File: backend/src/meridian_stores/agents/conversation_manager.py
from typing import Dict, List
from uuid import uuid4
class ConversationManager:
"""
Manages multi-turn conversation state.
In-memory storage for prototype (use Redis for production).
"""

    def __init__(self):
        self._conversations: Dict[str, List[dict]] = {}

    def get_conversation(self, conversation_id: str) -> List[dict]:
        """Get conversation history by ID."""
        return self._conversations.get(conversation_id, [])

    def add_message(self, conversation_id: str, role: str, content: str):
        """Add a message to conversation history."""
        if conversation_id not in self._conversations:
            self._conversations[conversation_id] = []
        self._conversations[conversation_id].append({
            "role": role,
            "content": content
        })

    def create_conversation(self) -> str:
        """Create a new conversation and return its ID."""
        conversation_id = str(uuid4())
        self._conversations[conversation_id] = []
        return conversation_id

    def clear_conversation(self, conversation_id: str):
        """Clear conversation history."""
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]

# Global instance for prototype

conversation_manager = ConversationManager()
Why: Simple state management that's easy to swap for Redis later

---

Task 8: Create chatbot.py
File: backend/src/meridian_stores/agents/chatbot.py
import json
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from .chatbot_config import ChatbotConfig
from .llm_clients import OpenAIClient
from .system_prompt import CUSTOMER_SUPPORT_PROMPT
class CustomerSupportBot:
"""AI-powered customer support chatbot using MCP and OpenAI."""

    def __init__(self, config: ChatbotConfig):
        self.config = config
        self.session: ClientSession | None = None
        self.llm: OpenAIClient | None = None
        self.tools: list = []

    async def initialize_mcp_session(self):
        """Connect to MCP server and list available tools."""
        # Note: Context manager will be handled by caller
        async with streamablehttp_client(
            url=self.config.mcp_server_url,
            headers=self.config.mcp_headers,
        ) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                self.session = session

                # Get available tools from MCP server
                mcp_tools = (await session.list_tools()).tools

                # Initialize LLM client
                llm_config = type('Config', (), {
                    'model': self.config.model,
                    'system_prompt': CUSTOMER_SUPPORT_PROMPT
                })()
                self.llm = OpenAIClient(llm_config, api_key=self.config.openai_api_key)

                # Convert MCP tools to OpenAI format
                self.tools = self.llm.convert_tools(mcp_tools)

    async def handle_message(
        self,
        user_message: str,
        conversation_history: list
    ) -> tuple[str, list]:
        """
        Process a user message and return bot response.

        Args:
            user_message: The user's message
            conversation_history: Previous messages in conversation

        Returns:
            Tuple of (bot_response, tool_calls_made)
        """
        # Add user message to conversation
        messages = conversation_history + [{"role": "user", "content": user_message}]

        # Run LLM loop (may call tools multiple times)
        final_messages, tool_calls = await self._run_llm_loop(messages)

        # Extract final assistant response
        assistant_message = final_messages[-1]["content"]

        return assistant_message, tool_calls

    async def _run_llm_loop(self, messages: list) -> tuple[list, list]:
        """
        Run LLM completion loop, executing tool calls until completion.

        Returns:
            Tuple of (updated_messages, list_of_tool_calls_made)
        """
        tool_calls_made = []

        while True:
            # Call LLM
            response = await self.llm.complete(messages, self.tools)

            # Add assistant message
            messages.append(self.llm.assistant_message(response["raw"]))

            # Check if done (no tool calls)
            if not response["tool_calls"]:
                break

            # Execute each tool call
            tool_results = []
            for tc in response["tool_calls"]:
                tool_calls_made.append(tc["name"])
                result = await self._execute_tool(tc["name"], tc["args"])
                tool_results.append({"id": tc["id"], "output": result})

            # Add tool results to messages
            tool_msgs = self.llm.user_message(tool_results)
            if isinstance(tool_msgs, list):
                messages.extend(tool_msgs)
            else:
                messages.append(tool_msgs)

        return messages, tool_calls_made

    async def _execute_tool(self, tool_name: str, args: dict) -> str:
        """Execute an MCP tool and return the result."""
        result = await self.session.call_tool(tool_name, args)
        return result.content[0].text if result.content else ""

    async def close(self):
        """Cleanup resources."""
        if self.llm:
            await self.llm.close()

## Why: Core chatbot logic with clean separation of concerns

Phase 4: Backend API Integration 🔌
Task 9: Add Pydantic models to app.py
File: backend/src/meridian_stores/app.py
Add after imports, before app creation:
from pydantic import BaseModel, Field
class ChatRequest(BaseModel):
"""Request for chat endpoint."""
message: str = Field(..., min_length=1, max_length=4000)
conversation_id: str | None = None
customer_id: str | None = None
class ChatResponse(BaseModel):
"""Response from chat endpoint."""
response: str
conversation_id: str
metadata: dict = {}
Why: Type-safe API contracts

---

Task 10: Add /api/chat endpoint to app.py
File: backend/src/meridian_stores/app.py
Add after existing routes:
from meridian_stores.agents.chatbot import CustomerSupportBot
from meridian_stores.agents.chatbot_config import ChatbotConfig
from meridian_stores.agents.conversation_manager import conversation_manager
@app.post("/api/chat")
async def chat(request: ChatRequest) -> ChatResponse:
"""
Handle customer support chat messages.

    Connects to MCP server, processes message with LLM, executes tools, returns response.
    """
    try:
        # Get or create conversation
        conversation_id = request.conversation_id or conversation_manager.create_conversation()
        conversation_history = conversation_manager.get_conversation(conversation_id)

        # Initialize chatbot
        config = ChatbotConfig(
            mcp_server_url=settings.mcp_server_url,
            openai_api_key=settings.openai_api_key,
            model=settings.chatbot_model,
        )

        bot = CustomerSupportBot(config)

        try:
            await bot.initialize_mcp_session()

            # Process message
            bot_response, tool_calls = await bot.handle_message(
                request.message,
                conversation_history
            )

            # Update conversation history
            conversation_manager.add_message(conversation_id, "user", request.message)
            conversation_manager.add_message(conversation_id, "assistant", bot_response)

            return ChatResponse(
                response=bot_response,
                conversation_id=conversation_id,
                metadata={"tool_calls": tool_calls}
            )

        finally:
            await bot.close()

    except Exception as e:
        raise HelloWorldError(
            code="chatbot_error",
            message=f"Failed to process chat message: {str(e)}",
            status_code=500
        )

## Why: Main entry point for chatbot functionality

Phase 5: Backend Testing 🧪
Task 11: Create test_chatbot.py
File: backend/tests/test_chatbot.py
import pytest
from meridian_stores.agents.llm_clients import OpenAIClient
from meridian_stores.agents.chatbot_config import ChatbotConfig
def test_chatbot_config_creation():
"""Test chatbot configuration."""
config = ChatbotConfig(
mcp_server_url="<https://test.com/mcp>",
openai_api_key="test-key",
model="gpt-4o"
)
assert config.model == "gpt-4o"
assert "application/json" in config.mcp_headers["Accept"]
def test_openai_client_tool_conversion():
"""Test MCP tool conversion to OpenAI format."""
config = type('Config', (), {'model': 'gpt-4o', 'system_prompt': 'test'})()
client = OpenAIClient(config, api_key="test-key")

    # Mock MCP tool
    mock_tool = type('Tool', (), {
        'name': 'test_tool',
        'description': 'A test tool',
        'inputSchema': {'type': 'object', 'properties': {}}
    })()

    converted = client.convert_tools([mock_tool])

    assert len(converted) == 1
    assert converted[0]['type'] == 'function'
    assert converted[0]['function']['name'] == 'test_tool'

# Additional tests would go here (mocked MCP server integration tests)

## Why: Ensure core components work correctly

Task 12: Update test_app.py
File: backend/tests/test_app.py
Add after existing tests:
@pytest.mark.asyncio
async def test_chat_endpoint_requires_message(client):
"""Test chat endpoint validation."""
response = await client.post("/api/chat", json={})
assert response.status_code == 422 # Validation error
@pytest.mark.asyncio
async def test_chat_endpoint_rejects_empty_message(client):
"""Test chat endpoint rejects empty messages."""
response = await client.post("/api/chat", json={"message": ""})
assert response.status_code == 422

# Note: Full integration tests with MCP server would require mocking or test server

## Why: Basic endpoint validation tests

Phase 6: Frontend Core 💻
Task 13: Create TypeScript types
File: frontend/src/types/chat.ts
export interface Message {
id: string;
role: "user" | "assistant";
content: string;
timestamp: Date;
}
export interface ChatRequest {
message: string;
conversation_id?: string;
customer_id?: string;
}
export interface ChatResponse {
response: string;
conversation_id: string;
metadata?: Record<string, any>;
}
export interface ErrorResponse {
error: {
code: string;
message: string;
};
}
Why: Type safety across frontend

---

Task 14: Create useChat hook
File: frontend/src/hooks/useChat.ts
import { useState } from "react";
import { apiUrl } from "../lib/apiBase";
import type { Message, ChatRequest, ChatResponse, ErrorResponse } from "../types/chat";
export function useChat() {
const [messages, setMessages] = useState<Message[]>([]);
const [isLoading, setIsLoading] = useState(false);
const [conversationId, setConversationId] = useState<string>();
const [error, setError] = useState<string | null>(null);
const sendMessage = async (text: string) => {
if (!text.trim()) return;
// Create user message
const userMessage: Message = {
id: crypto.randomUUID(),
role: "user",
content: text,
timestamp: new Date(),
};
// Add to UI immediately
setMessages((prev) => [...prev, userMessage]);
setIsLoading(true);
setError(null);
try {
const request: ChatRequest = {
message: text,
conversation_id: conversationId,
};
const res = await fetch(apiUrl("/api/chat"), {
method: "POST",
headers: { "Content-Type": "application/json" },
body: JSON.stringify(request),
});
if (!res.ok) {
const errorData = (await res.json()) as ErrorResponse;
throw new Error(errorData.error.message || "Failed to send message");
}
const data = (await res.json()) as ChatResponse;
// Update conversation ID
setConversationId(data.conversation_id);
// Add bot response
const botMessage: Message = {
id: crypto.randomUUID(),
role: "assistant",
content: data.response,
timestamp: new Date(),
};
setMessages((prev) => [...prev, botMessage]);
} catch (err) {
setError(err instanceof Error ? err.message : "An error occurred");
} finally {
setIsLoading(false);
}
};
const clearConversation = () => {
setMessages([]);
setConversationId(undefined);
setError(null);
};
return { messages, isLoading, error, sendMessage, clearConversation };
}
Why: Centralized chat logic with state management

---

Task 15: Create MessageBubble component
File: frontend/src/components/MessageBubble.tsx
import type { Message } from "../types/chat";
interface MessageBubbleProps {
message: Message;
}
export function MessageBubble({ message }: MessageBubbleProps) {
const isUser = message.role === "user";
return (
<div
style={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        marginBottom: "1rem",
      }} >
<div
style={{
          maxWidth: "70%",
          padding: "0.75rem 1rem",
          borderRadius: "0.5rem",
          backgroundColor: isUser ? "#3b82f6" : "#27272a",
          color: "#ffffff",
          wordWrap: "break-word",
        }} >
<div style={{ fontSize: "0.875rem", whiteSpace: "pre-wrap" }}>
{message.content}
</div>
</div>
</div>
);
}
Why: Reusable message display with minimal styling

---

Task 16: Create MessageList component
File: frontend/src/components/MessageList.tsx
import { useEffect, useRef } from "react";
import { MessageBubble } from "./MessageBubble";
import type { Message } from "../types/chat";
interface MessageListProps {
messages: Message[];
}
export function MessageList({ messages }: MessageListProps) {
const bottomRef = useRef<HTMLDivElement>(null);
// Auto-scroll to bottom when new messages arrive
useEffect(() => {
bottomRef.current?.scrollIntoView({ behavior: "smooth" });
}, [messages]);
return (
<div
style={{
        flex: 1,
        overflowY: "auto",
        padding: "1rem",
        display: "flex",
        flexDirection: "column",
      }} >
{messages.length === 0 ? (
<div
style={{
            flex: 1,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#71717a",
            fontSize: "0.875rem",
          }} >
Start a conversation by typing a message below
</div>
) : (
<>
{messages.map((msg) => (
<MessageBubble key={msg.id} message={msg} />
))}
<div ref={bottomRef} />
</>
)}
</div>
);
}
Why: Scrollable message container with auto-scroll

---

Task 17: Create TypingIndicator component
File: frontend/src/components/TypingIndicator.tsx
export function TypingIndicator() {
return (
<div style={{ padding: "0 1rem 1rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
<div
style={{
          padding: "0.75rem 1rem",
          borderRadius: "0.5rem",
          backgroundColor: "#27272a",
          color: "#a1a1aa",
          fontSize: "0.875rem",
        }} >
<span>Bot is typing</span>
<span className="typing-dots">...</span>
</div>
</div>
);
}
Why: Visual feedback during bot responses

---

Task 18: Create ChatInput component
File: frontend/src/components/ChatInput.tsx
import { useState, useRef, useEffect } from "react";
interface ChatInputProps {
onSend: (message: string) => void;
disabled?: boolean;
}
export function ChatInput({ onSend, disabled }: ChatInputProps) {
const [input, setInput] = useState("");
const textareaRef = useRef<HTMLTextAreaElement>(null);
useEffect(() => {
textareaRef.current?.focus();
}, []);
const handleSend = () => {
if (input.trim() && !disabled) {
onSend(input);
setInput("");
}
};
const handleKeyDown = (e: React.KeyboardEvent) => {
if (e.key === "Enter" && !e.shiftKey) {
e.preventDefault();
handleSend();
}
};
return (
<div
style={{
        padding: "1rem",
        borderTop: "1px solid #3f3f46",
        display: "flex",
        gap: "0.5rem",
      }} >
<textarea
ref={textareaRef}
value={input}
onChange={(e) => setInput(e.target.value)}
onKeyDown={handleKeyDown}
placeholder="Type your message..."
disabled={disabled}
rows={2}
style={{
          flex: 1,
          padding: "0.75rem",
          borderRadius: "0.375rem",
          border: "1px solid #3f3f46",
          backgroundColor: "#18181b",
          color: "#e4e4e7",
          fontSize: "0.875rem",
          resize: "none",
          fontFamily: "inherit",
        }}
/>
<button
onClick={handleSend}
disabled={disabled || !input.trim()}
style={{
          padding: "0.75rem 1.5rem",
          borderRadius: "0.375rem",
          border: "none",
          backgroundColor: disabled || !input.trim() ? "#3f3f46" : "#3b82f6",
          color: "#ffffff",
          fontSize: "0.875rem",
          fontWeight: 500,
          cursor: disabled || !input.trim() ? "not-allowed" : "pointer",
        }} >
Send
</button>
</div>
);
}
Why: User input with keyboard shortcuts and validation

---

Task 19: Create ChatInterface component
File: frontend/src/components/ChatInterface.tsx
import { useChat } from "../hooks/useChat";
import { MessageList } from "./MessageList";
import { ChatInput } from "./ChatInput";
import { TypingIndicator } from "./TypingIndicator";
export function ChatInterface() {
const { messages, isLoading, error, sendMessage, clearConversation } = useChat();
return (
<div
style={{
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        backgroundColor: "#18181b",
        color: "#e4e4e7",
      }} >
{/_ Header _/}
<div
style={{
          padding: "1rem",
          borderBottom: "1px solid #3f3f46",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }} >
<h1 style={{ fontSize: "1.25rem", fontWeight: 600, margin: 0 }}>
Meridian Electronics Support
</h1>
<button
onClick={clearConversation}
style={{
            padding: "0.5rem 1rem",
            borderRadius: "0.375rem",
            border: "1px solid #3f3f46",
            backgroundColor: "transparent",
            color: "#a1a1aa",
            fontSize: "0.875rem",
            cursor: "pointer",
          }} >
Clear
</button>
</div>
{/_ Error banner _/}
{error && (
<div
style={{
            padding: "0.75rem 1rem",
            backgroundColor: "#7f1d1d",
            color: "#fca5a5",
            fontSize: "0.875rem",
            borderBottom: "1px solid #991b1b",
          }} >
{error}
</div>
)}
{/_ Messages _/}
<MessageList messages={messages} />
{/_ Typing indicator _/}
{isLoading && <TypingIndicator />}
{/_ Input _/}
<ChatInput onSend={sendMessage} disabled={isLoading} />
</div>
);
}
Why: Main container that wires everything together

---

Task 20: Update App.tsx
File: frontend/src/App.tsx
Replace entire content:
import { ChatInterface } from "./components/ChatInterface";
export function App() {
return <ChatInterface />;
}
Why: Switch from hello world to chat UI

---

Phase 7: Integration & Testing 🧪
Task 21: Create directories
Commands:
mkdir -p frontend/src/types
mkdir -p frontend/src/hooks
mkdir -p frontend/src/components
Why: Ensure folder structure exists

---

Task 22: Test backend locally
Commands:

# Terminal 1: Start backend

cd backend
uv sync --group dev
uv run uvicorn meridian_stores.app:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Test with curl

curl -X POST <http://localhost:8000/api/chat> \
 -H "Content-Type: application/json" \
 -d '{"message": "Do you have any monitors?"}'
Expected: JSON response with bot answer and conversation_id

---

Task 23: Test frontend locally
Commands:

# Terminal 3: Start frontend

cd frontend
npm install
npm run dev
Test scenarios:

1. Type "Do you have wireless keyboards?" → Should get product list
2. Type "I want to order something" → Should ask for authentication
3. Test clear conversation button

---

Task 24: Update README.md
File: README.md
Add after "What you get" section:

## AI Chatbot Feature

The application includes an AI-powered customer support chatbot that:

- Answers product inquiries using natural language
- Checks real-time inventory
- Assists with order placement (after customer authentication)
- Looks up order history for returning customers
  The chatbot connects to an MCP (Model Context Protocol) server for order management and uses OpenAI GPT-4o for conversations.

### Required Environment Variables

Add to `config/.env`:

```bash
MERIDIAN_STORES_OPENAI_API_KEY=sk-proj-your-key-here
MERIDIAN_STORES_MCP_SERVER_URL=https://order-mcp-74afyau24q-uc.a.run.app/mcp
See config/env.example for the complete template.
**Why:** Document the chatbot feature for other developers
---
## **✅ FINAL CHECKLIST**
Before presenting to leadership:
- [ ] All 24 tasks completed
- [ ] Backend runs without errors
- [ ] Frontend displays chat interface
- [ ] Can search for products successfully
- [ ] Authentication flow works (email + PIN)
- [ ] Order placement completes successfully
- [ ] Error messages display properly
- [ ] AGENTS.md fully updated
- [ ] README.md documents chatbot setup
**Demo script:**
1. "Show me wireless keyboards" (product search)
2. "I'd like to order 2 of the Logitech model" (authentication flow)
3. "Show my order history" (history lookup)
4. "Order 10000 monitors" (error handling)
---
## **📊 ESTIMATED COMPLETION TIME**
- **Phase 1-2 (Prep & Config):** 30 minutes
- **Phase 3 (Backend Core):** 90 minutes
- **Phase 4 (API Integration):** 45 minutes
- **Phase 5 (Backend Tests):** 30 minutes
- **Phase 6 (Frontend):** 2 hours
- **Phase 7 (Integration):** 45 minutes
**Total: ~6 hours**
```
