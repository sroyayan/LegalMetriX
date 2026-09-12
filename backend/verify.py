"""Phase 9 verification harness for the LegalMetriX backend.

Runs the full app through FastAPI's TestClient (no server needed) and
verifies: module imports, health endpoint, auth enforcement, size limit,
image validation, a real Gemini label analysis, strict-JSON fallback, and
upload cleanup. Uses the venv python:  ./venv/Scripts/python.exe verify.py
"""

import asyncio
import importlib
import os
from pathlib import Path

WANT_OK = "\033[32m[PASS]\033[0m"
WANT_BAD = "\033[31m[FAIL]\033[0m"
ROOT = Path(__file__).resolve().parent


def check(name, ok, detail=""):
    print(f"{WANT_OK if ok else WANT_BAD} {name}" + (f"  -- {detail}" if detail else ""))


def main():
    results = []
    # 1. Import all app modules
    try:
        for s in ["app.schemas", "app.services.gemini_service", "app.api.scan", "app.main"]:
            importlib.import_module(s)
        results.append(("All modules import cleanly", True))
    except Exception as exc:  # noqa: BLE001
        results.append(("All modules import cleanly", False, repr(exc)))

    from fastapi.testclient import TestClient
    from app.main import app
    from app.services.gemini_service import LabelAnalysisError, _parse_json

    before = set((ROOT / "uploads").iterdir()) if (ROOT / "uploads").is_dir() else set()

    with TestClient(app) as client:
        headers = {"X-API-Key": os.getenv("LEGALMETRIX_API_KEY", "")}

        # 2. GET /
        r = client.get("/")
        results.append(("GET / health", r.status_code == 200, f"status={r.status_code}"))

        # 3. Auth: missing key
        r = client.post("/scan/upload", files={"file": ("x.jpg", b"xx", "image/jpeg")})
        results.append(("Auth: missing X-API-Key -> 401", r.status_code == 401, f"status={r.status_code}"))

        # 4. Auth: wrong key
        wrong = {"X-API-Key": "not-the-key"}
        r = client.post("/scan/upload", files={"file": ("x.jpg", b"xx", "image/jpeg")}, headers=wrong)
        results.append(("Auth: wrong X-API-Key -> 401", r.status_code == 401, f"status={r.status_code}"))

        # 5. Size limit: 11 MB dummy -> 413
        big = b"\x00" * (11 * 1024 * 1024)
        r = client.post("/scan/upload", files={"file": ("big.jpg", big, "image/jpeg")}, headers=headers)
        results.append(("Size limit: 11MB -> 413", r.status_code == 413, f"status={r.status_code}"))

        # 6. Not an image: text file -> 400
        r = client.post("/scan/upload", files={"file": ("note.txt", b"hello", "text/plain")}, headers=headers)
        results.append(("Validation: non-image -> 400", r.status_code == 400, f"status={r.status_code}"))

        # 7. Real label image -> 200 + analysis
        label = ROOT / "uploads" / "McVitie-s-Digestive-Wholewheat-Biscuit-3.webp"
        if label.is_file():
            with label.open("rb") as fh:
                r = client.post("/scan/upload", files={"file": ("label.webp", fh, "image/webp")}, headers=headers)
            body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            ok = r.status_code == 200 and body.get("success") is True and isinstance(body.get("analysis"), dict)
            results.append(("Real Gemini analysis -> 200 + JSON", ok, f"status={r.status_code} detail={body.get('detail','')}"))
            if ok:
                print("  analysis fields:", sorted(body["analysis"].keys()))
        else:
            results.append(("Real Gemini analysis -> 200 + JSON", False, "test image not found"))

        # 8. Upload cleanup (no new files left behind)
        after = set((ROOT / "uploads").iterdir()) if (ROOT / "uploads").is_dir() else set()
        results.append(("Uploads cleaned up after processing", not (after - before)))

    # 9. Strict-JSON fallback: markdown-fenced JSON parses
    try:
        parsed = _parse_json('```json\n{"product_name": "Biscuit"}\n```')
        results.append(("Strict-JSON fence fallback works", parsed == {"product_name": "Biscuit"}))
    except Exception as exc:  # noqa: BLE001
        results.append(("Strict-JSON fence fallback works", False, repr(exc)))

    # 10. Non-image path raises LabelAnalysisError
    from app.services.gemini_service import analyze_label
    tmp = ROOT / "uploads" / "__not_an_image.txt"
    try:
        tmp.write_text("definitely not an image", encoding="utf-8")
        analyze_label(str(tmp))
        results.append(("analyze_label rejects non-image", False))
    except (LabelAnalysisError, FileNotFoundError):
        results.append(("analyze_label rejects non-image", True))
    finally:
        tmp.unlink(missing_ok=True)

    print("\n===============================")
    failed = 0
    for row in results:
        name, ok = row[0], row[1]
        detail = row[2] if len(row) > 2 else ""
        check(name, ok, detail)
        if not ok:
            failed += 1
    print("===============================")
    print(f"RESULT: {len(results) - failed}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    raise SystemExit(main())