# Repository documentation rules

_Shared Reyndex guideline. Versioned source: `backend/docs/guidelines/README.md`. An identical copy is maintained in all twelve Reyndex repositories. Last synced 2026-09-22._

## Local authority

The repository's `AGENTS.md` and identical `CLAUDE.md` are its entry point. They select the local contracts and guidelines relevant to the task. Required instructions must be available in this clone; workspace-root files, personal configuration, installed skills, and another repository's agent guide are not prerequisites.

Keep ownership and coordination requirements explicit. A cross-repository contract change still requires comparing the actual producers and consumers; a local policy copy is not evidence that another implementation is compatible. External links may provide attribution or optional implementation context.

## Working and documentation rules

Check repository status and preserve unrelated changes. Use the owning domain's patterns and current scripts; avoid speculative abstractions, compatibility paths, migrations, or deployment actions for a prose change. Resolve code/policy discrepancies explicitly rather than silently treating either as correct.

Keep one authoritative home for detailed rules. READMEs explain purpose and setup; agent guides retain useful entry points, conventions, constraints, commands, and change hazards; contracts and runbooks explain invariants and operations. Aim for 1,000–1,500 useful words per agent guide without padding or stripping necessary context.

Verify descriptive claims and example commands against source. Distinguish policy, observed behavior, and deployment evidence. Preserve rationale and prerequisites; repair links and anchors after moves. Avoid implementation diaries, exhaustive inventories, test counts, and copied feature specifications.

## Shared copies and validation

Source labels identify version-controlled policy owners; they are not instructions to fetch more rules. Synchronize intentional shared copies when changing their rules, refresh the sync date, and keep their content identical. Put repository-specific links in the local guide or index. Brand documents identify their canonical files and consumer copies in the same way. Do not make different repositories' agent guides identical.

Apply the local [testing policy](reyndex-testing-guidelines.md). Documentation-only changes need source/reference checks, local links and anchors, guide-pair parity, shared-copy parity, and diff checks. Report unsynchronized consumers or unavailable integration evidence; do not claim validation that was not performed.
