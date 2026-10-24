"""
Capture visual evidence screenshots for Gate G1 using headless Firefox.
"""

import os
import time
import subprocess
import tempfile

BASE_URL = "http://localhost:3000"
EVIDENCE_DIR = "/home/redpanda/Documents/WeBug/docs/evidence"

def capture(url: str, output_path: str, width: int = 1440, height: int = 900, delay: float = 2.0):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    prof_dir = tempfile.mkdtemp(prefix="ff_g1_prof_")
    
    cmd = [
        "/usr/bin/firefox",
        "--headless",
        f"--window-size={width},{height}",
        f"--screenshot={output_path}",
        url,
        "--profile",
        prof_dir,
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        time.sleep(delay)
        print(f"Captured: {output_path} ({os.path.getsize(output_path)} bytes)")
    except Exception as e:
        print(f"Failed to capture {url}: {e}")
    finally:
        subprocess.run(["rm", "-rf", prof_dir])

def main():
    print("Capturing Gate G1 Evidence Screenshots...")

    # 1. Creator Dashboard with progress checklist & sample buttons
    capture(f"{BASE_URL}/dashboard?demo=creator", f"{EVIDENCE_DIR}/g1-01-dashboard-creator.png")

    # 2. Submissions List showing the live submissions
    capture(f"{BASE_URL}/submissions?demo=creator", f"{EVIDENCE_DIR}/g1-02-submissions-list.png")

    # 3. Submission Detail (using the high-risk submission we verified or sample S1)
    capture(f"{BASE_URL}/submission?id=sub-sample-s1&demo=creator", f"{EVIDENCE_DIR}/g1-03-submission-detail-creator.png")

    # 4. Reviewer Queue showing claimed and unassigned items
    capture(f"{BASE_URL}/queue?demo=reviewer", f"{EVIDENCE_DIR}/g1-04-reviewer-queue.png")

    # 5. Knowledge Base showing facts with Version 2 and tier badges
    capture(f"{BASE_URL}/kb?demo=admin&type=fact", f"{EVIDENCE_DIR}/g1-05-kb-facts-admin.png")

    # 6. Agency Creator view (strictly public tier only)
    capture(f"{BASE_URL}/kb?demo=agency", f"{EVIDENCE_DIR}/g1-06-kb-agency-public-only.png")

    # 7. Audit Log showing SHA-256 chained rows
    capture(f"{BASE_URL}/audit?demo=manager", f"{EVIDENCE_DIR}/g1-07-audit-trail-chained.png")

    print("Gate G1 Screenshot capture complete!")

if __name__ == "__main__":
    main()
