# 🧠 ProcureMind AI

## Agentic B2B Procurement Intelligence Platform

> **From raw RFQs and vendor quotations to explainable, auditable procurement decisions.**

ProcureMind AI is a production-style **AI-powered B2B procurement decision-support platform** that analyzes RFQs and multiple vendor quotations, validates procurement requirements, compares suppliers, ranks vendors, identifies risks, and generates explainable AI-assisted procurement recommendations.

Unlike a simple **“Upload PDF → Ask Chatbot”** application, ProcureMind combines:

**Document Intelligence → Deterministic Validation → Explainable Scoring → LangGraph Orchestration → LLM Reasoning → Human-in-the-Loop Approval → Persistent Audit History**

---

## 🚀 What ProcureMind Does

A buyer uploads:

- 📄 One RFQ PDF
- 📑 Multiple vendor quotation PDFs

ProcureMind automatically:

1. Extracts structured RFQ requirements
2. Parses multiple vendor quotations
3. Validates document completeness
4. Checks technical and commercial compliance
5. Calculates weighted vendor scores
6. Ranks suppliers
7. Generates an AI procurement recommendation
8. Performs risk analysis
9. Provides negotiation intelligence
10. Routes decisions through human approval
11. Stores procurement history
12. Generates downloadable procurement reports

---

## 🧠 Agentic Procurement Workflow

```text
RFQ PDF + Vendor Quotations
            │
            ▼
   ┌───────────────────┐
   │  RFQ Extraction   │
   └─────────┬─────────┘
             ▼
   ┌───────────────────┐
   │ Vendor Extraction │
   └─────────┬─────────┘
             ▼
   ┌───────────────────┐
   │  Data Validation  │
   └─────────┬─────────┘
             ▼
   ┌───────────────────┐
   │ Compliance Engine │
   └─────────┬─────────┘
             ▼
   ┌───────────────────┐
   │ Weighted Scoring  │
   └─────────┬─────────┘
             ▼
   ┌───────────────────┐
   │ AI Recommendation │
   └─────────┬─────────┘
             ▼
   ┌───────────────────┐
   │ Risk / HITL Gate  │
   └─────────┬─────────┘
             ▼
     PostgreSQL + Audit
```

The procurement pipeline is orchestrated using a **stateful LangGraph workflow** instead of relying on a single LLM call.

---

# 🏢 Multi-Role B2B Workflow

ProcureMind supports three major roles:

## 👤 Buyer

Buyers can:

- Upload RFQs
- Upload multiple vendor quotations
- Run procurement analyses
- Review vendor rankings
- Inspect technical compliance
- View AI recommendations
- Access Decision Intelligence
- View procurement history
- Download procurement reports

---

## ✅ Approver

Approvers provide the **Human-in-the-Loop (HITL)** decision layer.

They can:

- Review procurement cases
- Inspect recommended vendors
- Examine vendor scores
- Review AI reasoning
- Inspect procurement risk
- Approve or reject procurement decisions
- Maintain an auditable approval trail

---

## 🛡️ Admin

Admins provide organisation-level governance.

Capabilities include:

- User management
- Role management
- Procurement visibility
- Administrative controls
- B2B analytics
- Procurement governance

---

# 🧮 Explainable Vendor Scoring

ProcureMind does **not simply choose the cheapest vendor**.

Suppliers are evaluated using multiple procurement dimensions:

```text
Final Score =
    Price Score
  + Delivery Score
  + Technical Compliance Score
  + Supplier Performance Score
  + Warranty Score
```

This deterministic scoring engine provides a reliable foundation before LLM reasoning is applied.

---

# 🤖 AI Procurement Recommendation

The AI decision layer generates structured procurement intelligence including:

- 🏆 Recommended Vendor
- 📋 Executive Summary
- 💡 Why Selected
- 💪 Supplier Strengths
- ⚠️ Procurement Risks
- 🔍 Alternative Vendor Analysis
- 🤝 Negotiation Suggestions
- ✅ Final Decision Recommendation

Example decision:

```text
Recommended Vendor: Lenovo Enterprise
Final Score: 99.14
Decision: Approve with Conditions
```

---

# 🔥 Decision Intelligence

ProcureMind extends beyond basic vendor comparison.

### 📊 Supplier Performance

Analyzes supplier performance and procurement metrics.

### 🔄 What-If Simulation

Procurement teams can modify scoring priorities and observe how different weight configurations affect vendor rankings.

### 🔍 Explainability

Shows how individual procurement factors contribute to the final vendor score.

### ⚠️ Risk Intelligence

Provides procurement risk analysis for vendor decisions.

### 🤖 Procurement Copilot

Provides analysis-grounded AI assistance for procurement questions.

### 🤝 Negotiation Intelligence

Generates negotiation suggestions based on vendor pricing, warranty, delivery and commercial terms.

### 🧠 Agent Pipeline

Exposes stages of the AI procurement workflow for better transparency.

### 📜 Contract Intelligence

Supports contract-level procurement analytics.

### 📈 Spend Forecasting

Provides procurement spend forecasting capabilities.

---

# ⚡ Redis / Valkey Caching

ProcureMind integrates **Redis-compatible caching** for frequently requested procurement data.

Redis connectivity can be monitored through:

```http
GET /health/redis
```

The production Redis service is used to improve repeated data access and reduce unnecessary database operations.

---

# 🔐 Authentication & Authorization

ProcureMind implements:

- JWT Authentication
- Google Authentication
- Email/password authentication
- Role-Based Access Control
- Buyer authorization
- Approver authorization
- Admin authorization
- Protected procurement APIs

Privileged roles are controlled rather than freely assignable through public signup.

---

