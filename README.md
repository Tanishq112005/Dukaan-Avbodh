<p align="center">
  <img src="frontend/src/assets/logo.png" alt="Dukaan — Your E-Commerce AI Agent" width="400" />
</p>

<h1 align="center">Dukaan — AI-Powered E-Commerce Platform</h1>

<p align="center">
  <strong>An intelligent fashion e-commerce platform where AI agents handle product discovery, price negotiation, upselling, and checkout — all through natural conversation.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/React-61DAFB?style=flat-square&logo=react&logoColor=black" />
  <img src="https://img.shields.io/badge/LangGraph-FF6F00?style=flat-square&logo=langchain&logoColor=white" />
  <img src="https://img.shields.io/badge/MCP-Protocol-blueviolet?style=flat-square" />
  <img src="https://img.shields.io/badge/A2A-Protocol-green?style=flat-square" />
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/MongoDB-47A248?style=flat-square&logo=mongodb&logoColor=white" />
  <img src="https://img.shields.io/badge/Pinecone-000?style=flat-square&logo=pinecone&logoColor=white" />
  <img src="https://img.shields.io/badge/Razorpay-0C2451?style=flat-square&logo=razorpay&logoColor=white" />
  <img src="https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=flat-square&logo=tailwind-css&logoColor=white" />
