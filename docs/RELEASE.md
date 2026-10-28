# Release a reviewed revision

Use `.github/workflows/release.yml` with the reviewed existing tag and exact main
commit after reviewing the scientific and presentation changes.

The workflow is manually dispatched from `main` with an existing version tag
and the complete reviewed 40-character commit SHA. Dispatch SHA, checkout,
current main and the tag's resolved commit must all agree. Annotated tags are
resolved; missing or different tags fail without a tag-creation/movement call.
The verification job has read-only contents access. A separate publication job
gets contents-write access only after verification, rechecks the refs and either
creates the release for that existing tag or accepts an exactly matching prior
release. Different existing release notes are not overwritten. Concurrent
external writers are outside the workflow lock, so refs are checked immediately
before and after the release request; this is not a platform-wide atomic lock.

No data, model or duplicate build artifacts are uploaded, no cache is created by
the release workflow, and no quota or paid infrastructure is increased. The
release does not automatically replace the account's latest-release designation.
Local mock-API tests cover mismatched identities, missing/moved tags, moved main,
annotated tags, cycles and idempotent publication. They are not evidence that a
remote release has been executed.

Verification includes 13 scientific/source-integrity and seven guard tests,
original freeze/revision identities, all54published forecast reconstructions,
the hash-identical coefficient-based model restoration, current official-page
statistical/publication agreement and generated explorer/link checks. Current
source bytes may differ from the old pinned HTML. The comparison records that
difference and never changes the historical manifest or implies contemporaneous
capture. It is not the unavailable original-byte source reconstruction. Native
browser observations remain separately dated.

The original release record below preserves its historical date and scope.

# v1.0.0 research release

[Open the live explorer](https://prasanna-k-123.github.io/inflation-vintages/).

Actual browser verification completed 18 October 2026 at desktop and 375/320-pixel iframe widths, with native keyboard controls and the linked evidence checked. The iframe tests use real CSS layout widths; they do not emulate a phone OS, touch input or a screen reader. Detailed observations are in [browser_verification.json](../reports/browser_verification.json).

Seven scientific tests; 108 release/method/target and eighteen hindsight script views. Eleven original scientific hashes remain unchanged. Public-checkout numeric reproduction reconstructs all 54 forecasts and the original Ridge coefficients/metrics without raw documents or a private model artifact. Full source-cell re-audit additionally requires the pinned raw cache; it is not claimed by the numeric command.

The release tag identifies the final checked source commit. Raw source observations, credentials and private fitted artifacts are excluded. The explorer selects fixed aggregate research results or explicitly hypothetical assumptions; it does not refit or claim deployment.

Profile integration is tracked separately from this project release.
