# 3-Minute Judge Click-Path Demo Script

Follow this script to evaluate the core governance workflow from scratch in under 3 minutes.

### Step 1: Login & Role Selection (0:00 - 0:25)
1. Navigate to the homepage. Click the **"Creator (Team Social)"** demo login button.
2. Observe the role-tailored dashboard with active drafts and quick sample actions.

### Step 2: Ingest Sample & Run Review (0:25 - 0:55)
1. Click **"New Submission"**, then click **"Load Sample S1 (Unsupported Claims & Banned Terms)"**.
2. Notice the auto-assigned risk tier based on channel (`social` -> `low`).
3. Click **"Run Brand Review"**. Watch the deterministic stages progress via live status updates.

### Step 3: Inspect Findings & Guardrails (0:55 - 1:30)
1. On the Review Studio screen:
   - View green/blue highlighted text in the content editor.
   - Click the highlight on the banned word `"serum"`. Note the rule citation (`TERM-001`) and explanation.
   - Accept the suggested fix: notice the content immediately updates to `"Lumo Glow Concentrate"` and generates version 2.
   - Click the claim finding citing clinical trial `FACT-001`. Notice the cited validity date.
   - Click **Dismiss** and select `"Factual override supported by external lab doc"`.
2. Inspect the **Data Boundary** tab: verify that zero confidential information or unredacted keys were transmitted.

### Step 4: Submission & Reviewer Claim (1:30 - 2:10)
1. Click **"Submit for Review"**.
2. Log out and click **"Reviewer"** demo login.
3. Open the **Reviewer Queue**, locate the newly submitted item, and click **"Claim"**.
4. Add a comment on a finding, then click **"Request Changes"** or **"Approve"**.

### Step 5: Insights & Immutable Audit Log (2:10 - 3:00)
1. Log in as **"Brand Manager"**.
2. Navigate to **Insights**: observe recurring violations, team breakdown, and dismissal analytics.
3. Navigate to **Audit Log**: verify the cryptographic hash chain validating every action taken in steps 1 through 4.
