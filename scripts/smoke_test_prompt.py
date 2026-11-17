"""
Smoke test: verify v1.2 prompt loads and section parser compatibility.
Run from project root: venv\Scripts\python.exe scripts\smoke_test_prompt.py
"""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app.crud.inferance_crud import parse_report_sections, REPORT_SECTION_HEADERS

print("=== SMOKE TEST: Prompt Load ===")
prompt_path = os.path.normpath(os.path.join("app", "prompt", "system_prompt.txt"))
with open(prompt_path, "r", encoding="utf-8") as f:
    prompt = f.read()
print(f"Prompt loaded: {len(prompt)} chars")
print(f"v1.2 marker present: {'v1.2' in prompt}")
print(f"All 8 stages present: {all(f'Stage {i}' in prompt for i in range(1, 9))}")
for section in REPORT_SECTION_HEADERS:
    assert section in prompt, f"MISSING section in prompt: {section}"
print("[PASS] All 5 output section headings present in prompt.")

print()
print("=== SMOKE TEST: Section Parser Compatibility ===")
sample = """BUSINESS UNDERSTANDING
Shree Ganesh Engineering Works is a 3-year-old precision engineering manufacturer with 12 employees.

EVIDENCE MATCHING
| Category | Status | Supporting Evidence | Observation | Explanation |
|----------|--------|---------------------|-------------|-------------|
| Sales | PARTIAL MATCH | Invoices totalling Rs 400,000 | 40% coverage of declared Rs 1,000,000 | Sample submission likely |

POSSIBLE EXPLANATIONS
| Discrepancy | Hypothesis | Supporting Evidence | Contradicting Evidence | Missing Information | Plausibility |
|-------------|------------|---------------------|------------------------|---------------------|--------------|
| Gap of Rs 600,000 | 1. Sample invoices submitted | 1 customer invoice shown | None in file | Full customer ledger | High - partial submission common in MSME |
| | 2. Trade credit cycle | 30-day credit terms declared | No debtor ledger | Debtor aging schedule | Medium |

ADDITIONAL INFORMATION REQUIRED
- Opening stock register as of period start.
- Full customer ledger with aging schedule.
- Bank reconciliation statement.

OVERALL ASSESSMENT
Conclusion: PARTIAL MATCH
Summary: Declared manufacturing operations are partially corroborated by physical and production evidence. However, the Rs 600,000 turnover gap and absence of opening stock records prevent a full MATCH verdict.
"""

sections, status = parse_report_sections(sample)
print(f"Sections found: {list(sections.keys())}")
print(f"Overall status: {status}")
assert tuple(sections.keys()) == REPORT_SECTION_HEADERS, f"Header order mismatch: {list(sections.keys())}"
assert status == "PARTIAL MATCH", f"Status mismatch: {status}"
print("[PASS] Parser compatibility confirmed for v1.2 output format.")

print()
print("=== SMOKE TEST: Deterministic Reconciliation (ABC Textile) ===")
from app.schemas.request_schemas import ExplainRequest
from app.crud.inferance_crud import compute_deterministic_reconciliations, build_user_payload

with open("app/model/request_example.txt", "r") as f:
    req = ExplainRequest.model_validate_json(f.read())

facts = compute_deterministic_reconciliations(req)
facts_str = " ".join(facts)
print(f"Facts generated: {len(facts)}")
for fact in facts:
    print(f"  - {fact[:100]}")

payload = build_user_payload(req)
assert "=== DECLARED BUSINESS PROFILE ===" in payload
assert "=== DETERMINISTIC FACT CHECK (Python-Verified Math) ===" in payload
print(f"[PASS] Payload built: {len(payload)} chars")
print(f"       DETERMINISTIC FACT CHECK section present: {True}")

print()
print("All smoke tests PASSED.")
