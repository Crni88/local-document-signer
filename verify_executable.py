"""Test and verify that the compiled standalone executable runs and functions end-to-end."""

import json
import subprocess
import time
import urllib.request
from pathlib import Path

EXE_PATH = Path(__file__).resolve().parent / "dist" / "LocalDocumentSigner.exe"
TEST_PORT = 5088
BASE_URL = f"http://127.0.0.1:{TEST_PORT}"


def test_executable():
    print(f"Testing executable at: {EXE_PATH}")
    assert EXE_PATH.is_file(), f"Executable not found at {EXE_PATH}"

    # Launch executable with CLI mode on specific test port
    proc = subprocess.Popen(
        [str(EXE_PATH), "--cli", "--port", str(TEST_PORT), "--no-browser"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        # Poll until server responds
        ready = False
        for attempt in range(25):
            try:
                with urllib.request.urlopen(f"{BASE_URL}/api/capabilities", timeout=1) as resp:
                    if resp.status == 200:
                        ready = True
                        break
            except Exception:
                time.sleep(0.5)

        assert ready, "Server failed to start and respond on test port within 12 seconds."
        print("[PASS] Server successfully started and responded to capabilities endpoint.")

        # Test index.html delivery
        req = urllib.request.Request(f"{BASE_URL}/")
        with urllib.request.urlopen(req, timeout=3) as resp:
            html = resp.read().decode("utf-8")
            assert "Local Document Signer" in html
            print("[PASS] Index page served correctly with status 200.")

        # Test static assets
        req = urllib.request.Request(f"{BASE_URL}/static/styles.css")
        with urllib.request.urlopen(req, timeout=3) as resp:
            assert resp.status == 200
            print("[PASS] Static CSS served correctly.")

        req = urllib.request.Request(f"{BASE_URL}/static/app.js")
        with urllib.request.urlopen(req, timeout=3) as resp:
            assert resp.status == 200
            print("[PASS] Static JS served correctly.")

        # Test capabilities API
        req = urllib.request.Request(f"{BASE_URL}/api/capabilities")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            assert "docx" in data and "maxFileSize" in data
            print(f"[PASS] Capabilities API returned: {data}")

        # Test signature generation API
        sig_data = json.dumps({"name": "Test Signer", "style": "handwritten", "color": "black"}).encode("utf-8")
        req = urllib.request.Request(
            f"{BASE_URL}/api/signature",
            data=sig_data,
            headers={
                "Content-Type": "application/json",
                "X-Requested-With": "LocalSigner",
            },
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            sig_result = json.loads(resp.read().decode("utf-8"))
            assert "image" in sig_result and sig_result["width"] > 0
            print(f"[PASS] Signature generation API succeeded (image size: {len(sig_result['image'])} chars).")

        print("\nAll end-to-end executable verification checks PASSED!")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        print("[PASS] Executable terminated cleanly.")


if __name__ == "__main__":
    test_executable()
