import json
from pathlib import Path
import sys

from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.main import app


def main() -> None:
    cases_path = Path(__file__).with_name("eval_cases.json")
    cases = json.loads(cases_path.read_text())
    client = TestClient(app)

    passed = 0
    for index, case in enumerate(cases, start=1):
        session_id = case.get("session_id", f"eval-{index}")
        for setup_message in case.get("setup_messages", []):
            client.post(
                "/chat",
                json={
                    "session_id": session_id,
                    "message": setup_message,
                    "include_debug": False,
                },
            )

        response = client.post(
            "/chat",
            json={
                "session_id": session_id,
                "message": case["message"],
                "include_debug": True,
            },
        )
        payload = response.json()
        actual = payload["decision"]
        ok = actual in case["expected_decisions"]
        if ok:
            passed += 1

        print(
            f"[{'PASS' if ok else 'FAIL'}] {case['name']}: "
            f"expected {case['expected_decisions']} got {actual} "
            f"(confidence={payload['confidence']}, latency_ms={payload.get('debug', {}).get('latency_ms')})"
        )

    print(f"\nSummary: {passed}/{len(cases)} cases passed")


if __name__ == "__main__":
    main()
