# ProcureMind B2B Intelligence Upgrade

This bundle extends the existing deployed ProcureMind architecture. It does **not** replace PostgreSQL, Valkey/Redis, FastAPI, LangGraph, React/TanStack, or Render deployment.

## Backend additions

- Buyer / Approver / Admin role guards
- Human approval workflow and approval audit records
- Organisation-wide B2B spend dashboard endpoint
- Supplier performance analytics
- What-if scoring simulator with configurable live weights
- Explainable score contribution breakdown
- Rule-based risk / suspicious quotation signals
- Analysis-grounded AI Copilot using the existing Groq/LangChain model
- Negotiation playbook + vendor email draft
- Visible agent-pipeline API
- Contract analytics + expiry alerts
- Directional 3-month spend forecasting
- Admin user/role management APIs
- Public signup locked to `buyer`; admin promotes trusted users

## Frontend update bundle

Copy the `src/` folder from `procurewise-insight-b2b-update.zip` over the existing frontend `src/` folder. It only replaces/adds the listed files; the rest of the current GitHub frontend stays untouched.

New routes:
- `/analytics`
- `/contracts`
- `/approver-dashboard`
- `/admin-dashboard`
- `/intelligence/$analysisId`

The existing `/analysis/$analysisId` page gets a **Decision Intelligence** button.

## First admin

Public signup is buyer-only for security. Promote one existing account once:

```powershell
python scripts/set_user_role.py your-email@example.com admin
```

Then the admin can promote other users from the Admin Dashboard.

## Local backend check

```powershell
python -m uvicorn app.main:app --reload --port 8001
```

Open `/docs` and verify the `B2B Procurement Intelligence` endpoints.

## Local frontend check

```powershell
npm install
npm run dev
```

TanStack generates the new route tree during dev/build.

## Production deploy

After local testing, commit backend and frontend separately. Render should redeploy the GitHub-connected services. `Base.metadata.create_all()` will create the **new** `approval_records` and `contract_records` tables without replacing existing procurement tables.

Do not commit `.env`, local uploads, `.venv`, or generated reports.
