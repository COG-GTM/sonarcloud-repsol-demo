# Playbook — Sonar finding triage and remediation

You own exactly one SonarCloud finding, described at the end of this prompt.
Triage it before you touch any code: most of the value here is refusing to
"fix" what is not actually exploitable.

## 0. Boot the app first

This service has a UI, and the UI is how you prove your verdict:

```
go run ./cmd/api      # serves the contract desk on http://localhost:8080
```

Open it in the browser before deciding anything. Every finding below is either
reachable from a page (search, contract detail, attachment download, export,
region summary) or provably unreachable from any of them.

## 1. Understand the finding

- Read the Sonar rule description and the flagged code plus its callers.
- Determine how untrusted input reaches the flagged line, if at all.
- Find the page or request that reaches it. If nothing in the UI reaches it,
  say so explicitly — that is already half of a false-positive argument.

## 2. Decide: real vulnerability or false positive

Classify as **false positive** only when you can prove at least one of:

- the flagged value cannot be influenced by untrusted input,
- the construct carries no security decision (e.g. a non-persisted digest used
  as a local cache key),
- the code only runs in test or fixture context that never ships,
- an existing control (validation, allowlist, parameterization) already blocks
  the attack, and you can point at it.

Otherwise treat it as real.

## 3. If it is real: prove it, then fix it

- Reproduce the issue **in the browser**: navigate to the affected page, submit
  the payload as a user would, and screenshot the result (data leaking, a script
  firing, a file you should not be able to read, a command executing). Fall back
  to a failing unit test or a `curl` only when the finding has no UI path.
- Apply the minimal, idiomatic fix (parameterized queries, allowlists,
  `filepath.Clean` + root containment, exec without a shell, secrets from the
  environment or the secret manager, TLS verification enabled, encryption and
  least-privilege network rules in IaC).
- Re-run the exact same browser reproduction against the patched build and
  screenshot it failing to exploit. Then check that the legitimate flow still
  works in the UI (a normal search still returns contracts, a real attachment
  still downloads) — a fix that breaks the feature is not a fix.
- Run `go build ./...` and `go test ./...`.
- Open a PR against the remediation branch given below. The PR body must state:
  the Sonar key and rule, why the finding is real, the exploit path, the fix,
  and the evidence that it is fixed.

## 4. If it is a false positive

- Do not change the code.
- Still try to exploit it in the browser, and capture the attempt failing: send
  the payload the rule implies through the UI and screenshot the rejection or
  the harmless output. An unexploitable finding is much more convincing shown
  than argued.
- Open no PR. Report back with the Sonar key, the rule, the failed exploit
  attempt, and the argument for why it is not exploitable, citing the specific
  lines that make it safe (the validator, the allowlist, the escaping, the
  test-only scope), and recommend marking it as "Won't fix" / "Safe" in
  SonarCloud with that justification.

## 5. Always

- Keep the change scoped to this one finding.
- Record a short verification report (what you ran, what you saw) with the
  before/after screenshots attached, so a human reviewer can audit the decision
  without rerunning it.
