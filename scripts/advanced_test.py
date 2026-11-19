"""Advanced endpoint smoke test: stress, VOI, scenarios, baselines, copilot."""
import urllib.request
import json
import time
import sys

BASE = "http://localhost:8000"


def post(path, data, timeout=90):
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        f"{BASE}{path}", body, {"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def get(path, timeout=30):
    with urllib.request.urlopen(f"{BASE}{path}", timeout=timeout) as r:
        return json.loads(r.read())


results = []

def check(name, fn):
    try:
        t0 = time.time()
        result = fn()
        elapsed = time.time() - t0
        results.append((name, True, f"{elapsed:.1f}s"))
        return result
    except Exception as e:
        results.append((name, False, str(e)[:80]))
        return None


print("=" * 60)
print(" VidyaPlan Advanced Endpoint Tests")
print("=" * 60)

# 1. Run plan
plan = check("POST /api/plan", lambda: post("/api/plan", {"budget": 5000000, "cohort_only": True}))
if plan:
    pid = plan["plan_id"]
    funded = plan["kpis"]["interventions_funded"]
    print(f"     plan_id={pid}  funded={funded}  budget_used=Rs.{plan['budget_used']:,}")
else:
    pid = 8  # fallback to last known plan
    print(f"     using fallback plan_id={pid}")

# 2. Stress test
stress = check("POST /api/plan/stress", lambda: post("/api/plan/stress", {"budget": 5000000, "n_scenarios": 50, "seed": 42}))
if stress:
    print(f"     regret={stress['expected_regret_pct']:.1f}%  items={len(stress['details'])}")

# 3. VOI
voi = check(f"GET /api/plan/{pid}/verify-first", lambda: get(f"/api/plan/{pid}/verify-first"))
if voi is not None:
    print(f"     {len(voi)} verification entries")

# 4. Scenario compare
sc = check("POST /api/plan/compare", lambda: post("/api/plan/compare", {"budget": 5000000}))
if sc:
    print(f"     low={sc['low']['funded']}  base={sc['base']['funded']}  high={sc['high']['funded']}  gained={len(sc['gained_in_high'])}  lost={len(sc['lost_in_low'])}")

# 5. Baselines
bl = check(f"GET /api/plan/{pid}/baselines", lambda: get(f"/api/plan/{pid}/baselines"))
if bl:
    for b in bl:
        print(f"     {b['method']:12s}  obj={b['objective']:.2f}  pct_vs_opt={b['pct_vs_optimiser']:.1f}%")

# 6. Copilot (Granite)
cop = check("POST /api/copilot", lambda: post("/api/copilot", {"instruction": "what if budget drops 30 percent", "budget": 5000000}, timeout=60))
if cop:
    print(f"     source={cop['source']}  tool={cop['tool_call']}  status={cop['status']}")

# 7. Memo PDF — binary response, can't use get() which decodes JSON
def _check_pdf():
    import urllib.request
    with urllib.request.urlopen(f"{BASE}/api/plan/{pid}/memo.pdf", timeout=30) as r:
        data = r.read()
        ct = r.headers.get("Content-Type", "")
        assert "pdf" in ct.lower() or data[:4] == b"%PDF", f"Not a PDF: {ct}"
        return {"bytes": len(data), "content_type": ct}

memo_ok = check(f"GET /api/plan/{pid}/memo.pdf", _check_pdf)
if memo_ok:
    print(f"     {memo_ok['bytes']} bytes  content_type={memo_ok['content_type']}")

# 8. Audit
audit = check("GET /api/audit", lambda: get("/api/audit"))
if audit:
    print(f"     {len(audit)} audit entries")

# Results
print()
print("=" * 60)
passed = sum(1 for _, ok, _ in results if ok)
failed = sum(1 for _, ok, _ in results if not ok)
for name, ok, detail in results:
    status = "PASS" if ok else "FAIL"
    print(f"  {status:4s}  {name:40s}  {detail}")
print("=" * 60)
print(f"  {passed} passed  |  {failed} failed")
print("=" * 60)
sys.exit(0 if failed == 0 else 1)
