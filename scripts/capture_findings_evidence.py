"""
Capture visual evidence screenshots for Phase 2B (Submission Details & Findings Triage)
for samples S1 through S5 using headless Firefox.
"""

import os
import time
import subprocess
import tempfile

BASE_URL = "http://localhost:3000"
EVIDENCE_DIR = "/home/redpanda/Documents/WeBug/docs/evidence"

def capture(url: str, output_path: str, width: int = 1440, height: int = 950, delay: float = 3.0):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    prof_dir = tempfile.mkdtemp(prefix="ff_findings_prof_")
    
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
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=25)
        time.sleep(delay)
        size = os.path.getsize(output_path)
        print(f"Captured: {output_path} ({size} bytes)")
    except Exception as e:
        print(f"Failed to capture {url}: {e}")
    finally:
        subprocess.run(["rm", "-rf", prof_dir])

def main():
    print("Capturing Phase 2B Findings Evidence Screenshots for Samples S1 to S5...")

    samples = [
        ("sub-sample-s1", "findings-s1.png", "Sample S1: Unsupported Claims & Disclaimers"),
        ("sub-sample-s2", "findings-s2.png", "Sample S2: Off-Tone Marketing Copy"),
        ("sub-sample-s3", "findings-s3.png", "Sample S3: Clean & Fully Compliant Announcement"),
        ("sub-sample-s4", "findings-s4.png", "Sample S4: Confidential Launch Term Leak"),
        ("sub-sample-s5", "findings-s5.png", "Sample S5: Prompt Injection Security Test"),
    ]

    for sub_id, filename, label in samples:
        url = f"{BASE_URL}/submission/?id={sub_id}&demo=creator"
        out_path = f"{EVIDENCE_DIR}/{filename}"
        print(f"\nCapturing {label} -> {out_path}...")
        capture(url, out_path, delay=2.5)

    print("\nPhase 2B Visual Evidence capture complete!")

if __name__ == "__main__":
    main()
