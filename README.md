<p align="center">
  <img src="frontend/src/assets/logo.png" alt="Dukaan — Your E-Commerce AI Agent" width="380" />
</p>

<h1 align="center">Dukaan — AI-Native Autonomous E-Commerce Platform</h1>

<p align="center">
  <strong>An intelligent, end-to-end fashion e-commerce ecosystem powered by dual autonomous AI agents (Customer Stylist & Merchant Copilot), dynamic margin-guarded price negotiation, real-time behavioral personalization, event-driven background notifications, and Google Agent-to-Agent (A2A) protocol compliance.</strong>
</p>

<p align="center">
  <a href="https://dukaan-avbodh.onrender.com/"><strong>🚀 View Live Demo</strong></a>&nbsp;&nbsp;•&nbsp;&nbsp;
  <a href="https://www.youtube.com/watch?v=cWfC2f-2MW0"><strong>🎥 Watch A2A Video Demo</strong></a><br><br>
  <em>Demo Merchant Account</em> 👉 <strong>Email:</strong> <code>hello@gmail.com</code> | <strong>Password:</strong> <code>123456</code>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/React_19-61DAFB?style=flat-square&logo=react&logoColor=black" alt="React 19" />
  <img src="https://img.shields.io/badge/LangGraph-FF6F00?style=flat-square&logo=langchain&logoColor=white" alt="LangGraph" />
  <img src="https://img.shields.io/badge/MCP_Protocol-blueviolet?style=flat-square" alt="MCP Protocol" />
  <img src="https://img.shields.io/badge/A2A_Protocol-green?style=flat-square" alt="A2A Protocol" />
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/MongoDB-47A248?style=flat-square&logo=mongodb&logoColor=white" alt="MongoDB" />
  <img src="https://img.shields.io/badge/Redis-DC382D?style=flat-square&logo=redis&logoColor=white" alt="Redis" />
  <img src="https://img.shields.io/badge/RabbitMQ-FF6600?style=flat-square&logo=rabbitmq&logoColor=white" alt="RabbitMQ" />
  <img src="https://img.shields.io/badge/Pinecone-000000?style=flat-square&logo=pinecone&logoColor=white" alt="Pinecone" />
  <img src="https://img.shields.io/badge/Razorpay-0C2451?style=flat-square&logo=razorpay&logoColor=white" alt="Razorpay" />
  <img src="https://img.shields.io/badge/Brevo-0B99FF?style=flat-square&logo=sendinblue&logoColor=white" alt="Brevo" />
  <img src="https://img.shields.io/badge/Tailwind_CSS_v4-38B2AC?style=flat-square&logo=tailwind-css&logoColor=white" alt="Tailwind CSS" />