# 🛠 Technology Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI |
| Language | Python |
| Agent Orchestration | LangGraph |
| LLM Integration | LangChain / LLM APIs |
| PDF Processing | PyMuPDF |
| Validation | Pydantic |
| ORM | SQLAlchemy |
| Database | PostgreSQL |
| Cache | Redis / Valkey |
| Authentication | JWT + Google OAuth |
| Reporting | Automated PDF Reports |
| Deployment | Render |

---

# 📁 Project Architecture

```text
app/
│
├── api/
│   ├── auth_routes.py
│   ├── routes.py
│   ├── history_routes.py
│   ├── report_routes.py
│   └── b2b_routes.py
│
├── database/
│   └── models.py
│
├── dependencies/
│   └── role_dependencies.py
│
├── graph/
│   └── workflow.py
│
├── schemas/
│   ├── auth_schema.py
│   └── b2b_schema.py
│
├── services/
│   ├── llm_services.py
│   ├── langchain_services.py
│   └── b2b_intelligence.py
│
└── main.py
```

---

# 🌐 API Capabilities

## Authentication

```text
POST /auth/signup
POST /auth/login
POST /auth/google
GET  /auth/me
```

## Procurement AI

```text
POST /procurement/compare
POST /procurement/upload-rfq
POST /procurement/upload-vendor
POST /procurement/compare-pdf
POST /procurement/compare-multiple-pdfs
```

## Procurement History

```text
GET    /history
GET    /history/{analysis_id}
DELETE /history/{analysis_id}
```

## Reports

```text
GET /reports/{analysis_id}/pdf
```

## B2B Intelligence

```text
GET  /b2b/dashboard
GET  /b2b/supplier-performance

GET  /b2b/approvals
POST /b2b/approvals/{analysis_id}/decision

POST /b2b/analysis/{analysis_id}/what-if
GET  /b2b/analysis/{analysis_id}/explainability
GET  /b2b/analysis/{analysis_id}/risk
GET  /b2b/analysis/{analysis_id}/negotiation
POST /b2b/analysis/{analysis_id}/copilot
GET  /b2b/analysis/{analysis_id}/agent-pipeline

GET  /b2b/contracts
POST /b2b/contracts

GET  /b2b/forecast

GET   /b2b/admin/users
PATCH /b2b/admin/users/{user_id}/role
```

## Infrastructure Health

```text
GET /health
GET /health/redis
```

---

# 🏗 System Architecture

```text
┌───────────────────────────────┐
│ React + TypeScript Frontend   │
│ Buyer · Approver · Admin      │
└───────────────┬───────────────┘
                │
             REST + JWT
                │
                ▼
┌───────────────────────────────┐
│         FastAPI Backend       │
├───────────────────────────────┤
│ LangGraph Workflow            │
│ LLM Intelligence              │
│ PDF Extraction                │
│ Compliance Engine             │
│ Vendor Scoring                │
│ Risk & Explainability         │
│ RBAC / Approval Workflow      │
│ Reporting                     │
└──────────┬───────────┬────────┘
           │           │
           ▼           ▼
     PostgreSQL    Redis / Valkey
```

---

# 🚀 Local Setup

### Clone Repository

```bash
git clone https://github.com/KAVINGUPTA09/procuremind-ai-backend.git
cd procuremind-ai-backend
```

### Create Virtual Environment

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment Variables

Create a `.env` file containing the required database, authentication, LLM and Redis configuration.

Never commit `.env` or private credentials.

### Create Database Tables

```bash
python create_tables.py
```

### Start Backend

```bash
python -m uvicorn app.main:app --reload --port 8001
```

Swagger API documentation:

```text
http://127.0.0.1:8001/docs
```

---

# 🧪 Testing

Run automated tests using:

```bash
pytest
```

Recommended end-to-end test:

```text
Authentication
      ↓
Buyer Dashboard
      ↓
Upload RFQ + Vendor PDFs
      ↓
LangGraph Analysis
      ↓
Compliance + Vendor Ranking
      ↓
AI Recommendation
      ↓
Decision Intelligence
      ↓
History + PDF Report
      ↓
Approver Decision
      ↓
Admin / Analytics / Contracts
```

---

# 💡 Why ProcureMind Is Different

ProcureMind AI is **not another PDF chatbot**.

It demonstrates how AI can be integrated into a real enterprise decision workflow using:

- Agentic AI
- Stateful LangGraph orchestration
- Large Language Models
- Deterministic business logic
- Explainable vendor scoring
- Document intelligence
- Human-in-the-Loop approval
- Role-Based Access Control
- PostgreSQL persistence
- Redis caching
- Procurement analytics
- Production deployment

The LLM assists procurement reasoning while deterministic scoring and human review maintain transparency and control.

---

# 🖥 Frontend

The ProcureMind product interface is maintained separately:

**Frontend Repository:**  
`KAVINGUPTA09/procurewise-insight`

---

# 👨‍💻 Builder

## Kavin Gupta

**B.Tech CSE · AI/ML & Agentic AI**

Focus Areas:

`Agentic AI` · `Large Language Models` · `LangGraph` · `RAG` · `Multi-Agent Systems` · `Machine Learning` · `AI Automation`

GitHub: **KAVINGUPTA09**

LinkedIn: **kavin-gupta-509b8a321**

---

## ⚠️ Disclaimer

ProcureMind AI is a **decision-support platform**.

AI-generated recommendations are intended to assist authorised procurement professionals and should not replace organisational procurement policies, due diligence or human judgement.

---

<p align="center">
  <strong>🧠 ProcureMind AI</strong>
  <br>
  Agentic B2B Procurement Intelligence
</p>

<p align="center">
  FastAPI · LangGraph · PostgreSQL · Redis · LLMs
</p>
