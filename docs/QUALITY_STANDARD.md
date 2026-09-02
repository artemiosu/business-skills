# Skill quality standard

A Business Skill earns inclusion by changing agent decisions reliably—not by adding a long persona prompt.

## Acceptance gates

1. **Distinct job:** concrete recurring request and explicit non-goals.
2. **Discoverable:** precise name/description and useful UI metadata.
3. **Progressive:** compact entrypoint; conditional references loaded only when needed.
4. **Evidence-aware:** provenance, uncertainty, and source-instruction boundaries.
5. **Safe by default:** reversible behavior and authorization at mutation boundaries.
6. **Observable:** deterministic checks for fragile mechanics and realistic behavioral cases.
7. **Portable:** no hidden dependency or account assumption; documented requirements.
8. **Maintained:** owner, version, changelog entry, and compatibility notes.

## Review scorecard

Reviewers score 0–2 for each gate. A candidate needs 14/16, with no zero on distinct job, safety, or observable behavior. Passing is necessary, not sufficient; maintainers may reject overlap, excessive context cost, or unmaintainable scope.

## Evidence levels

- Experimental: plausible workflow, synthetic tests only.
- Stable beta: validated mechanics plus realistic adversarial cases; field calibration incomplete.
- Stable: repeated real-world use, resolved evaluations, documented limitations.

No badge or status implies guaranteed business outcomes.
