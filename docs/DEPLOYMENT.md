# Deployment Guide: Free Cloud Deployment (Neon Postgres + Render Web Service)

This guide provides step-by-step instructions to deploy **Inkguard** to a zero-cost cloud environment with **no credit card required**, utilizing:
1. **Neon Serverless PostgreSQL** (Permanent free tier, 1 GB storage, no credit card).
2. **Render Web Service** (Hobby free tier, 750 free instance hours/month, 512 MB RAM, no credit card).

---

## Before-You-Deploy Checklist

> [!IMPORTANT]
> **CRITICAL PRE-DEPLOYMENT SAFETY CHECKS**
> 1. **Run Prompt L1 First**: Verify all unit and integration tests pass locally before deploying (`python manage.py test && python manage.py arch`).
> 2. **Never Commit Secrets to Git**: All API keys and credentials (`DATABASE_URL`, `JWT_SECRET`, `LLM_API_KEY`) must **only** be set via host environment variables in Render's dashboard. Never push a `.env` file or commit secrets to the repository.
> 3. **Verify Git Hygiene**: Ensure `git status` shows `.env` is ignored and uncommitted.

---

## Provider Limits & Verification (Verified 24 Oct 2026)

| Provider | Service | Free Tier Limits | Expiration & Idle Policy | Official Docs Reference |
| :--- | :--- | :--- | :--- | :--- |
| **Neon** | Serverless Postgres | 1 GB storage, 100 CU-hrs/mo, 2 CU compute | **Permanent**; scales compute to zero after 5 min idle (handled by automatic reconnect retry) | [Neon Free Tier](https://neon.tech/docs/introduction/plans#free-tier) |
| **Render** | Web Service | 512 MB RAM, 0.1 CPU, 750 instance hrs/mo | **Permanent**; spins down after 15 min idle (handled by frontend Cold-Start UX banner) | [Render Free Plans](https://render.com/docs/free) |

> [!WARNING]
> **Do NOT use Render's Free PostgreSQL Database**: Render free databases expire and are deleted after 30 days. Neon's free tier is permanent and does not expire.

---

## Step 1: Create Free Neon PostgreSQL Database

1. Navigate to [https://neon.tech](https://neon.tech) and click **Sign Up** (sign in using your GitHub or Google account; **no credit card required**).
2. In the Neon Console, click **New Project**:
   * **Project Name**: `inkguard-prod`
   * **Postgres Version**: `16` (default)
   * **Region**: Choose `US East (Ohio)` or `US East (Oregon)` (match your Render region to minimize latency).
   * Click **Create Project**.
3. Once created, the **Connection Details** modal will appear:
   * Select **Connection string**.
   * Toggle **Pooled connection** (recommended for serverless) or **Direct connection**.
   * Ensure `sslmode=require` is present at the end of the URI.
4. Copy the complete connection string:
   ```text
   postgresql://[user]:[password]@[host]/neondb?sslmode=require
   ```
   *(Keep this string copied; you will paste it into Render in Step 2).*

---

## Step 2: Deploy Web Service to Render

### Option A: Native Python Runtime (Recommended for Fast Builds)

Because Render free tier has a 512 MB build RAM limit, using Render's native Python runtime with the pre-compiled frontend in `backend/app/static/` avoids build timeouts:

1. Sign up or log in at [https://render.com](https://render.com) using your GitHub account.
2. Click **New +** in the top navigation and select **Web Service**.
3. Select **Build and deploy from a Git repository** and connect your `WeBug` repository.
4. Configure service parameters:
   * **Name**: `inkguard`
   * **Region**: `Oregon (US West)` or `Ohio (US East)` (match your Neon region)
   * **Branch**: `main`
   * **Root Directory**: Leave blank (repository root)
   * **Runtime**: `Python 3`
   * **Build Command**: `pip install -r backend/requirements.txt`
   * **Start Command**: `uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT`
   * **Instance Type**: `Free` ($0/month)

### Option B: Docker Runtime via Multi-Stage Dockerfile

If you prefer building both frontend and backend within Docker:
1. Follow steps 1–3 above.
2. Choose **Runtime**: `Docker`.
3. Render will automatically detect the root [Dockerfile](file:///home/redpanda/Documents/WeBug/Dockerfile) and build both the Next.js static export and Python server.

---

## Step 3: Configure Environment Variables in Render

In your Render Web Service dashboard, click the **Environment** tab on the left sidebar and configure the following variables:

| Variable Name | Required | Is Secret? | Value / Example | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `APP_ENV` | Yes | No | `production` | Enables production error logging and static file serving. |
| `DATABASE_URL` | Yes | **YES** | `postgresql://...neondb?sslmode=require` | Your Neon connection string copied in Step 1. |
| `JWT_SECRET` | Yes | **YES** | *(Click "Generate" or enter 32+ random characters)* | Cryptographic HMAC secret for signing JWT session tokens. |
| `DEMO_MODE` | Yes | No | `true` | Enables persona role-switching and judge demo accounts. |
| `DEMO_PASSWORD` | Yes | **YES** | `LumoDemo2026!` | Universal password for seeded demo persona logins. |
| `NEXT_PUBLIC_API_BASE` | Yes | No | `/api/v1` | Same-origin API endpoint (eliminates CORS). |
| `LLM_MODE` | Yes | No | `mock` *(or `live` once key is added)* | Review engine mode. `mock` operates 100% offline. |
| `LLM_API_KEY` | Optional | **YES** | *(Paste Google AI Studio API key if `live`)* | Required only for live Gemini calls. Never commit to git. |
| `LLM_BASE_URL` | Yes | No | `https://generativelanguage.googleapis.com/v1beta/openai/` | Google AI Studio OpenAI-compatible endpoint. |
| `LLM_MODEL` | Yes | No | `gemini-2.5-flash` | Free-tier compatible high-speed model identifier. |
| `LLM_DAILY_CAP` | Yes | No | `100` | Hard stop threshold protecting free AI Studio quotas. |
| `MAX_CONTENT_CHARS` | Yes | No | `20000` | Input size guard returning 413 on oversized copy. |
| `RATE_LIMIT_REVIEWS_PER_HOUR` | Yes | No | `60` | DoS protection returning 429 on excessive requests. |
| `CORS_ORIGINS` | No | No | `*` | Allowed CORS origins (not needed when using same-origin `/api/v1`). |
| `ALLOW_SEED_RESET` | Yes | No | `false` | Prevents unauthorized external database wiping in production. |

Click **Save Changes**. Render will automatically trigger the initial deployment.

---

## Step 4: Verify Initial Startup & Auto-Seeding

1. In Render's dashboard, click **Logs**.
2. Watch the startup sequence. You will observe:
   ```text
   INFO: Waiting for application startup.
   [Database] Connection established successfully (attempt 1).
   INFO [alembic.runtime.migration] Context impl PostgresqlImpl.
   [Database] Alembic migrations applied successfully to head.
   [Database] Database is empty. Loading initial brand seed...
   [Seed] 1. Loading teams...
   [Seed] 2. Loading users (8 demo personas)...
   [Seed] 3. Loading Lumo brand knowledge base (~45 curated entries)...
   [Seed] 4. Loading sample submissions (S1 to S5)...
   [Seed] 5. Loading synthetic review history (8 weeks, 4 teams, 80 reviews)...
   [Database] Initial brand seed loaded successfully.
   INFO: Application startup complete.
   INFO: Uvicorn running on http://0.0.0.0:10000 (Press CTRL+C to quit)
   ```
3. Copy your live Render URL (e.g., `https://inkguard.onrender.com`).

---

## Step 5: (Optional) Keep-Alive Ping via GitHub Actions

Render free web services spin down after 15 minutes of inactivity. To keep your instance warm during judge review:

1. In your GitHub repository, navigate to **Settings** > **Secrets and variables** > **Actions**.
2. Click **New repository secret**:
   * **Name**: `APP_URL`
   * **Value**: Your Render live URL (e.g., `https://inkguard.onrender.com`).
3. Click **Add secret**.
4. The scheduled workflow [.github/workflows/keep_alive.yml](file:///home/redpanda/Documents/WeBug/.github/workflows/keep_alive.yml) will ping `/api/v1/health` every 10 minutes to prevent idle spin-down.

---

## Step 6: Post-Deployment Verification (Golden Path Walkthrough)

Open your live deployment URL in an **Incognito / Private browser window** and verify the end-to-end flow:

1. **Cold-Start Verification**: If the instance is sleeping, verify the top banner displays:
   > *"Waking the server, this can take about a minute"*
2. **Health Check**:
   ```bash
   curl -i https://[your-subdomain].onrender.com/api/v1/health
   # Expected: HTTP 200 OK {"status":"healthy","version":"0.2.0","ai_mode":"mock"}
   ```
3. **Automated E2E Verification**:
   ```bash
   python manage.py e2e --base-url https://[your-subdomain].onrender.com
   ```
4. **Judge Golden Path (GP-1 to GP-6)**:
   * Click **Elena Chen (Creator)** demo card on the login screen.
   * On the Dashboard, click **Sample S1: Lumo Summer Social Campaign**.
   * Click **Run Governance Review** (completes in Mock mode; live stage ticker displays).
   * Review findings in the content view, click **Dismiss** or **Accept** on suggestions.
   * Click **Submit for Review**.
   * Switch role in header to **Sarah Jenkins (Reviewer)**.
   * Open the submitted campaign from the Reviewer Queue and click **Claim Review**.
   * Click **Approve**.
   * Switch role back to **Elena Chen (Creator)** and click **Mark Published**.

---

## How to Redeploy

* **Automatic Deployments**: Any push to the `main` branch on GitHub automatically triggers a redeploy on Render.
* **Manual Redeployment**:
  1. Open your Render dashboard.
  2. Click **Manual Deploy** in the top right.
  3. Select **Clear build cache & deploy** to force a clean re-installation.