</p>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [System Architecture](#-system-architecture)
- [Key Features](#-key-features)
  - [1. Customer AI Stylist & Negotiator](#1-customer-ai-stylist--negotiator)
  - [2. Merchant Business Copilot & Management Suite](#2-merchant-business-copilot--management-suite)
  - [3. Agent-to-Agent (A2A) Commerce Protocol](#3-agent-to-agent-a2a-commerce-protocol)
  - [4. Event-Driven Messaging & Security Subsystem](#4-event-driven-messaging--security-subsystem)
- [Tech Stack](#-tech-stack)
- [Repository Structure](#-repository-structure)
- [AI Agent System — Deep Dive](#-ai-agent-system--deep-dive)
  - [Customer Agent (MCP-Driven)](#customer-agent-mcp-driven)
  - [Merchant Agent (Native Structured Tools)](#merchant-agent-native-structured-tools)
  - [Proactive Behavioral Triggers](#proactive-behavioral-triggers)
- [Business Logic & Mathematical Models](#-business-logic--mathematical-models)
  - [Dynamic Price Negotiation Engine](#dynamic-price-negotiation-engine)
  - [Campaign-Aware Sequential Pricing](#campaign-aware-sequential-pricing)
  - [Hybrid Recommendation Engine](#hybrid-recommendation-engine)
  - [Curated Combo Kit Upselling](#curated-combo-kit-upselling)
- [API Reference](#-api-reference)
- [Database Schema & Storage Architecture](#-database-schema--storage-architecture)
- [Getting Started & Local Setup](#-getting-started--local-setup)
  - [Prerequisites](#prerequisites)
  - [1. Clone Repository](#1-clone-repository)
  - [2. Backend Setup](#2-backend-setup)
  - [3. Frontend Setup](#3-frontend-setup)
  - [4. Environment Variables Reference](#4-environment-variables-reference)
- [Running the Services](#-running-the-services)
- [Testing & Quality Assurance](#-testing--quality-assurance)
- [Deployment Guide](#-deployment-guide)
- [Git Workflow & Commit Standards](#-git-workflow--commit-standards)
- [License & Credits](#-license--credits)

---

## 🔭 Overview

**Dukaan** ("shop" in Hindi) reimagines e-commerce from the ground up as an AI-native ecosystem. Rather than forcing shoppers through static filters and rigid checkout funnels, Dukaan pairs every customer with an autonomous **AI Stylist & Negotiator** that assists with natural language discovery, builds personalized bundle offers, conducts mathematical price negotiations with strict margin protection, and coordinates in-chat Razorpay checkout.

Simultaneously, store owners manage their business with an autonomous **Merchant AI Copilot** that monitors real-time sales KPIs, detects inventory risks, updates pricing bounds, and analyzes haggling patterns through conversation or an interactive analytics portal.

External buyer agents can also autonomously browse, negotiate, and transact on Dukaan via compliance with the Google **Agent-to-Agent (A2A)** protocol.

---

## 🏗 System Architecture

The following diagram illustrates the modern decoupled architecture of Dukaan:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               FRONTEND (React 19 + Vite)                               │
│  ┌───────────────────────┐  ┌───────────────────────┐  ┌────────────────────────────┐  │
│  │   Customer Storefront │  │ Floating Agent Widget │  │ Merchant Analytics Portal  │  │
│  │ (Catalog/Filters/Cart)│  │ (Streaming/Cards/OTP) │  │ (Recharts/Orders/Copilot)  │  │
│  └───────────┬───────────┘  └───────────┬───────────┘  └─────────────┬──────────────┘  │
│              │                          │                            │                 │
│              └──────────────────────────┼────────────────────────────┘                 │
│                                         │ HTTP / REST / SSE (Axios + JWT)              │
└─────────────────────────────────────────┼──────────────────────────────────────────────┘
                                          ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               FASTAPI BACKEND (main.py)                                │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │ Feature Domains: Auth | Cart | Chat | Merchant | Negotiation | Notification      │  │
│  │                  Order | Payment | Product | rabbitmq | Recommedation | User     │  │
│  └───────┬───────────────────────────┬─────────────────────────────┬────────────────┘  │
│          │                           │                             │                   │
│  ┌───────▼───────┐           ┌───────▼────────┐            ┌───────▼────────┐          │
│  │  Controllers  │           │   Middleware   │            │ Background Bus │          │
│  │ & Domain Svc  │           │  JWT Auth &    │            │ (aio-pika AMQP │          │
│  │               │           │  Merchant RBAC │            │  Producer)     │          │
│  └───────┬───────┘           └────────────────┘            └───────┬────────┘          │
│          │                                                         │                   │
│          ├──────────────────────────┬──────────────────────────────┤                   │
│          ▼                          ▼                              ▼                   │
│  ┌──────────────────┐    ┌─────────────────────┐        ┌─────────────────────┐        │
│  │ Customer Agent   │    │ Merchant Copilot    │        │ RabbitMQ Broker     │        │
│  │ (LangGraph Graph)│    │ (LangGraph Graph)   │        │ Queue: dukaan.notif │        │
│  └───────┬──────────┘    └──────────┬──────────┘        └──────────┬──────────┘        │
│          │                          │                              │                   │
│          │ MCP SSE (port 8001)      │ Native Function Calling      │ Worker Consumer   │
│          ▼                          ▼                              ▼                   │
│  ┌──────────────────┐    ┌─────────────────────┐        ┌─────────────────────┐        │
│  │ FastMCP User Svc │    │ 7 Merchant Tools    │        │ Brevo Email Service │        │
│  │ (Catalog, Search,│    │ (Analytics, Orders, │        │ (Signup OTP, Reset, │        │
│  │ Cart, Negotiate) │    │  Inventory, Bounds) │        │  Order Slips)       │        │
│  └──────────────────┘    └─────────────────────┘        └─────────────────────┘        │
└──────────┬──────────────────────────┬──────────────────────────────┬───────────────────┘
           │                          │                              │
           ▼                          ▼                              ▼
┌─────────────────────┐    ┌─────────────────────┐        ┌─────────────────────┐
│  PostgreSQL (Neon)  │    │  MongoDB (Atlas)    │        │ Redis Cache         │
│  Users, Products,   │    │  chat_threads,      │        │ 5-min OTP TTL,      │
│  Orders, Carts,     │    │  merchant_chats,    │        │ Brute-force limits, │
│  Campaigns, Events  │    │  audit_logs, Memory │        │ Checkpoints         │
└─────────────────────┘    └─────────────────────┘        └─────────────────────┘
                                      │
                                      ▼
                           ┌─────────────────────┐
                           │ Pinecone Vector DB  │
                           │ 384-dim Embeddings  │
                           │ Semantic Search     │
                           └─────────────────────┘
```

---

## ✨ Key Features

### 1. Customer AI Stylist & Negotiator
- **Natural Language Shopping:** Chat with an AI stylist that answers sizing queries, searches clothing by aesthetics, modifies the cart, and prepares orders.
- **Semantic Vector Search:** Powered by Pinecone and HuggingFace `all-MiniLM-L6-v2` dense embeddings, allowing queries like *"something earthy for an autumn evening"*.
- **Margin-Guarded Negotiation:** Customers can haggle on price. The agent mathematically computes cost floors and loyalty concessions without ever dipping below minimum merchant margins.
- **Curated Combo Kit Bundling:** Generates complementary outfit bundles (e.g., matching a selected shirt with trending trousers) with stacked campaign discounts.
- **Proactive Interactivity:** Automatically triggers conversational outreach when shoppers view multiple items, linger on checkout, or go idle.
- **In-Chat Payment Link:** Instant Razorpay payment links generated and rendered as interactive cards directly in the conversation.

### 2. Merchant Business Copilot & Management Suite
- **Interactive Analytics Dashboard:** Real-time metrics on gross revenue, net profit, average order value, category breakdowns, and AI-negotiated discount volume.
- **Conversational Copilot:** Store owners can query store metrics, search orders, and reprice inventory using natural language (e.g., *"Show me our lowest stock items and summarize today's revenue"*).
- **Strict Role-Based Security (RBAC):** All merchant tools, endpoints, and chat threads enforce strict role validation (`merchant` or `admin`). Customer calls are rejected with `HTTP 403 Forbidden`.
- **Dynamic Pricing Guardrails:** Merchants can dynamically adjust platform-wide maximum discount percentages and minimum profit margin thresholds.
- **Chat & Financial Auditing:** Comprehensive audit logs stored in MongoDB tracking every discount decision, haggling session, and order transition.

### 3. Agent-to-Agent (A2A) Commerce Protocol
- **Agent Card Discovery:** Machine-readable endpoint at `/.well-known/agent-card.json` advertising platform capabilities, pricing models, and communication interfaces.
- **Machine-Readable Catalog:** Standardized endpoint at `/a2a/catalog` allowing external AI agents to programmatically retrieve product inventory.
- **JSON-RPC Autonomous Interaction:** Standardized `/a2a/interact/message:send` endpoint enabling buyer agents to initiate sessions, negotiate pricing, and finalize orders autonomously.

### 4. Event-Driven Messaging & Security Subsystem
- **Redis-Backed OTP Verification:** 6-digit OTP verification for account signup and forgot-password flows with 5-minute TTL, attempt counters, and brute-force protection.
- **Asynchronous RabbitMQ Message Queue:** Decouples email notifications from HTTP request cycles using `aio-pika` async producers and a standalone consumer worker.
- **Brevo (Sendinblue) Email Service:** Professional, responsive HTML email templates for account verification, password resets, and order confirmation slips with offline fallback.

---

## 🛠 Tech Stack

| Domain | Technology | Description |
|---|---|---|
| **Backend Framework** | **FastAPI** | High-performance asynchronous Python REST framework |
| **Relational Database** | **PostgreSQL (Neon)** | Serverless cloud PostgreSQL managed with **SQLModel** + **asyncpg** |
| **Document & Memory Store** | **MongoDB (Atlas)** | Motor async driver for chat transcripts, audit trails, and agent memory |
| **In-Memory Cache** | **Redis** | In-memory key-value store for OTPs, rate-limiting, and state checkpointers |
| **Message Broker** | **RabbitMQ** | Asynchronous message broker with `aio-pika` and robust reconnection logic |
| **AI Agent Orchestration** | **LangGraph** | Stateful cyclic multi-agent graph with checkpointers and tool nodes |
| **Tool Protocol** | **FastMCP** | Model Context Protocol server exposing user tools on port 8001 |
| **LLM Gateway** | **OpenRouter / Gemini / Groq** | Multi-provider LLM gateway supporting Gemini, Claude, and Llama models |
| **Vector Database** | **Pinecone** | Cloud vector database for dense product embeddings |
| **Embeddings** | **HuggingFace** | `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional dense vectors) |
| **Payment Gateway** | **Razorpay** | Webhook-verified payment order creation and payment links |
| **Email Service** | **Brevo (Sendinblue)** | Transactional email delivery via REST API v3 with responsive HTML templates |
| **Frontend Framework** | **React 19** + **Vite** | Modern client framework with fast build tooling |
| **Styling** | **Tailwind CSS v4** | Utility-first styling with modern dark/light styling rules |
| **State Management** | **Zustand** | Persisted global state slices for auth, cart, chat, and catalog |
| **Routing** | **React Router v7** | Declarative client-side routing |
| **Visualizations** | **Recharts** | Interactive charts for merchant analytics |

---

## 📁 Repository Structure

```
Dukaan/
├── backend/
│   ├── main.py                         # FastAPI application entry point & lifecycle hooks
│   ├── requirements.txt                # Production Python dependencies
│   ├── .env                            # Backend environment configuration
│   ├── backfill_embeddings.py          # Script to vectorize product catalog into Pinecone
│   │
│   ├── Auth/                           # Authentication & Identity domain
│   │   ├── controller.py               # Signup, login, and password reset logic
│   │   ├── otp.py                      # Redis OTP service (TTL, brute-force limits)
│   │   ├── jwt.py                      # Token encoding, decoding, and verification
│   │   ├── routes.py                   # /auth/signup, /auth/login, /auth/verify-otp, etc.
│   │   └── schemas.py                  # Pydantic request & response models
│   │
│   ├── Merchant/                       # Merchant business domain & native tools
│   │   ├── controller.py               # Analytics, orders, and pricing bounds handler
│   │   ├── database.py                 # Merchant database queries & SQL aggregations
│   │   ├── tools.py                    # 7 Native Structured LangChain tools (RBAC enforced)
│   │   ├── routes.py                   # /merchant/analytics, /orders, /chat, etc.
│   │   ├── models.py                   # MerchantDiscountPolicy & settings
│   │   └── utils.py                    # Role validation, currency & margin math helpers
│   │
│   ├── Notification/                   # Notification & email delivery domain
│   │   ├── service.py                  # Central NotificationService orchestrator
│   │   ├── base.py                     # Abstract base email and SMS provider interfaces
│   │   ├── templates.py                # Responsive HTML/text email templates
│   │   └── providers/
│   │       └── brevo.py                # Brevo REST API v3 provider with fallback
│   │
│   ├── rabbitmq/                       # Asynchronous message broker integration
│   │   ├── connection.py               # Resilient aio-pika robust connection manager
│   │   ├── producer.py                 # Async event publisher for order & OTP events
│   │   └── worker.py                   # Standalone consumer queue worker
│   │
│   ├── agents/                         # LangGraph stateful agent definitions
│   │   ├── user/                       # Customer Stylist agent (MCP-backed)
│   │   │   ├── graph.py                # StateGraph compiled with Mongo checkpointer
│   │   │   ├── prompts.py              # ReAct prompt instructions & output schemas
│   │   │   └── agent_service.py        # Agent initialization and MCP tool bindings
│   │   └── merchant/                   # Merchant Copilot agent (native tools)
│   │       ├── agent_node.py           # LLM node & tool execution node
│   │       ├── agent_prompts.py        # Merchant copilot system prompts
│   │       └── agent_service.py        # Graph compilation & merchant state setup
│   │
│   ├── mcp/                            # Model Context Protocol servers
│   │   └── mcp_server_user/            # Customer tools server (port 8001)
│   │       ├── cart.py                 # Cart operations
│   │       ├── order.py                # Order and payment checking
│   │       ├── pricing.py              # Combo calculations & negotiation tool
│   │       ├── product.py              # Product retrieval
│   │       ├── recommendation.py       # Hybrid recommendation logic
│   │       ├── search.py               # Vector + keyword hybrid search
│   │       └── user.py                 # Buyer profile management
│   │
│   ├── Cart/                           # Cart management domain
│   ├── Chat/                           # Customer chat threads & audit retrieval
│   ├── Negotiation/                    # Dynamic price haggling endpoints
│   ├── Order/                          # Order lifecycle & status tracking
│   ├── Payment/                        # Razorpay order creation & webhook handlers
│   ├── Product/                        # Catalog management, models & schemas
│   ├── Recommedation/                  # Recommendation engine services
│   ├── User/                           # User models & profile services
│   ├── UserEvents/                     # Client behavioral event tracking
│   │
│   ├── config/                         # Database and infrastructure singletons
│   │   ├── database.py                 # Neon PostgreSQL connection & table initializer
│   │   ├── mogodbconfig.py             # MongoDB Motor async client
│   │   ├── redis.py                    # Redis client with connection pooling
│   │   ├── vectorDatabase.py           # Pinecone index client
│   │   ├── chatModel.py                # LLM factory (OpenRouter / LangChain)
│   │   └── embeddingModel.py           # HuggingFace sentence transformer factory
│   │
│   └── tests/                          # Automated integration and unit test suites
│       ├── test_merchant_e2e.py        # Complete Merchant domain end-to-end test
│       ├── test_merchant_tools.py      # Merchant tools RBAC and execution test
│       ├── test_notifications_rabbitmq_auth.py # OTP, RabbitMQ, and email test
│       └── ...                         # Concurrency, negotiation & cart tests
│
├── frontend/
│   ├── index.html                      # Single Page Application HTML root
│   ├── package.json                    # Frontend dependencies & scripts
│   ├── vite.config.js                  # Vite bundler configuration
│   ├── tailwind.config.js              # Tailwind CSS configuration
│   │
│   └── src/
│       ├── App.jsx                     # Root router component
│       ├── main.jsx                    # React 19 entry point
│       ├── store/                      # Zustand state management
│       │   ├── useStore.js             # Consolidated persisted store
│       │   ├── createAuthSlice.js      # User identity & JWT persistence
│       │   ├── createCartSlice.js      # Cart state & local synchronization
│       │   ├── createChatSlice.js      # Chat messages, streaming, & active thread
│       │   └── createProductSlice.js   # Catalog cache & active filters
│       ├── services/                   # HTTP API client modules (Axios)
│       │   ├── api.js                  # Centralized Axios client with JWT interceptor
│       │   ├── authService.js          # Signup, verify OTP, login, reset password
│       │   ├── agentService.js         # Streaming chat and trigger events
│       │   └── ...                     # Cart, order, product services
│       └── features/                   # Modular feature components
│           ├── auth/                   # Login, Signup, OTP Modal, Forgot Password
│           ├── chatbot/                # Floating AI Stylist widget & cards
│           ├── merchant/               # Merchant dashboard, charts, & copilot
│           ├── cart/                   # Cart drawer, checkout, and order slips
│           ├── products/               # Product catalog, grid, and product cards
│           └── shared/                 # Navbar, footer, and common modals
│
└── AGENTS.md                           # Strict multi-agent engineering rules
```

---

## 🤖 AI Agent System — Deep Dive

### Customer Agent (MCP-Driven)
The customer agent is constructed using **LangGraph** following the ReAct (Reasoning + Acting) loop. It connects to the user tools via FastMCP over Server-Sent Events (SSE) on port 8001:

```
[Customer Query] ──► [Agent Node (LLM)] ──► Tool Call Needed?
                            ▲                      │
                            │                YES   ▼
                     [Execute Tool] ◄─── [Tools Node (FastMCP: 8001)]
                            │
                            ▼ NO
                    [Final Streaming Response]
```

#### User MCP Tools Summary:
| Tool Name | Purpose | Key Guardrails |
|---|---|---|
| `search_products` | Semantic vector search + keyword fallback | Top-$k$ similarity, gender-aware filtering |
| `get_product_detail` | Detailed specifications, sizes, and stock | Validates product ID existence |
| `get_cart` / `add_to_cart` | Inspect and manipulate user cart items | Quantity clamps, size availability check |
| `calculate_combo_offer` | Assembles matching items into a bundle | Applies priority campaign discounts |
| `negotiate_discount` | Dynamic price haggling calculation | Bounded by profit floor and loyalty tier |
| `decline_combo_offer` | Resets active negotiated bundle | Reverts cart pricing to base NSP |
| `create_order` | Finalizes cart into order & payment link | Verifies stock & Razorpay credentials |
| `check_payment_status` | Confirms payment settlement with Razorpay | Validates webhook / signature state |

### Merchant Agent (Native Structured Tools)
Unlike the customer agent, the Merchant Copilot uses **7 native LangChain Structured Tools** compiled directly into the application process. This eliminates network serialization overhead, ensures instant response times, and enforces strict merchant authorization.

```
[Merchant Prompt] ──► [Merchant Agent Node] ──► Inspects Role & Session
                             │
                             ▼
                 [Valid Merchant Role?]
                 ├── NO  ──► Returns 403 Forbidden Error
                 └── YES ──► Executes Native Tool ──► Returns Analytics / Repricing
```

#### Native Merchant Tools:
1. `merchant_get_store_analytics`: Computes gross revenue, net profit, margin %, total orders, and cumulative discounts given.
2. `merchant_get_top_selling_products`: Identifies top revenue-generating products with stock tracking.
3. `merchant_get_inventory_health_and_reorder_alerts`: Flags items with low stock ($\le 5$) or out of stock.
4. `merchant_lookup_order_details`: Fetches complete customer, address, itemized products, and payment status for any order.
5. `merchant_update_product_pricing_and_margin`: Safely adjusts product price, minimum profit margin %, or stock count with audit tracking.
6. `merchant_get_customer_negotiation_insights`: Aggregates customer haggling behavior, accepted discounts, and drop-off patterns.
7. `merchant_publish_catalog_item`: Creates new catalog items and automatically generates Pinecone vector embeddings.

### Proactive Behavioral Triggers
The frontend monitors user actions and dispatches behavioral events to `/chat/event`:
- `idle_timeout`: User inactive on a page for $>30$ seconds.
- `viewed_multiple_products`: User browsed 3+ products in the same category without adding to cart.
- `viewed_checkout`: User opened the cart/checkout page.
- `activity_threshold_reached`: Cumulative engagement score passes engagement threshold.

*Spam Protection:* The backend applies an in-memory session debounce filter, ensuring an agent suggestion is not fired repeatedly within the same interaction window.

---

## 💰 Business Logic & Mathematical Models

### Dynamic Price Negotiation Engine
The negotiation engine guarantees that no discount ever causes a merchant to incur a loss.

1. **Margin Floor Calculation:**
   $$\text{Total Price} = \sum (\text{Selling Price} \times \text{Quantity})$$
   $$\text{Total Cost} = \sum (\text{Cost Price} \times \text{Quantity})$$
   $$\text{Minimum Required Profit} = \sum (\text{Cost Price} \times \text{Min Margin \%} \times \text{Quantity})$$
   $$\text{Maximum Permissible Discount} = \text{Total Price} - \text{Total Cost} - \text{Minimum Required Profit}$$

2. **Loss-Leader Rejection:**
   If $\text{Total Price} - \text{Total Cost} \le 0$, the request is immediately rejected.

3. **Loyalty-Tier Concession Weighting:**
   - **New Customer:** Maximum discount capped at $70\%$ of available headroom; concession rate $= 25\%$.
   - **Returning Customer:** Standard concession rate $= 30\%$.
   - **Loyal Customer** (order placed within 30 days): Concession rate $= 40\%$.

4. **Exponential Decay Haggling:**
   $$\text{Remaining Headroom} = \text{Ceiling Discount} - \text{Current Discount}$$
   $$\text{Concession Step} = \max(0.5\%, \text{Remaining Headroom} \times \text{Concession Factor})$$
   $$\text{Counter Offer} = \min(\text{Current} + \text{Step}, \text{Requested}, \text{Ceiling})$$

5. **Hard Safety Floor:**
   If Counter Price $\le \text{Total Cost}$, price is clamped to $\text{Total Cost} + ₹0.01$.

### Campaign-Aware Sequential Pricing
Campaigns stack sequentially based on priority tiers:
- `HIGH_PRIORITY`: Weight $= 3\times$
- `MEDIUM_PRIORITY`: Weight $= 2\times$
- `LOW_PRIORITY`: Weight $= 1\times$

$$\text{New Selling Price (NSP)} = \text{Base Price} \times \prod_{i=1}^{n} (1 - \text{Discount}_i)$$

Whenever a campaign is linked or updated, a SQLAlchemy event trigger recalculates the product's catalog importance score:
$$\text{Importance Score} = \text{Stock} \times \sum (\text{Campaign Weights})$$

### Hybrid Recommendation Engine
Recommendations balance customer historical interest with store campaign priorities:
$$\text{Product Score} = 0.5 \times \text{Normalized}(\text{Behavior Score}) + 0.5 \times \text{Normalized}(\text{Importance Score})$$

For semantic search results, query vector similarity is prioritized:
$$\text{Search Score} = 0.7 \times \text{Cosine Similarity} + 0.3 \times \text{Normalized}(\text{Importance Score})$$

**Behavioral Interaction Weights:**
- Completed Purchase: $+5.0$ (decayed over 60 days)
- Added to Cart: $+3.0$
- Accepted Suggestion: $+3.0$
- Viewed Product: $+1.0$
- Removed from Cart: $-1.0$
- Dismissed Suggestion: $-2.0$

### Curated Combo Kit Upselling
When a user adds an item to their cart, the upsell engine:
1. Selects 1–2 items from the active cart.
2. Finds 1–2 complementary items (e.g., matching a T-Shirt with Jeans or Shorts) filtered by gender.
3. Applies campaign discounts to calculate base bundle pricing.
4. Provides a pre-approved bundle discount (typically $5\%-10\%$) to encourage higher Average Order Value (AOV).

---

## 📡 API Reference

### Authentication & Account Security
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/auth/signup` | Public | Register user and trigger 6-digit verification OTP |
| `POST` | `/auth/verify-otp` | Public | Verify OTP and activate account |
| `POST` | `/auth/resend-otp` | Public | Resend verification OTP with rate limiting |
| `POST` | `/auth/login` | Public | Authenticate with identifier/password → returns JWT |
| `POST` | `/auth/forgot-password` | Public | Request password reset OTP |
| `POST` | `/auth/reset-password` | Public | Submit reset OTP and set new password |

### Products & Catalog
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/product/catalog` | Public | Retrieve full product catalog |
| `GET` | `/product/detail/{id}` | Public | Get product details & log view event |
| `GET` | `/product/type/{type}` | Public | Filter products by category |
| `POST` | `/product/add` | Merchant | Add new product to catalog (auto-vectorized) |

### Cart & Checkout
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/cart/` | Customer | Fetch current active cart and items |
| `POST` | `/cart/item` | Customer | Add product to cart with size/quantity |
| `PUT` | `/cart/item/{item_id}` | Customer | Update cart item quantity |
| `DELETE`| `/cart/item/{item_id}` | Customer | Remove specific item from cart |
| `DELETE`| `/cart/` | Customer | Clear all items from active cart |
| `POST` | `/checkout/` | Customer | Process order checkout with applied discounts |

### Orders & Payments
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/order/my-orders` | Customer | Get order history for authenticated user |
| `GET` | `/order/all` | Merchant | List all platform orders |
| `GET` | `/order/{id}` | Authenticated | Get detailed order status and items |
| `PATCH` | `/order/{id}/status` | Merchant | Update order fulfillment status |
| `POST` | `/api/payment/create-order` | Authenticated | Create Razorpay order and payment link |
| `POST` | `/api/payment/verify` | Authenticated | Verify HMAC SHA-256 signature and clear cart |
| `GET` | `/api/payment/status/{user_id}` | Authenticated | Check user payment completion status |
| `POST` | `/api/payment/webhook` | Public | Razorpay asynchronous event webhook |

### AI Agents & Chat
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/chat/message` | Public / User | Send query to Customer Stylist agent |
| `POST` | `/chat/event` | Public / User | Dispatch proactive behavioral trigger |
| `GET` | `/chat/threads` | Authenticated | Get user chat session history |
| `GET` | `/chat/thread/{thread_id}` | Authenticated | Get full message transcript for thread |

### Merchant Operations & Copilot
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/merchant/analytics` | Merchant | Fetch revenue, profit, margins, and trends |
| `GET` | `/merchant/orders` | Merchant | Paginated order list with customer details |
| `GET` | `/merchant/orders/{order_id}` | Merchant | Single order itemization |
| `PUT` | `/merchant/orders/{order_id}/status` | Merchant | Update fulfillment status |
| `GET` | `/merchant/inventory-alerts` | Merchant | Low-stock and out-of-stock item alerts |
| `GET` | `/merchant/audit-logs` | Merchant | MongoDB financial and negotiation audit logs |
| `GET` | `/merchant/chat-threads` | Merchant | Customer conversation audit transcripts |
| `GET` | `/merchant/merchant-chats` | Merchant | Merchant copilot conversation history |
| `GET` | `/merchant/pricing-bounds` | Merchant | Current platform negotiation discount limits |
| `PUT` | `/merchant/pricing-bounds` | Merchant | Update maximum discount & minimum margin |
| `POST` | `/merchant/chat` | Merchant | Conversational Merchant Copilot query |

### Google A2A (Agent-to-Agent) Protocol
| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/.well-known/agent-card.json` | Public | Standard machine-readable agent card |
| `POST` | `/a2a/start_session` | Public | Initialize session for external buyer agent |
| `GET` | `/a2a/catalog` | Public | Retrieve JSON product catalog for AI agents |
| `POST` | `/a2a/interact/message:send` | Public | Send JSON-RPC 2.0 message between agents |

---

## 🗄 Database Schema & Storage Architecture

### PostgreSQL Tables (SQLModel + asyncpg)

```
┌─────────────────────────┐         ┌─────────────────────────┐
│          users          │         │        products         │
├─────────────────────────┤         ├─────────────────────────┤
│ id (PK)                 │         │ id (PK)                 │
│ name                    │         │ name                    │
│ identifier (email) (UQ) │         │ price, cost_price       │
│ password_hash           │◄───┐     │ min_profit_margin_%     │
│ role (enum)             │    │     │ stock                   │
│ address                 │    │     │ type (enum)             │
│ created_at              │    │     │ brand, gender, sizes    │
└────────────┬────────────┘    │     │ description, rating     │
             │                 │     │ image_url, discount     │
             │1:N              │     │ importance_score        │
             ▼                 │     └────────────┬────────────┘
┌─────────────────────────┐    │                  │
│         orders          │    │                  │1:N
├─────────────────────────┤    │                  ▼
│ id (PK)                 │    │     ┌─────────────────────────┐
│ user_id (FK)            │    │     │  campaign_product_links │
│ product_id (FK)─────────┼────┼────►├─────────────────────────┤
│ discount_percent        │    │     │ campaign_id (FK)        │
│ status                  │    │     │ product_id (FK)         │
│ razorpay_order_id       │    │     └────────────┬────────────┘
│ razorpay_payment_id     │    │                  │
│ payment_link            │    │                  ▼
│ created_at              │    │     ┌─────────────────────────┐
└─────────────────────────┘    │     │        campaigns        │
                               │     ├─────────────────────────┤
┌─────────────────────────┐    │     │ id (PK)                 │
│          carts          │    │     │ agenda, discount_%      │
├─────────────────────────┤    │     │ priority, type          │
│ id (PK)                 │    │     │ total_items_sold        │
│ user_id (FK, Unique)    │────┘     └─────────────────────────┘
│ created_at, updated_at  │
└────────────┬────────────┘          ┌─────────────────────────┐
             │1:N                    │   discount_policies     │
             ▼                       ├─────────────────────────┤
┌─────────────────────────┐          │ id (PK)                 │
│       cart_items        │          │ product_id (FK)         │
├─────────────────────────┤          │ base_discount_%, max_%  │
│ id (PK)                 │          │ agent_step_%, min_qty   │
│ cart_id (FK)            │          └─────────────────────────┘
│ product_id (FK)         │
│ quantity, size          │          ┌─────────────────────────┐
│ added_at                │          │ merchant_discount_pol.  │
└─────────────────────────┘          ├─────────────────────────┤
                                     │ id (PK)                 │
┌─────────────────────────┐          │ merchant_id (FK)        │
│       user_events       │          │ max_negotiation_disc_%  │
├─────────────────────────┤          │ min_profit_margin_%     │
│ id (PK), user_id (FK)   │          │ is_active, updated_at   │
│ product_id, event_type  │          └─────────────────────────┘
│ category, timestamp     │
└─────────────────────────┘
```

### MongoDB Collections (Motor async)
| Database | Collection | Content / Schema |
|---|---|---|
| `dukaan_chat` | `chat_threads` | Customer chat history with nested messages, timestamps, and thread state |
| `dukaan_chat` | `merchant_chats` | Merchant copilot conversation history and state snapshots |
| `dukaan_audit`| `audit_logs` | Detailed audit records of price concessions, orders, and payment webhooks |
| `langgraph`   | `checkpoints` | Serialized LangGraph agent graph execution states |

### Redis Key Patterns
| Key Pattern | Data Type | TTL | Purpose |
|---|---|---|---|
| `otp:signup:{email}` | String | 300s (5m) | 6-digit verification code for new user registration |
| `otp:forgot_password:{email}` | String | 300s (5m) | 6-digit verification code for password reset |
| `otp:attempts:{purpose}:{email}` | Integer | 300s (5m) | Failed attempt counter (locks at 5 failed tries) |

---

## 🚀 Getting Started & Local Setup

### Prerequisites
- **Python 3.11+**
- **Node.js 18+** and **npm**
- **PostgreSQL** (local instance or cloud [Neon](https://neon.tech))
- **MongoDB** (local instance or cloud [MongoDB Atlas](https://www.mongodb.com/atlas))
- **Redis** (local instance or cloud [Upstash](https://upstash.com))
- **RabbitMQ** (local instance, Docker, or [CloudAMQP](https://customer.cloudamqp.com))
- API Keys for: **OpenRouter** (or Google Gemini / Groq), **Pinecone**, **HuggingFace**, **Razorpay**, and optionally **Brevo**.

### 1. Clone Repository
```bash
git clone https://github.com/Tanishq112005/Dukaan-Avbodh.git
cd Dukaan-Avbodh
```

### 2. Backend Setup
```bash
cd backend

# Create and activate virtual environment
# Windows:
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS:
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup
```bash
cd ../frontend

# Install npm packages
npm install
```

### 4. Environment Variables Reference

#### Backend (`backend/.env`):
```env
# ─── Databases ─────────────────────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://user:password@ep-host.region.neon.tech/dukaan?ssl=require
MONGODB_URL=mongodb+srv://user:password@cluster.mongodb.net/dukaan?retryWrites=true&w=majority
REDIS_URL=redis://localhost:6379/0

# ─── Message Broker (RabbitMQ) ─────────────────────────────────────────────
RABBITMQ_URL=amqp://guest:guest@localhost:5672/

# ─── AI & LLM Providers ────────────────────────────────────────────────────
OPEN_ROUTER_KEYS=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GOOGLE_API_KEY=AIzaxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ─── Embeddings & Vector Search ────────────────────────────────────────────
HUGGINGFACE_API_KEY=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
PINECONE_API_KEY=pc-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ─── MCP Tool Servers ──────────────────────────────────────────────────────
MCP_USER_SERVER_URL=http://127.0.0.1:8001/sse

# ─── Payments (Razorpay) ───────────────────────────────────────────────────
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxx
RAZORPAY_KEY_SECRET=xxxxxxxxxxxxxxxxxxxxxxxx

# ─── Email Delivery (Brevo) ────────────────────────────────────────────────
BREVO_API_KEY=xkeysib-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
BREVO_SENDER_EMAIL=noreply@dukaan.com
BREVO_SENDER_NAME=Dukaan Store

# ─── Application & Security ────────────────────────────────────────────────
JWT_SECRET=your-super-secret-jwt-signing-key-here
FRONTEND_URL=http://localhost:5173
```

#### Frontend (`frontend/.env`):
```env
VITE_API_URL=http://localhost:8000
VITE_RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxx
```

---

## ▶️ Running the Services

To run the complete platform locally, open separate terminal windows:

### Terminal 1 — User MCP Server
```bash
cd backend
.venv\Scripts\activate   # (or source .venv/bin/activate on Linux/Mac)
python -m mcp.mcp_server_user.main
```
*Runs FastMCP SSE server on `http://localhost:8001`.*

### Terminal 2 — RabbitMQ Notification Worker (Optional for local development)
```bash
cd backend
.venv\Scripts\activate
python -m rabbitmq.worker
```
*If RabbitMQ is not running, the application gracefully dispatches emails synchronously using simulated or direct delivery.*

### Terminal 3 — FastAPI Backend
```bash
cd backend
.venv\Scripts\activate
uvicorn main:app --reload --port 8000
```
*FastAPI runs on `http://localhost:8000` with interactive Swagger docs at `http://localhost:8000/docs`.*

### Terminal 4 — React Frontend
```bash
cd frontend
npm run dev
```
*Vite dev server starts on `http://localhost:5173`.*

---

## 🧪 Testing & Quality Assurance

Dukaan includes a comprehensive suite of end-to-end integration tests validating role security, OTP lifecycles, and database consistency.

Run tests using the project's virtual environment:

```bash
cd backend

# Run the complete unified Merchant Domain E2E test suite
python tests/test_merchant_e2e.py

# Run Merchant AI Tools RBAC authorization test suite
python tests/test_merchant_tools.py

# Run Notifications, RabbitMQ worker, and Redis OTP auth test suite
python tests/test_notifications_rabbitmq_auth.py

# Run Order concurrency and inventory reservation test suite
python tests/test_order_concurrency_e2e.py
```

---

## 🌐 Deployment Guide

| Service | Recommended Host | Configuration Details |
|---|---|---|
| **Backend API** | [Render](https://render.com) / [Railway](https://railway.app) | Web Service running `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| **Frontend** | [Vercel](https://vercel.com) | Framework preset: Vite. Output directory: `dist/`. SPA rewrites configured in `vercel.json` |
| **User MCP Tool Server** | [Render](https://render.com) | Background Worker / Private Service running `python -m mcp.mcp_server_user.main` |
| **PostgreSQL** | [Neon](https://neon.tech) | Serverless PostgreSQL with SSL connection pooling |
| **MongoDB** | [MongoDB Atlas](https://www.mongodb.com/atlas) | Serverless or M0 cluster with IP access rules configured |
| **Redis** | [Upstash](https://upstash.com) | Serverless Redis with standard TLS connection string |
| **RabbitMQ** | [CloudAMQP](https://www.cloudamqp.com) | Managed RabbitMQ cluster |

---

## 🛡 Git Workflow & Commit Standards

Per repository engineering conventions defined in [`AGENTS.md`](AGENTS.md):
- **NEVER work directly on the `main` branch.** Development takes place on dedicated agent branches (`agent-backend`, `agent-frontend`, `agent-docs`).
- **Incremental commits:** Every change represents an isolated, testable improvement.
- **Commit prefix standard:**
  - `feat: <message>` — New features or architectural capabilities.
  - `fix: <message>` — Bug fixes and corrections.
  - `update: <message>` — Improvements or modifications to existing functionality.

---

## 📄 License & Credits

This project is licensed under the **MIT License**.

Built with ❤️ by **Tanishq** — *Dukaan Avbodh*
