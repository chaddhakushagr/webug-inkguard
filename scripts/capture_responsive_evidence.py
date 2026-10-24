"""
Capture responsive screenshots at 1280px, 1024px, 768px, and 390px widths
for the core screens to satisfy Gate / Phase visual QA requirements.
"""

import asyncio
import json
import subprocess
import tempfile
import os
import base64
import websockets

EVIDENCE_DIR = "/home/redpanda/Documents/WeBug/docs/evidence"
os.makedirs(EVIDENCE_DIR, exist_ok=True)

TARGETS = [
    # 1. Login across all 4 widths
    ("http://localhost:3000/", f"{EVIDENCE_DIR}/resp-1280-login.png", 1280, 900),
    ("http://localhost:3000/", f"{EVIDENCE_DIR}/resp-1024-login.png", 1024, 900),
    ("http://localhost:3000/", f"{EVIDENCE_DIR}/resp-768-login.png", 768, 900),
    ("http://localhost:3000/", f"{EVIDENCE_DIR}/resp-390-login.png", 390, 844),

    # 2. Dashboard across all 4 widths
    ("http://localhost:3000/dashboard/?demo=creator", f"{EVIDENCE_DIR}/resp-1280-dashboard.png", 1280, 900),
    ("http://localhost:3000/dashboard/?demo=creator", f"{EVIDENCE_DIR}/resp-1024-dashboard.png", 1024, 900),
    ("http://localhost:3000/dashboard/?demo=creator", f"{EVIDENCE_DIR}/resp-768-dashboard.png", 768, 900),
    ("http://localhost:3000/dashboard/?demo=creator", f"{EVIDENCE_DIR}/resp-390-dashboard.png", 390, 844),

    # 3. Submission Detail across all 4 widths
    ("http://localhost:3000/submission/?id=sub-sample-s1&demo=creator", f"{EVIDENCE_DIR}/resp-1280-submission.png", 1280, 950),
    ("http://localhost:3000/submission/?id=sub-sample-s1&demo=creator", f"{EVIDENCE_DIR}/resp-1024-submission.png", 1024, 950),
    ("http://localhost:3000/submission/?id=sub-sample-s1&demo=creator", f"{EVIDENCE_DIR}/resp-768-submission.png", 768, 950),
    ("http://localhost:3000/submission/?id=sub-sample-s1&demo=creator", f"{EVIDENCE_DIR}/resp-390-submission.png", 390, 844),

    # 4. Knowledge Base across all 4 widths
    ("http://localhost:3000/kb/?demo=creator", f"{EVIDENCE_DIR}/resp-1280-kb.png", 1280, 950),
    ("http://localhost:3000/kb/?demo=creator", f"{EVIDENCE_DIR}/resp-1024-kb.png", 1024, 950),
    ("http://localhost:3000/kb/?demo=creator", f"{EVIDENCE_DIR}/resp-768-kb.png", 768, 950),
    ("http://localhost:3000/kb/?demo=creator", f"{EVIDENCE_DIR}/resp-390-kb.png", 390, 844),

    # 5. Insights across all 4 widths
    ("http://localhost:3000/insights/?demo=manager", f"{EVIDENCE_DIR}/resp-1280-insights.png", 1280, 950),
    ("http://localhost:3000/insights/?demo=manager", f"{EVIDENCE_DIR}/resp-1024-insights.png", 1024, 950),
    ("http://localhost:3000/insights/?demo=manager", f"{EVIDENCE_DIR}/resp-768-insights.png", 768, 950),
    ("http://localhost:3000/insights/?demo=manager", f"{EVIDENCE_DIR}/resp-390-insights.png", 390, 844),

    # 6. About AI screen (Desktop + Mobile)
    ("http://localhost:3000/about-ai/?demo=creator", f"{EVIDENCE_DIR}/resp-1280-about-ai.png", 1280, 900),
    ("http://localhost:3000/about-ai/?demo=creator", f"{EVIDENCE_DIR}/resp-390-about-ai.png", 390, 844),
]

async def capture_all():
    print(f"Capturing responsive evidence across {len(TARGETS)} targets...")
    prof = tempfile.mkdtemp(prefix="ff_bidi_resp_")
    p = subprocess.Popen([
        "/usr/bin/firefox", "--headless", "--remote-debugging-port=9222",
        "--profile", prof
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    await asyncio.sleep(2.0)
    try:
        async with websockets.connect("ws://127.0.0.1:9222/session") as ws:
            # Init session
            await ws.send(json.dumps({"id": 1, "method": "session.new", "params": {"capabilities": {}}}))
            await ws.recv()
            await ws.send(json.dumps({"id": 2, "method": "browsingContext.getTree", "params": {}}))
            res = json.loads(await ws.recv())
            context_id = res["result"]["contexts"][0]["context"]

            for url, out_path, width, height in TARGETS:
                # Set viewport
                await ws.send(json.dumps({
                    "id": 10,
                    "method": "browsingContext.setViewport",
                    "params": {"context": context_id, "viewport": {"width": width, "height": height}}
                }))
                await ws.recv()

                # Navigate
                await ws.send(json.dumps({
                    "id": 11,
                    "method": "browsingContext.navigate",
                    "params": {"context": context_id, "url": url, "wait": "complete"}
                }))
                await ws.recv()
                await asyncio.sleep(2.5)

                # Capture
                await ws.send(json.dumps({
                    "id": 12,
                    "method": "browsingContext.captureScreenshot",
                    "params": {"context": context_id}
                }))
                s_res = json.loads(await ws.recv())
                img_b64 = s_res["result"]["data"]
                with open(out_path, "wb") as f:
                    f.write(base64.b64decode(img_b64))
                print(f"  [PASS] {os.path.basename(out_path)} ({width}x{height}) -> {os.path.getsize(out_path)} bytes")

    finally:
        p.terminate()
        p.wait()
        subprocess.run(["rm", "-rf", prof])

if __name__ == "__main__":
    asyncio.run(capture_all())
