# Testing policy

_Shared Reyndex guideline. Versioned source: `backend/docs/guidelines/reyndex-testing-guidelines.md`. Identical copies: `mcp-gateway`, `brand-system`, `website`, `candidate-engine`, `infrastructure`, `notion-enrichment-engine`, `formula-engine`, `worker-autoscaler`, `ai-enrichment-engine`, `web-app`, `remote-pdf-extractor`, `backend`. Source attribution is informational; this copy contains the required rules. Last synced 2026-09-22._

Tests protect critical product behavior. They are not a checklist for every function, branch, input variation, or code change. Deliberately leave low-impact implementation details without dedicated tests.

## Admission rule

Add or retain a test only when **both** are true:

1. A plausible failure could break an essential user journey, violate security or workspace isolation, lose/corrupt durable data, mischarge money, or duplicate/strand consequential work.
2. The test detects that failure and adds meaningful protection beyond existing tests, types, schema validation, and framework guarantees.

Be able to name the failure and its product consequence in one sentence. No separate scoring system, coverage registry, or justification document is required. “This code changed,” “this branch is uncovered,” and “a mutation survived” are not reasons to add a test.

## Protect

- Authentication, authorization, tenant isolation, credential secrecy, and sensitive-data exposure
- Billing, credits, destructive operations, persistence integrity, and data-loss migrations
- Critical state transitions, idempotency, concurrency, retries, ordering, and recovery
- Producer/consumer contracts whose failure breaks a real workflow: API, event, engine, queue, and provider boundaries
- Essential user journeys where a wiring failure would escape narrower checks

Test these at the smallest scope that exposes the risk. A critical calculation may need a unit test; a broken route registration needs an integration test. A module boundary or HTTP call alone does not establish criticality.

## Do not test by default

- Magic strings, constant lists, labels, copy, CSS classes, or routine default values
- Trimming, joining, splitting, casing, formatting, simple mapping/filtering, getters, setters, or pass-through helpers
- Incidental array/object order, internal object shapes, private call sequences, or implementation snapshots
- Types, dependency behavior, or framework guarantees already enforced elsewhere
- Every equivalent input, optional field combination, branch, scenario, or mutation
- The same rule at several layers without a distinct consequential failure at each layer

Judge exceptions by consequence, not syntax. An HMAC payload, persisted identifier, permission string, or FIFO order can control security or durable work and merit focused protection. Ordinary string manipulation or array order does not. Do not use “contract” to justify asserting every property or inventing hypothetical risks for trivial code.

## Test design and pruning

Assert externally observable outcomes with independent expected values. Cover materially different critical success, rejection, and recovery paths; use representative cases instead of exhaustive permutations. Reuse existing fixtures and tools. Mock external dependencies where useful, but verify consequential producer/consumer compatibility against real schemas or implementations; matching hand-written mocks proves neither side.

During an authorized test audit, delete tests that fail the admission rule. Do not move their assertions elsewhere, merge unrelated cases to disguise the count, or remove distinct critical protection for a numerical target. Explain any meaningful protection intentionally removed. This policy alone does not authorize a bulk test deletion.

No test-count, coverage-percentage, or mutation-score targets. Use coverage or mutation results only to investigate a suspected critical gap. No new framework or live-provider requirement follows from this policy.

## What to run

- Documentation-only changes: check accuracy, references, instruction parity, and diffs. No application build or full test suite solely for prose changes.
- Localized code changes: run the affected meaningful tests and applicable lint/type checks; broaden when shared behavior or failures warrant it.
- Shared foundations, cross-repo contracts, or broad refactors: run the relevant broader suites on affected producers and consumers. Run builds when packaging, compilation, routing, or deployment output is at risk.
- Existing mandatory CI/release gates still apply. Do not bypass or weaken them. A command list documents available checks; it does not require every command after every edit.

Once relevant checks pass, repeat only after changes or new evidence justify it. Report what ran and what remains unverified. Backend PostgreSQL tests use the disposable harness, never development/staging/production databases. Local tests do not prove deployed provider behavior, performance, or production readiness.
