"""End-to-end smoke test for VidyaPlan API.
Run with: python scripts/smoke_test.py
"""
import json
import sys
import urllib.request

BASE = "http://localhost:8000"


def get(path: str) -> dict:
    with urllib.request.urlopen(BASE + path) as r:
        return json.loads(r.read())


def post(path: str, body: dict) -> dict:
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        BASE + path, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def put(path: str, body: dict) -> dict:
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        BASE + path, data=data,
        headers={"Content-Type": "application/json"},
        method="PUT",
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def run():
    passed = []
    failed = []

    def check(name: str, fn):
        try:
            fn()
            passed.append(f"  PASS  {name}")
        except AssertionError as e:
            failed.append(f"  FAIL  {name}  —  {e}")
        except Exception as e:
            failed.append(f"  ERROR {name}  —  {type(e).__name__}: {e}")

    # ── 1. Health ──────────────────────────────────────────────────────────
    def test_health():
        r = get("/health")
        assert r["status"] == "ok", f"status={r['status']}"
        assert r["db"] == "ok", f"db={r['db']}"
    check("GET /health", test_health)

    # ── 2. Version ────────────────────────────────────────────────────────
    def test_version():
        r = get("/api/version")
        assert r["version"] == "0.1.0"
    check("GET /api/version", test_version)

    # ── 3. Data summary ───────────────────────────────────────────────────
    summary = {}
    def test_data_summary():
        nonlocal summary
        summary = get("/api/data/summary")
        assert summary["cohort_schools"] == 40, f"cohort={summary['cohort_schools']}"
        assert summary["total_schools"] == 77076, f"total={summary['total_schools']}"
        for fac in ["electricity", "library", "computers"]:
            assert fac in summary["evidence_counts"], f"missing {fac}"
        passed.append(
            f"  PASS  GET /api/data/summary"
            f"  (cohort={summary['cohort_schools']}, total={summary['total_schools']})"
        )
    try:
        test_data_summary()
    except Exception as e:
        failed.append(f"  FAIL  GET /api/data/summary  —  {e}")

    # ── 4. Data quality log ───────────────────────────────────────────────
    def test_quality():
        r = get("/api/data/quality")
        assert len(r) > 0, "quality log is empty"
        passed.append(f"  PASS  GET /api/data/quality  ({len(r)} entries)")
    try:
        test_quality()
    except Exception as e:
        failed.append(f"  FAIL  GET /api/data/quality  —  {e}")

    # ── 5. Schools list ───────────────────────────────────────────────────
    def test_schools():
        r = get("/api/schools?in_cohort=true")
        assert len(r) == 40, f"expected 40 schools, got {len(r)}"
        for s in r[:3]:
            assert "evidence" in s
            for fac in ["electricity", "library", "computers"]:
                assert fac in s["evidence"], f"missing {fac} in evidence"
        passed.append(f"  PASS  GET /api/schools?in_cohort=true  ({len(r)} schools)")
    try:
        test_schools()
    except Exception as e:
        failed.append(f"  FAIL  GET /api/schools  —  {e}")

    # ── 6. Config GET ─────────────────────────────────────────────────────
    def test_config_get():
        r = get("/api/config")
        assert "costs" in r and "weights" in r
        assert r["costs"]["library"] == 150000
        assert r["provenance"] == "SIMULATED"
        passed.append(f"  PASS  GET /api/config  (library=Rs.{r['costs']['library']})")
    try:
        test_config_get()
    except Exception as e:
        failed.append(f"  FAIL  GET /api/config  —  {e}")

    # ── 7. Config PUT ─────────────────────────────────────────────────────
    def test_config_put():
        r = put("/api/config", {
            "costs": {"library": 150000, "electricity": 250000, "computers": 400000},
            "weights": {"electricity": 1.0, "computers": 0.9, "library": 0.8},
        })
        assert r["status"] == "ok"
    check("PUT /api/config", test_config_put)

    # ── 8. Run plan ───────────────────────────────────────────────────────
    plan_id = None
    n_selected = 0
    def test_run_plan():
        nonlocal plan_id, n_selected
        r = post("/api/plan", {"budget": 5000000, "cohort_only": True})
        assert r["budget_used"] <= 5000000, f"budget exceeded: {r['budget_used']}"
        assert r["plan_id"] is not None
        plan_id = r["plan_id"]
        n_selected = len(r["selected"])
        n_deferred = len(r["deferred"])
        pct = round(r["budget_used"] / r["budget"] * 100)
        passed.append(
            f"  PASS  POST /api/plan"
            f"  (id={plan_id}, funded={n_selected}, deferred={n_deferred},"
            f" used=Rs.{int(r['budget_used'])} ({pct}%))"
        )
    try:
        test_run_plan()
    except Exception as e:
        failed.append(f"  FAIL  POST /api/plan  —  {e}")

    # ── 9. Get plan ───────────────────────────────────────────────────────
    if plan_id:
        def test_get_plan():
            r = get(f"/api/plan/{plan_id}")
            assert r["id"] == plan_id
            assert "recommendations" in r
            passed.append(
                f"  PASS  GET /api/plan/{plan_id}"
                f"  ({len(r['recommendations'])} recommendations, status={r['status']})"
            )
        try:
            test_get_plan()
        except Exception as e:
            failed.append(f"  FAIL  GET /api/plan/{{id}}  —  {e}")

    # ── 10. List plans ────────────────────────────────────────────────────
    def test_list_plans():
        r = get("/api/plans")
        assert len(r) >= 1
        passed.append(f"  PASS  GET /api/plans  ({len(r)} plans)")
    try:
        test_list_plans()
    except Exception as e:
        failed.append(f"  FAIL  GET /api/plans  —  {e}")

    # ── 11. Submit review ─────────────────────────────────────────────────
    if plan_id:
        def test_review():
            detail = get(f"/api/plan/{plan_id}")
            selected_recs = [rec for rec in detail["recommendations"] if rec["status"] == "selected"]
            if not selected_recs:
                passed.append("  SKIP  POST /api/reviews/{id}  (no selected recs)")
                return
            rec_id = selected_recs[0]["id"]
            r = post(f"/api/reviews/{rec_id}", {
                "decision": "approved",
                "reviewer": "SmokeTestUser",
                "note": "Automated smoke test approval",
            })
            assert r["status"] == "ok"
            assert r["decision"] == "approved"
            passed.append(f"  PASS  POST /api/reviews/{rec_id}  (approved)")
        try:
            test_review()
        except Exception as e:
            failed.append(f"  FAIL  POST /api/reviews/{{id}}  —  {e}")

    # ── 12. Audit log ─────────────────────────────────────────────────────
    def test_audit():
        r = get("/api/audit")
        assert len(r) >= 1
        entry = r[0]
        for key in ["actor", "action", "entity", "created_at"]:
            assert key in entry, f"missing key: {key}"
        passed.append(f"  PASS  GET /api/audit  ({len(r)} entries)")
    try:
        test_audit()
    except Exception as e:
        failed.append(f"  FAIL  GET /api/audit  —  {e}")

    # ── Summary ───────────────────────────────────────────────────────────
    print()
    print("=" * 58)
    print(" VidyaPlan Smoke Test Results")
    print("=" * 58)
    for line in passed:
        print(line)
    for line in failed:
        print(line)
    print("=" * 58)
    print(f"  {len(passed)} passed  |  {len(failed)} failed")
    print("=" * 58)
    print()

    if failed:
        sys.exit(1)
    else:
        print("  ALL TESTS PASSED - OK")
        print()


if __name__ == "__main__":
    run()