</p>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [AI Agent System — Deep Dive](#-ai-agent-system--deep-dive)
- [Business Logic — Deep Dive](#-business-logic--deep-dive)
- [API Reference](#-api-reference)
- [Database Schema](#-database-schema)
- [Getting Started](#-getting-started)
- [Environment Variables](#-environment-variables)
- [Running the Application](#-running-the-application)
- [A2A Protocol (Agent-to-Agent)](#-a2a-protocol-agent-to-agent)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🔭 Overview

**Dukaan** ("shop" in Hindi) is a full-stack AI-native e-commerce platform for fashion/clothing. Unlike traditional e-commerce where users browse a static catalog, Dukaan features **two autonomous AI agents** — one for **customers** and one for **merchants** — that actively assist with every step of the shopping and store-management experience.

The platform demonstrates cutting-edge AI engineering patterns:

- **LangGraph** stateful agent graphs with MongoDB-backed per-user memory
- **MCP (Model Context Protocol)** tool servers for modular, hot-swappable agent capabilities
- **A2A (Agent-to-Agent)** protocol compliance for inter-agent commerce
- **Behavioral scoring** and **hybrid recommendation** engine
- **Dynamic price negotiation** with profit-margin guardrails
- **Campaign-aware sequential pricing** with combo kit optimization
- **Razorpay** payment integration with webhook-based order confirmation

---

## ✨ Key Features

### 🧑‍💼 Customer AI Agent
| Feature | Description |
|---|---|
| **Conversational Shopping** | Users chat with an AI stylist that searches products, manages the cart, and handles checkout |
| **Semantic Product Search** | Pinecone vector DB + HuggingFace embeddings for "show me something like…" queries |
| **Smart Recommendations** | Hybrid scoring (behavioral affinity × campaign importance) with gender-aware filtering |
| **Combo Kit Builder** | Automatically bundles cart items + complementary recommendations into discounted kits |
| **AI Price Negotiation** | Users can haggle — the agent uses exponential-decay concession with loyalty-adjusted limits |
| **Proactive Suggestions** | Triggers on idle timeout, multi-product viewing, or checkout page visit |
| **Integrated Payments** | Razorpay payment link generation → webhook confirmation → auto cart clear |

### 🏪 Merchant AI Agent
| Feature | Description |
|---|---|
| **Analytics Dashboard** | Revenue, profit margins, AI discount impact, category breakdown, daily trends |
| **Campaign Management** | Create/update/delete marketing campaigns with priority-based discount stacking |
| **Catalog Management** | Add products with AI-assisted metadata via conversational interface |
| **Order Management** | View all orders with product details, payment status, and customer info |
| **Chat Audit Trail** | Full transcript of every customer conversation with negotiation logs |
| **Money Audit Logs** | MongoDB-backed audit trail of every financial action (discounts given, orders placed) |

### 🤖 A2A (Agent-to-Agent) Protocol
| Feature | Description |
|---|---|
| **Agent Card Discovery** | `/.well-known/agent-card.json` endpoint for standard agent capability advertising |
| **Machine-Readable Catalog** | `/a2a/catalog` endpoint for external buyer agents to browse inventory |
| **JSON-RPC Interaction** | `/a2a/interact/message:send` for other AI agents to shop autonomously |
| **Session Management** | Token-based sessions for external agents with automatic user creation |

---

## 🏗 Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React + Vite)                   │
│  ┌─────────┐  ┌──────────┐  ┌───────────┐  ┌─────────────────┐  │
│  │  Auth   │  │ Products │  │   Cart    │  │ Merchant Dash   │  │
│  │ (Clerk) │  │ Listing  │  │ + Summary │  │ Analytics+Chat  │  │
│  └────┬────┘  └────┬─────┘  └─────┬─────┘  └───────┬─────────┘  │
│       │            │              │                 │            │
│  ┌────┴────────────┴──────────────┴─────────────────┴──────────┐ │
│  │              AgentWidget (Chatbot)                          │ │
│  │   Zustand Store (Auth + Cart + Chat + Product slices)       │ │
│  └─────────────────────────┬───────────────────────────────────┘ │
└────────────────────────────┼─────────────────────────────────────┘
                             │ HTTP (axios)
                             ▼
┌────────────────────────────────────────────────────────────────────┐
│                     FASTAPI BACKEND (main.py)                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Routes: auth / product / order / checkout / payment / chat  │  │
│  │          merchant / a2a                                      │  │
│  └──────┬─────────────┬───────────────────────┬─────────────────┘  │
│         │             │                       │                    │
│  ┌──────▼──────┐ ┌────▼─────────────┐  ┌──────▼──────────────┐    │
│  │ Controllers │ │ LangGraph Agents │  │ Middleware          │    │
│  │ auth/prod/  │ │  ┌─────────────┐ │  │ JWT Auth + RBAC     │    │
│  │ order/chkot │ │  │ User Agent  │ │  └─────────────────────┘    │
│  └──────┬──────┘ │  └──────┬──────┘ │                              │
│         │        │  ┌──────▼──────┐ │                              │
│  ┌──────▼──────┐ │  │Merch Agent  │ │                              │
│  │  Services   │ │  └──────┬──────┘ │                              │
│  │ negotiation │ │         │MCP     │                              │
│  │ pricing     │ └─────────┼────────┘                              │
│  │ behavior    │           │                                       │
│  │ recommend   │           ▼                                       │
│  │ upsell      │  ┌────────────────────┐                           │
│  │ combo       │  │ MCP Tool Servers   │                           │
│  │ analytics   │  │ User  (port 8001)  │                           │
│  │ payment     │  │ Merch (port 8002)  │                           │
│  │ audit       │  └────────────────────┘                           │
│  └──────┬──────┘                                                   │
│         │                                                          │
│  ┌──────▼──────────────────────────────────────────────────────┐   │
│  │                    Repositories (Data Access)               │   │
│  │  product / order / cart / user / campaign / analytics /     │   │
│  │  user_event / discount_policy / chat_audit                  │   │
│  └──────┬──────────────────────┬───────────────────────────────┘   │
│         │                      │                                   │
│  ┌──────▼──────┐    ┌──────────▼──────────┐  ┌─────────────────┐  │
│  │ PostgreSQL  │    │    MongoDB          │  │   Pinecone      │  │
│  │ (Neon)      │    │ (Atlas / local)     │  │  Vector DB      │  │
│  │ SQLModel    │    │ Chat audit, memory, │  │  Semantic       │  │
│  │ + asyncpg   │    │ agent checkpoints   │  │  Search         │  │
│  └─────────────┘    └─────────────────────┘  └─────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

---

## 🛠 Tech Stack

### Backend
| Technology | Purpose |
|---|---|
| **FastAPI** | Async REST API framework |
| **SQLModel** + **asyncpg** | Async PostgreSQL ORM (hosted on Neon) |
| **MongoDB** (Motor) | Chat audit logs, agent memory checkpoints |
| **LangGraph** | Stateful agent graph orchestration |
| **LangChain** | LLM abstraction, MCP adapter, tool binding |
| **FastMCP** | Model Context Protocol tool servers |
| **Pinecone** | Vector database for semantic product search |
| **HuggingFace** | Embedding model (`all-MiniLM-L6-v2`, 384-dim) |
| **OpenRouter** | LLM gateway (multi-model support) |
| **Razorpay** | Payment gateway (orders, payment links, webhooks) |
| **bcrypt** + **python-jose** | Password hashing + JWT authentication |

### Frontend
| Technology | Purpose |
|---|---|
| **React 19** + **Vite** | UI framework + dev/build tooling |
| **TypeScript** | Type safety |
| **Tailwind CSS v4** | Utility-first styling |
| **Zustand** | Lightweight state management (persisted) |
| **React Router v7** | Client-side routing |
| **Clerk** | Authentication provider (SSO, social login) |
| **Recharts** | Dashboard analytics charts |
| **Lucide React** | Icon library |
| **Axios** | HTTP client |
| **Vercel Analytics** | Production usage analytics |

---

## 📁 Project Structure

```
Dukaan/
├── backend/
│   ├── main.py                      # FastAPI app entry point, startup/shutdown lifecycle
│   ├── requirements.txt             # Python dependencies
│   ├── .env                         # Backend environment variables
│   │
│   ├── agents/                      # LangGraph AI Agent definitions
│   │   ├── user/                    # Customer-facing AI agent
│   │   │   ├── agent_service.py     # Agent initialization, MCP tool loading
│   │   │   ├── agent_graph.py       # StateGraph definition (agent ↔ tools loop)
│   │   │   ├── agent_nodes.py       # Agent node (LLM call) + tools node (execute)
│   │   │   ├── agent_prompts.py     # System prompt with ReAct instructions
│   │   │   └── agentState.py        # TypedDict state schema
│   │   └── merchant/                # Merchant-facing AI agent
│   │       ├── agent_service.py     # Merchant agent init + MCP loading
│   │       ├── agent_graph.py       # Merchant StateGraph
│   │       ├── agent_node.py        # Merchant LLM + tools nodes
│   │       ├── agent_prompts.py     # Merchant system prompt
│   │       └── agent_state.py       # Merchant state schema
│   │
│   ├── mcp/                         # MCP (Model Context Protocol) Tool Servers
│   │   ├── mcp_server_user/         # User-facing tools (port 8001)
│   │   │   ├── main.py              # Server entry point
│   │   │   ├── server.py            # FastMCP server instance
│   │   │   ├── product.py           # get_products_by_type, get_product_detail
│   │   │   ├── search.py            # search_products (semantic + keyword)
│   │   │   ├── cart.py              # get_cart, add_to_cart, remove_from_cart, etc.
│   │   │   ├── order.py             # create_order, check_payment_status, clear_cart
│   │   │   ├── pricing.py           # calculate_combo_offer, negotiate_discount
│   │   │   ├── recommendation.py    # recommend_products (hybrid engine)
│   │   │   └── user.py              # get_user_details, update_user_details
│   │   └── mcp_server_merchant/     # Merchant-facing tools (port 8002)
│   │       ├── main.py              # Server entry point
│   │       ├── server.py            # FastMCP server instance
│   │       ├── analytics.py         # get_overall_merchant_summary
│   │       ├── campagin.py          # CRUD campaigns, link products
│   │       └── product.py           # add_product, get_catalog, get_product_detail
│   │
│   ├── config/                      # Configuration & external service clients
│   │   ├── database.py              # Async PostgreSQL (Neon) singleton
│   │   ├── mogodbconfig.py          # MongoDB (Motor) async client
│   │   ├── chatModel.py             # LLM factory (OpenRouter)
│   │   ├── embeddingModel.py        # Embedding model factory (HuggingFace)
│   │   ├── vectorDatabase.py        # Pinecone index client
│   │   └── mcp_config.py            # MCP server URLs + MultiServerMCPClient
│   │
│   ├── models/                      # SQLModel database models
│   │   ├── product.py               # Product, Campaign, CampaignProductLink, ProductType
│   │   ├── user.py                  # User (customer / merchant / ai_agent)
│   │   ├── order.py                 # Order (with Razorpay fields)
│   │   ├── cart.py                  # Cart + CartItem
│   │   ├── discount_policy.py       # Per-product negotiation rules
│   │   ├── user_event.py            # Behavioral tracking events
│   │   └── chat_audit.py            # Pydantic models for chat threads (MongoDB)
│   │
│   ├── services/                    # Core business logic
│   │   ├── negotiation_service.py   # AI price haggling engine
│   │   ├── pricing_service.py       # Campaign-aware sequential discount pricing
│   │   ├── combo_pricing_engine.py  # Kit builder + combo negotiation limits
│   │   ├── recommendation_service.py# Hybrid (affinity + importance) product ranking
│   │   ├── behavior_scorer.py       # User behavior scoring (views, purchases, sessions)
│   │   ├── upsell_service.py        # Curated kit (cart + recommendations) assembly
│   │   ├── analytics_service.py     # Merchant dashboard metrics computation
│   │   ├── payment_service.py       # Razorpay integration + order status management
│   │   ├── audit_logger.py          # MongoDB-backed financial action audit trail
│   │   └── a2a_service.py           # A2A session/user management
│   │
│   ├── repositories/                # Data access layer (async DB queries)
│   │   ├── base_repository.py       # Generic CRUD base
│   │   ├── product_repository.py    # Product queries (by type, by ID, in-stock, etc.)
│   │   ├── order_repository.py      # Order CRUD
│   │   ├── cart_repository.py       # Cart operations (add/remove/clear/get)
│   │   ├── cart_read_repository.py   # Read-only cart queries
│   │   ├── cart_write_repository.py  # Write cart operations
│   │   ├── user_repository.py       # User CRUD + lookup by identifier
│   │   ├── campain_repository.py    # Campaign CRUD + product linking
│   │   ├── analytics_repository.py  # Analytics aggregation queries
│   │   ├── discount_policy_repository.py # Discount policy queries
│   │   ├── user_event_repository.py # Behavioral event queries
│   │   └── chat_audit_repository.py # MongoDB chat thread operations
│   │
│   ├── controllers/                 # Request handling logic
│   │   ├── auth_controller.py       # Signup + Login (bcrypt + JWT)
│   │   ├── product_controller.py    # Product CRUD operations
│   │   ├── order_controller.py      # Order management
│   │   ├── checkout_controller.py   # Checkout flow
│   │   └── user_controller.py       # User profile operations
│   │
│   ├── routes/                      # FastAPI route definitions
│   │   ├── auth_routes.py           # POST /auth/signup, /auth/login
│   │   ├── product_routes.py        # GET /product/catalog, /product/detail/{id}
│   │   ├── order_routes.py          # GET /order/my-orders, /order/all
│   │   ├── checkout_routes.py       # POST /checkout/
│   │   ├── payment_routes.py        # POST /api/payment/create-order, /verify, /webhook
│   │   ├── chat_routes.py           # POST /chat/message, /chat/event
│   │   ├── merchant_routes.py       # GET /merchant/analytics, POST /merchant/chat
│   │   ├── a2a_routes.py            # A2A protocol endpoints
│   │   └── user_routes.py           # User profile endpoints
│   │
│   ├── schemas/                     # Pydantic request/response models
│   ├── middleware/                   # Auth + RBAC middleware
│   └── utils/                       # Utility functions
│       ├── pricing_math.py          # Sequential discounts, haggling math
│       ├── chat_llm_model/          # LLM provider factory
│       └── embedding_model/         # Embedding provider factory
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                  # Root component with routing
│   │   ├── main.jsx                 # React DOM entry point
│   │   ├── store/                   # Zustand state management
│   │   │   ├── useStore.js          # Combined persisted store
│   │   │   ├── createAuthSlice.js   # Authentication state
│   │   │   ├── createCartSlice.js   # Cart state
│   │   │   ├── createChatSlice.js   # AI chatbot state
│   │   │   └── createProductSlice.js# Product listing state
│   │   ├── features/               # Feature-based component modules
│   │   │   ├── auth/               # Login + Signup pages
│   │   │   ├── home/               # Hero, Browse by Style, Product Sections
│   │   │   ├── products/           # Product listing + detail + filters
│   │   │   ├── cart/               # Cart page + summary + order confirmation
│   │   │   ├── chatbot/            # AI agent widget (container, messages, input)
│   │   │   ├── merchant/           # Dashboard (analytics, orders, campaigns, chat)
│   │   │   └── shared/             # Navbar, Footer
│   │   ├── hooks/
│   │   │   └── useAgent.js         # Chat agent hook (message send, event triggers)
│   │   └── lib/
│   │       └── utils.js            # Tailwind merge utility
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── index.html
│
├── fix_db.py                        # DB migration helper
├── migrate_scratch.py               # Column migration script
└── test_orders.py                   # Order testing script
```

---

## 🤖 AI Agent System — Deep Dive

### Agent Architecture

Both agents follow the same **LangGraph** ReAct pattern:

```
User Message → [Agent Node (LLM)] → has tool calls? ──yes──→ [Tools Node] ─┐
                      ▲                      │                              │
                      │                      no                             │
                      │                      ▼                              │
                      │               Return response                      │
                      └────────────────────────────────────────────────────┘
```

**Key design decisions:**

1. **MongoDB Checkpointer** — Each user's conversation history persists across sessions via `MongoDBSaver`. The agent remembers previous interactions, negotiation state, and preferences.

2. **MCP Tool Servers** — Agent tools run as separate FastMCP processes (user tools on port 8001, merchant tools on port 8002). This decouples tool logic from the agent, enables independent scaling, and follows the Model Context Protocol standard.

3. **Per-User State** — Thread ID = user ID, so each customer gets an isolated conversation with full memory.

### User Agent Tools (MCP Server — Port 8001)

| Tool | Description |
|---|---|
| `get_products_by_type` | Fetch products filtered by category (t-shirt, jeans, etc.) |
| `get_product_detail` | Get detailed info for a specific product |
| `search_products` | Semantic search via Pinecone + keyword fallback |
| `recommend_products` | Hybrid recommendation engine (behavior + campaign importance) |
| `get_cart` | Retrieve current cart state |
| `add_to_cart` | Add item to cart (with size) |
| `remove_from_cart` | Remove item from cart |
| `update_cart_item_quantity` | Change item quantity |
| `calculate_combo_offer` | Build a curated kit and compute combo pricing |
| `negotiate_discount` | Run the negotiation engine for a requested discount |
| `decline_combo_offer` | User rejected the combo — reset to cart-only pricing |
| `get_user_details` | Check if user profile is complete for checkout |
| `update_user_details` | Update name/email/address |
| `create_order` | Place order → generate Razorpay payment link |
| `check_payment_status` | Poll Razorpay for payment confirmation |
| `clear_cart` | Empty cart after successful payment |

### Merchant Agent Tools (MCP Server — Port 8002)

| Tool | Description |
|---|---|
| `get_overall_merchant_summary` | Revenue, profit, AI discount impact, trends |
| `get_product_sales_details` | Per-product sales breakdown |
| `get_sales_by_category` | Category-level revenue analysis |
| `get_catalog` | List all products in the store |
| `get_product_detail` | Detailed view of a specific product |
| `add_product` | Add a new product to the catalog |
| `create_campaign` | Create a marketing campaign |
| `get_all_campaigns` | List all active campaigns |
| `update_campaign` | Modify campaign settings |
| `delete_campaign` | Remove a campaign |
| `get_campaign_sales_summary` | Performance metrics for campaigns |

### Proactive Agent Triggers

The frontend monitors user behavior and fires events to the backend:

| Event | When It Fires |
|---|---|
| `idle_timeout` | User inactive for X seconds |
| `viewed_multiple_products` | User browsed several product pages |
| `viewed_checkout` | User visited the cart/checkout page |
| `activity_threshold_reached` | Accumulated interaction score passes threshold |

The backend has a **spam filter** that prevents duplicate triggers within the same session window.

---

## 💰 Business Logic — Deep Dive

### Pricing Pipeline

```
Product Base Price
       │
       ▼
Campaign Discounts (sequential stacking, sorted by priority)
  Price × (1 - campaign₁%) × (1 - campaign₂%) × ...
       │
       ▼
New Selling Price (NSP) ← This is the price the agent works with
       │
       ▼
Combo Kit Assembly (cart items + recommended items)
       │
       ▼
Negotiation Discount (on top of NSP, bounded by margin)
       │
       ▼
Final Price
```

### Campaign System

Campaigns have **three priority tiers** with weighted importance scores:

| Campaign Type | Weight | Effect |
|---|---|---|
| `LOW_PRIORITY` | 1× | Stock × 1 added to product's importance score |
| `MEDIUM_PRIORITY` | 2× | Stock × 2 added to product's importance score |
| `HIGH_PRIORITY` | 3× | Stock × 3 added to product's importance score |

- Campaigns are linked to products via a many-to-many join table (`CampaignProductLink`)
- When a campaign link is added/removed, a **SQLAlchemy event trigger** recomputes the product's `importance_score = stock × Σ(campaign weights)`
- Higher importance scores boost products in recommendations and search results

### Negotiation Engine

The negotiation system is a multi-layered engine that ensures the merchant never loses money:

```
1. Compute negotiation limits from the combo's New Selling Prices
   ├── total_price     = Σ(NSP × quantity)
   ├── total_cost      = Σ(cost_price × quantity)
   ├── total_min_profit = Σ(cost_price × min_profit_margin% × quantity)
   ├── margin          = total_price − total_cost
   └── max_discount    = total_price − total_cost − total_min_profit

2. Loss-leader check
   └── If margin ≤ 0: REJECT all discounts immediately

3. User loyalty adjustment
   ├── New user (no orders):       cap reduced to 70%, concession = 25%
   ├── Returning user (old order): concession = 30%
   └── Loyal user (order < 30d):   concession = 40%

4. Exponential-decay haggling (calculate_next_offer)
   ├── remaining = ceiling − current_discount
   ├── step = remaining × concession_factor  (min 0.5%)
   ├── next_offer = min(current + step, requested, ceiling)
   └── Hard cap: AGENT_MAX_DISCOUNT_PERCENT = 15%

5. Safety clamp
   └── If counter_price ≤ total_cost: clip to cost + ₹0.01
```

**Key rule:** The agent **never invents a discount**. Every discount value comes from the `negotiate_discount` tool.

### Recommendation Engine

The recommendation system uses a **hybrid scoring** approach:

```
Final Score = 0.5 × normalized(event_relevance) + 0.5 × normalized(importance_score)
```

For **search results**, semantic similarity is prioritized:

```
Final Score = 0.7 × normalized(semantic_score) + 0.3 × normalized(importance_score)
```

**Complementary Category Logic:**
| If cart contains... | Suggest... |
|---|---|
| T-shirt, Shirt, or Hoodie | Jeans, Shorts |
| Jeans or Shorts | T-shirt, Shirt, Hoodie |

**Behavioral Scoring Weights:**
| Event | Weight | Multiplier |
|---|---|---|
| Purchased | +5.0 | Current session: 3×, Past session: 1.5× |
| Add to Cart | +3.0 | Recency decay: max(0.2, 1 − days/60) |
| Suggestion Accepted | +3.0 | Global trend: 0.5× |
| Viewed | +1.0 | — |
| Remove from Cart | −1.0 | — |
| Suggestion Skipped | −2.0 | — |

### Combo Kit Builder

The upsell service assembles curated kits:

1. Take **1-2 items from the cart** (prefer campaign-linked items)
2. Add **1-2 recommended items** (complementary categories, gender-matched)
3. Apply campaign discounts to get New Selling Prices
4. Compute combo totals with optional extra negotiated discount

---

## 📡 API Reference

### Authentication
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/signup` | Public | Create account (name, identifier, password, role) |
| `POST` | `/auth/login` | Public | Login → returns JWT token |

### Products
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/product/catalog` | Public | List all products |
| `GET` | `/product/detail/{id}` | Optional | Product detail (tracks view event if logged in) |
| `GET` | `/product/type/{type}` | JWT | Filter by product type |
| `POST` | `/product/add` | Merchant | Add new product |

### Cart & Checkout
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/checkout/` | Customer/AI | Process checkout with discount |

### Orders
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/order/my-orders` | JWT | Get current user's orders |
| `GET` | `/order/all` | Merchant | Get all orders |
| `PATCH` | `/order/{id}/status` | Merchant | Update order status |

### AI Chat
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/chat/message` | Public | Send message to customer AI agent |
| `POST` | `/chat/event` | Public | Fire behavioral event (idle, viewed, payment) |

### Payments
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/payment/create-order` | Public | Create Razorpay order |
| `POST` | `/api/payment/verify` | Public | Verify payment signature |
| `GET` | `/api/payment/status/{user_id}` | Public | Check payment status |
| `POST` | `/api/payment/webhook` | Public | Razorpay webhook receiver |

### Merchant Dashboard
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/merchant/analytics` | Merchant | Business metrics & trends |
| `GET` | `/merchant/audit-logs` | Merchant | Financial audit trail |
| `GET` | `/merchant/chat-threads` | Merchant | All customer chat transcripts |
| `GET` | `/merchant/orders` | Merchant | All orders with details |
| `POST` | `/merchant/chat` | Merchant | Chat with merchant AI agent |

### A2A Protocol
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/.well-known/agent-card.json` | Public | Agent capability discovery |
| `POST` | `/a2a/start_session` | Public | Create agent session token |
| `GET` | `/a2a/catalog` | Public | Machine-readable product catalog |
| `POST` | `/a2a/interact/message:send` | Public | JSON-RPC agent interaction |

---

## 🗄 Database Schema

### PostgreSQL (Relational — via Neon)

```
┌──────────────┐       ┌──────────────────────┐
│     User     │       │       Product         │
├──────────────┤       ├──────────────────────┤
│ id (PK)      │       │ id (PK)              │
│ name         │       │ name                 │
│ role (enum)  │       │ price                │
│ identifier   │◄──┐   │ cost_price           │
│ password_hash│   │   │ min_profit_margin_%  │
│ address      │   │   │ stock                │
│ created_at   │   │   │ type (enum)          │
└──────┬───────┘   │   │ brand, gender, sizes │
       │           │   │ description          │
       │1:N        │   │ rating, discount     │
       ▼           │   │ image_url            │
┌──────────────┐   │   │ importance_score     │
│    Order     │   │   └──────┬──────┬────────┘
├──────────────┤   │          │      │
│ id (PK)      │   │          │1:N   │M:N
│ product_id(FK)───┘          │      │
│ user_id (FK) │              │      ▼
│ discount_%   │              │  ┌───────────────────┐
│ status       │              │  │CampaignProductLink│
│ razorpay_*   │              │  ├───────────────────┤
│ payment_link │              │  │ campaign_id (FK)  │
│ created_at   │              │  │ product_id  (FK)  │
└──────────────┘              │  └─────────┬─────────┘
                              │            │
┌──────────────┐              │            │
│     Cart     │              │            ▼
├──────────────┤              │  ┌─────────────────┐
│ id (PK)      │              │  │    Campaign      │
│ user_id (FK) │  unique      │  ├─────────────────┤
│ created_at   │              │  │ id (PK)         │
│ updated_at   │              │  │ agenda          │
└──────┬───────┘              │  │ discount_%      │
       │1:N                   │  │ priority        │
       ▼                      │  │ type (enum)     │
┌──────────────┐              │  │ total_items_sold│
│  CartItem    │              │  │ total_products  │
├──────────────┤              │  └─────────────────┘
│ id (PK)      │              │
│ cart_id (FK)  │              │
│ product_id(FK)│              │
│ quantity     │              │
│ size         │              │  ┌─────────────────┐
│ added_at     │              │  │DiscountPolicy   │
└──────────────┘              │  ├─────────────────┤
                              │  │ id (PK)         │
┌──────────────┐              │  │ product_id (FK) │
│  UserEvent   │              │  │ base_discount_% │
├──────────────┤              │  │ max_discount_%  │
│ id (PK)      │              │  │ agent_step_%    │
│ user_id (FK) │              │  │ min_loyalty     │
│ product_id   │──────────────┘  │ min_qty         │
│ event_type   │                 └─────────────────┘
│ category     │
│ timestamp    │
└──────────────┘
```

### MongoDB (Document — via Atlas / local)

| Collection | Database | Purpose |
|---|---|---|
| `chat_threads` | `dukaan_chat` | Full chat transcripts with nested messages and thread state |
| `audit_logs` | `dukaan_audit` | Financial action audit trail (discounts, orders, payments) |
| `checkpoints` | `langgraph` | LangGraph agent memory checkpoints (per-thread) |

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** and **npm**
- **PostgreSQL** (or a Neon serverless account)
- **MongoDB** (local or Atlas)
- API keys for: OpenRouter, Pinecone, HuggingFace, Razorpay

### 1. Clone the repository

```bash
git clone https://github.com/Tanishq112005/Dukaan-Avbodh.git
cd Dukaan-Avbodh
```

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
```

### 4. Configure Environment Variables

Create `backend/.env` and `frontend/.env` files (see [Environment Variables](#-environment-variables) section).

---

## 🔐 Environment Variables

### Backend (`backend/.env`)

```env
# ─── Database ───
DATABASE_URL=postgresql://user:pass@host/dbname       # Neon PostgreSQL connection string
MONGODB_URL=mongodb+srv://user:pass@cluster/db         # MongoDB Atlas (or mongodb://localhost:27017)

# ─── AI / LLM ───
OPEN_ROUTER_KEYS=sk-or-v1-xxxx                         # OpenRouter API key (primary LLM gateway)
GOOGLE_API_KEY=AIza...                                 # Google Gemini API key (optional)
GROQ_API_KEY=gsk_xxxx                                  # Groq API key (optional)
OPEN_API_KEY=sk-xxxx                                   # OpenAI API key (optional)

# ─── Embeddings & Vector Search ───
HUGGINGFACE_API_KEY=hf_xxxx                            # HuggingFace API key
PINECONE_API_KEY=pc-xxxx                               # Pinecone API key

# ─── MCP Servers ───
MCP_USER_SERVER_URL=http://127.0.0.1:8001/sse          # User MCP server URL
MCP_MERCHANT_SERVER_URL=http://127.0.0.1:8002/sse      # Merchant MCP server URL
FASTMCP_TOKEN=                                         # Optional auth token for MCP

# ─── Payments ───
RAZORPAY_KEY_ID=rzp_test_xxxx                          # Razorpay Key ID
RAZORPAY_KEY_SECRET=xxxx                               # Razorpay Key Secret

# ─── Auth ───
JWT_SECRET=your-secret-key                             # JWT signing secret

# ─── Frontend ───
FRONTEND_URL=http://localhost:5173                     # CORS allowed origin
```

### Frontend (`frontend/.env`)

```env
VITE_CLERK_PUBLISHABLE_KEY=pk_test_xxxx                # Clerk publishable key
CLERK_SECRET_KEY=sk_test_xxxx                          # Clerk secret key
VITE_API_URL=http://localhost:8000                     # Backend API URL
VITE_RAZORPAY_KEY_ID=rzp_test_xxxx                     # Razorpay key (for checkout widget)
```

---

## ▶️ Running the Application

You need **three terminal windows** to run the full stack:

### Terminal 1 — MCP Tool Servers

```bash
cd backend

# Start User MCP Server (port 8001)
python -m mcp.mcp_server_user.main &

# Start Merchant MCP Server (port 8002)
python -m mcp.mcp_server_merchant.main &
```

> **Note:** On Windows, run each command in a separate terminal instead of using `&`.

### Terminal 2 — FastAPI Backend

```bash
cd backend

# Start the FastAPI server (port 8000)
uvicorn main:app --reload --port 8000
```

The startup sequence will:
1. Initialize PostgreSQL (create tables + run migrations)
2. Initialize the LLM (OpenRouter) and embedding model (HuggingFace)
3. Connect to Pinecone vector database
4. Load MCP tools and compile the User Agent graph
5. Load MCP tools and compile the Merchant Agent graph
6. Connect to MongoDB

### Terminal 3 — React Frontend

```bash
cd frontend

# Start the dev server (port 5173)
npm run dev
```

### Access Points

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| User MCP Server | http://localhost:8001 |
| Merchant MCP Server | http://localhost:8002 |

---

## 🔗 A2A Protocol (Agent-to-Agent)

Dukaan implements Google's **Agent-to-Agent (A2A) protocol**, enabling external AI buyer agents to interact with the store programmatically:

### 1. Discover the Agent

```bash
curl https://your-domain.com/.well-known/agent-card.json
```

Returns the agent's capabilities: product discovery, cart management, negotiation, checkout.

### 2. Start a Session

```bash
curl -X POST https://your-domain.com/a2a/start_session
```

Returns a `chat_token` for subsequent interactions.

### 3. Browse the Catalog

```bash
curl https://your-domain.com/a2a/catalog
```

Returns a machine-readable product listing.

### 4. Interact via JSON-RPC

```bash
curl -X POST https://your-domain.com/a2a/interact/message:send \
  -H "Content-Type: application/json" \
  -d '{
    "params": {
      "message": {
        "parts": [{"text": "Show me jeans under 1000 rupees"}]
      },
      "metadata": {
        "context_id": "your-chat-token"
      }
    }
  }'
```

---

## 🌐 Deployment

The application is designed for deployment on:

- **Backend:** [Render](https://render.com) (FastAPI + MCP servers as background workers)
- **Frontend:** [Vercel](https://vercel.com) (with Vite build)
- **Database:** [Neon](https://neon.tech) (serverless PostgreSQL)
- **MongoDB:** [MongoDB Atlas](https://www.mongodb.com/atlas) (managed)
- **Vector DB:** [Pinecone](https://www.pinecone.io) (serverless)

### Build Commands

```bash
# Frontend production build
cd frontend
npm run build          # outputs to dist/

# Backend (no build step, use uvicorn directly)
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

<p align="center">
  Built with ❤️ by <strong>Tanishq</strong> — <em>Dukaan Avbodh</em>
</p>
