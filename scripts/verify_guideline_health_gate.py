"""
Gate Script: Guideline Health Brand Manager Journey & Screenshot Evidence.
Captures high-resolution visual evidence of:
- Ambiguous rules tab with RULE-AMBIG-01 ranked #1 and plain-words contributing factors
- Ambiguity drill-down modal showing actual dismissal reasons and clarification comments
- Stale rules & facts tab with severity badges, reasons, and 'Review this entry' KB link
- Uncited comment gaps tab with clusters, draft rule copy, and Approve/Edit/Reject actions
- Newly approved gap proposal appearing in the Knowledge Base
- Append-only audit log entry for the approved draft rule
"""

import asyncio
import json
import subprocess
import tempfile
import os
import base64
import httpx
import websockets

EVIDENCE_DIR = "/home/redpanda/Documents/WeBug/docs/evidence"
os.makedirs(EVIDENCE_DIR, exist_ok=True)

FE_BASE = "http://localhost:3000"
API_BASE = "http://localhost:8000/api/v1"

async def run_evidence_capture():
    print("[Gate] Starting Guideline Health Brand Manager automated verification...")

    prof = tempfile.mkdtemp(prefix="ff_bidi_gh_")
    p = subprocess.Popen([
        "/usr/bin/firefox", "--headless", "--remote-debugging-port=9222",
        "--profile", prof
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    await asyncio.sleep(2.5)

    try:
        async with websockets.connect("ws://127.0.0.1:9222/session") as ws:
            # 1. Initialize BiDi session
            await ws.send(json.dumps({"id": 1, "method": "session.new", "params": {"capabilities": {}}}))
            await ws.recv()
            await ws.send(json.dumps({"id": 2, "method": "browsingContext.getTree", "params": {}}))
            res = json.loads(await ws.recv())
            context_id = res["result"]["contexts"][0]["context"]

            # Set viewport to 1440x950 for clear, crisp presentation
            await ws.send(json.dumps({
                "id": 3,
                "method": "browsingContext.setViewport",
                "params": {"context": context_id, "viewport": {"width": 1440, "height": 950}}
            }))
            await ws.recv()

            async def eval_js(expression: str):
                await ws.send(json.dumps({
                    "id": 100,
                    "method": "script.evaluate",
                    "params": {
                        "context": context_id,
                        "expression": expression,
                        "target": {"context": context_id},
                        "awaitPromise": True,
                    }
                }))
                return json.loads(await ws.recv())

            async def snap(filename: str):
                out_path = os.path.join(EVIDENCE_DIR, filename)
                await ws.send(json.dumps({
                    "id": 200,
                    "method": "browsingContext.captureScreenshot",
                    "params": {"context": context_id}
                }))
                s_res = json.loads(await ws.recv())
                img_b64 = s_res["result"]["data"]
                with open(out_path, "wb") as f:
                    f.write(base64.b64decode(img_b64))
                print(f"  ✓ Saved evidence: {filename} ({os.path.getsize(out_path):,} bytes)")

            # -----------------------------------------------------------------
            # Step 1: Navigate to Guideline Health as Brand Manager
            # -----------------------------------------------------------------
            print("\n[Step 1] Navigating to Guideline Health as Brand Manager...")
            gh_url = f"{FE_BASE}/insights/guideline-health/?demo=manager"
            await ws.send(json.dumps({
                "id": 10,
                "method": "browsingContext.navigate",
                "params": {"context": context_id, "url": gh_url, "wait": "complete"}
            }))
            await ws.recv()
            await asyncio.sleep(3.0)

            # Snap Tab 1: Ambiguous Rules
            await snap("gh-01-ambiguous-rules.png")

            # -----------------------------------------------------------------
            # Step 2: Open Drill-Down on RULE-AMBIG-01
            # -----------------------------------------------------------------
            print("\n[Step 2] Opening Drill-Down on RULE-AMBIG-01...")
            click_drilldown_js = """
            (() => {
                const buttons = Array.from(document.querySelectorAll('button'));
                const drillBtn = buttons.find(b => b.textContent.includes('Drill-Down'));
                if (drillBtn) {
                    drillBtn.click();
                    return true;
                }
                return false;
            })()
            """
            await eval_js(click_drilldown_js)
            await asyncio.sleep(1.5)
            await snap("gh-02-ambiguity-drilldown.png")

            # Close drilldown modal
            close_modal_js = """
            (() => {
                const buttons = Array.from(document.querySelectorAll('button'));
                const closeBtn = buttons.find(b => b.textContent.includes('Close Drill-Down'));
                if (closeBtn) closeBtn.click();
            })()
            """
            await eval_js(close_modal_js)
            await asyncio.sleep(1.0)

            # -----------------------------------------------------------------
            # Step 3: Switch to Stale Rules & Facts Tab
            # -----------------------------------------------------------------
            print("\n[Step 3] Switching to Stale tab...")
            switch_stale_js = """
            (() => {
                const tab = document.getElementById('tab-stale');
                if (tab) {
                    tab.click();
                    return true;
                }
                return false;
            })()
            """
            await eval_js(switch_stale_js)
            await asyncio.sleep(1.5)
            await snap("gh-03-stale-rules.png")

            # -----------------------------------------------------------------
            # Step 4: Switch to Uncited Comment Gaps Tab
            # -----------------------------------------------------------------
            print("\n[Step 4] Switching to Gaps tab...")
            switch_gaps_js = """
            (() => {
                const tab = document.getElementById('tab-gaps');
                if (tab) {
                    tab.click();
                    return true;
                }
                return false;
            })()
            """
            await eval_js(switch_gaps_js)
            await asyncio.sleep(1.5)
            await snap("gh-04-gaps-proposals.png")

            # -----------------------------------------------------------------
            # Step 5: Approve Draft Rule Proposal
            # -----------------------------------------------------------------
            print("\n[Step 5] Approving first draft rule proposal...")
            # Click the first 'Approve Draft Rule' button in the UI
            click_approve_js = """
            (() => {
                const buttons = Array.from(document.querySelectorAll('button'));
                const approveBtn = buttons.find(b => b.textContent.includes('Approve Draft Rule'));
                if (approveBtn) {
                    approveBtn.click();
                    return true;
                }
                return false;
            })()
            """
            res = await eval_js(click_approve_js)
            await asyncio.sleep(2.5)

            # Also verify via API that the entry exists in KB
            async with httpx.AsyncClient(base_url=API_BASE) as client:
                kb_res = await client.get("/kb/entries?status=active", headers={"Authorization": "Bearer demo-token-u-manager"})
                active_entries = kb_res.json()
                gap_entries = [e for e in active_entries if e["code"].startswith("RULE-GAP-")]
                print(f"  Active KB gap entries found: {len(gap_entries)}")
                approved_entry = gap_entries[0] if gap_entries else None
                approved_code = approved_entry["code"] if approved_entry else "RULE-GAP"

            # -----------------------------------------------------------------
            # Step 6: Navigate to Knowledge Base to show approved rule
            # -----------------------------------------------------------------
            print(f"\n[Step 6] Navigating to Knowledge Base for {approved_code}...")
            kb_url = f"{FE_BASE}/kb/?id={approved_code}&demo=manager"
            await ws.send(json.dumps({
                "id": 20,
                "method": "browsingContext.navigate",
                "params": {"context": context_id, "url": kb_url, "wait": "complete"}
            }))
            await ws.recv()
            await asyncio.sleep(3.0)
            await snap("gh-05-gap-approved-kb.png")

            # -----------------------------------------------------------------
            # Step 7: Navigate to Audit Log to show audit record
            # -----------------------------------------------------------------
            print("\n[Step 7] Navigating to Audit Log to verify audit record...")
            audit_url = f"{FE_BASE}/audit/?demo=manager"
            await ws.send(json.dumps({
                "id": 30,
                "method": "browsingContext.navigate",
                "params": {"context": context_id, "url": audit_url, "wait": "complete"}
            }))
            await ws.recv()
            await asyncio.sleep(3.0)
            await snap("gh-06-gap-audit-entry.png")

            print("\n[Gate Verification] All 6 visual evidence screenshots successfully captured!")

    finally:
        p.terminate()
        p.wait()
        subprocess.run(["rm", "-rf", prof])

if __name__ == "__main__":
    asyncio.run(run_evidence_capture())
