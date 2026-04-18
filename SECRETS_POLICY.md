# PM-Tennis Project — Secrets Policy

This document governs the handling of secrets, credentials, account identifiers, trading-execution details, and any other sensitive material in the PM-Tennis project. It exists because the project's Git repository is public (per decision D-005), which makes explicit rules about what enters the repo load-bearing rather than optional.

The document has two sections. **Part A** is an operator quick reference — short, practical, checklist-style, designed to be consulted before any commit. **Part B** is a policy statement — longer, declarative, framed for any reader who encounters the repo publicly (a security researcher, a prospective collaborator, a curious passer-by) and wants to understand the project's posture toward secrets and personal information.

The two sections cover the same ground at different depths. If they ever disagree, Part B is authoritative, because Part A is a compressed view and Part B is the source. Disagreements are themselves bugs in the document and should be surfaced to Claude for reconciliation.

---

# Part A — Operator quick reference

## A.1 Before every commit: the two-question check

Before committing any file to the repository, the operator answers two questions in order.

**Question 1: Does this file contain anything from the secret list below?**

If yes, the commit does not proceed. The file either needs to be edited to remove the sensitive content, or it does not belong in the repo at all.

**Question 2: Has Claude flagged anything about this file during the session in which it was produced?**

If Claude said anything like "this contains sensitive information," "this should not be committed," "store this in an environment variable instead," the operator heeds it. Claude is obligated to flag these things per Section 1.5.4 of the plan; the operator's job is not to override the flag without explicit reasoning.

If both questions clear, the commit proceeds normally.

## A.2 The secret list (short version)

Never in the repo, ever:

1. **Platform passwords and 2FA seeds.** GitHub, Netlify, Render, backup storage provider, domain registrar. These live only in the operator's password manager.

2. **Platform API keys and tokens.** Render deploy keys, Netlify build tokens, GitHub personal access tokens, the `X-PM-Tennis-Token` shared secret that guards the trade-entry endpoint. These live in the platform's environment-variable interface (Render dashboard, Netlify dashboard). Code that reads them reads by name (e.g., `os.environ["PM_TENNIS_TOKEN"]`) and never embeds the value.

3. **Polymarket US account information.** Account email, funded balance in absolute dollars, wallet addresses, position sizes in absolute dollars, anything that identifies the operator as the holder of that specific Polymarket account.

4. **Personal identifying information.** The operator's name, exact location, contact details, anything that de-anonymizes beyond the coarse "US-based operator" framing the project otherwise carries.

5. **Real-time trading detail.** Live open positions, prices of orders just placed, anything that would let an observer front-run or piggyback a trade in progress.

## A.3 Sensitive-but-different

Two categories that are not "secret" in the hard sense but require their own handling.

**Trading execution in historical form (manual-trade logs, reconciliation logs, window-close results).** These are sensitive while the observation window is live and in the period leading up to the decision memo. After the window closes, whether they are published (with or without anonymization) is the operator's decision at that time. The default is: they remain in platform storage and in the operator's backups, not in the public repo, until the operator explicitly decides otherwise.

**The captured archive (JSONL files of book ticks, score events, envelopes).** This is not committed to the repo for two reasons: (a) size — gigabytes of JSONL do not belong in git regardless of content; (b) sensitivity — the archive contains the manual-trade envelopes, which under A.3 above are not for public release by default. The archive lives on the Render persistent disk and in the nightly backup to object storage. If it is ever published, the decision is explicit and logged to DecisionJournal.

## A.4 What does belong in the repo

- The build plan document.
- The governance artifacts: STATE, Playbook, Orientation, DecisionJournal, RAID, PreCommitmentRegister, SECRETS_POLICY.
- All source code (capture, API, replay simulator, dashboard, admin UI, test harnesses).
- All code-level configuration that does not contain secrets (Dockerfiles, docker-compose.yml with env-var references, Render service configuration files, Netlify build settings, GitHub Actions workflows).
- The four commitment files (`signal_thresholds.json`, `fees.json`, `breakeven.json`, `sackmann/build_log.json`) once they exist. These are pre-commitments — their publication is the point.
- Session handoff documents (`Handoff_H-NNN.md`).
- Runbooks, data dictionaries, analysis notebooks (with sensitive outputs removed or clearly marked as private).
- Test vectors, parity-check fixtures, sample data synthesized for tests.

If a file falls outside this list and outside the secret list, the default action is to ask Claude whether it should be committed. The list is not exhaustive, and ambiguous cases are resolved in session, not by operator judgement alone.

## A.5 Where secrets actually live

- **Platform environment variables.** Render's service-environment interface, Netlify's site-environment interface. Values are entered directly into the platform's web UI. Code reads them at runtime by variable name. Neither the plaintext value nor the variable name-plus-value pair ever enters the repo.

- **Operator's password manager.** Passwords, 2FA seeds, recovery codes, backup-storage access keys. Not shared with Claude in chat; not committed; not emailed to anyone.

- **Operator's Polymarket US app and account.** The account itself is the source of truth for its own credentials. Account-adjacent identifiers (email, wallet, etc.) are not written down in the project materials.

## A.6 The "I'm about to type a secret into chat" guard

If the operator is about to paste something into the chat that matches the secret list, the right procedure is: don't. Claude does not need secret values to build the project; Claude writes the code that reads the environment variable, and the operator enters the value into the platform UI separately. If a procedure ever seems to require Claude to see a secret, that procedure is wrong; Claude should be asked to propose an alternative that keeps the secret out of the chat.

If a secret is accidentally pasted into chat, the session is not safe and the affected credential is rotated at the source (e.g., revoke the token at the platform, generate a new one). The event is logged to DecisionJournal as a security incident. The chat transcript may still contain the leaked value and should be treated as compromised; subsequent sessions do not reference the prior chat for continuity.

## A.7 The "Claude is about to produce a file that contains a secret" guard

If Claude produces a file for the operator to commit and that file contains what appears to be a secret (an API key, a token, a password, account detail), Claude is obligated to flag it and either remove the sensitive content or restructure the file to read from an environment variable. The operator is obligated to notice flags. If a flagged file is committed anyway, this is an out-of-protocol event or a drift incident; it is logged to DecisionJournal.

---

# Part B — Policy statement

This section is written for readers of the public repository who want to understand the project's posture toward secrets, personal information, and trading-related material. It is also the authoritative version of the rules summarized in Part A.

## B.1 Project context

PM-Tennis is a personal-use trading instrument and observation system built around a specific mispricing thesis on Polymarket US's in-play tennis markets. It is designed, built, and operated by a single non-technical operator working with an AI assistant (Claude) across a series of chat sessions. The project is deliberately governed: a written build plan, a decision journal, a risk/assumption/issue log, a pre-commitment register, and this secrets policy, among other artifacts, together make the project auditable from its history.

The project's code and governance artifacts live in a **public** Git repository. Public visibility was a deliberate choice, not an accident of convenience. The reasoning, stated in DecisionJournal entry D-005, is that a public repo forces discipline around secrets that is desirable regardless of who is watching, and that the project's strategy, thesis, and commitment files are meant to be transparent for the pre-commitment discipline to carry epistemic weight.

What is public is the *design*. What is not public is *which specific human operates the account, where they are, how much they are trading, and what positions they currently hold*. This distinction — public strategy, private operator — is the shape of the policy.

## B.2 What this project does not put in the repository

The following material is not in the repository, will not be in the repository, and any commit that introduces it is a policy violation and subject to the response procedure in B.5.

**Platform authentication material.** Passwords, 2FA seeds, OAuth tokens, API keys, deploy keys, build tokens, personal access tokens, and any credential that would grant a third party access to the project's GitHub organization, Netlify account, Render service, backup storage, domain registrar, or any other account the project depends on. These credentials live in the respective platform's environment-variable or credential-management interface, entered directly through the platform's web UI, and referenced in code by variable name only.

**Operator identity information.** The operator is not named in the repository. The operator's exact location is not recorded in the repository. The operator's contact details are not in the repository. The coarse framing that the operator is US-based and holds a funded Polymarket US account is the level of specificity the project commits to publicly; anything finer than that is out of scope for repo content.

**Polymarket US account identifiers.** The account email, the wallet address (if any), the trading account balance in absolute dollars, and any identifier that would let a third party map the project to the specific Polymarket account it operates on are not in the repository. Position sizes are discussed in *relative* terms ("$25 notional per entry" per the build plan's Section 9) because that is a strategic parameter, not in *absolute* terms that would imply total capital.

**Real-time trading state.** Live open positions, recent fills, current orders resting on the exchange — anything that would let an observer front-run a trade in progress — are not pushed to the repo. The admin UI that displays this information is protected by the `X-PM-Tennis-Token` shared secret and does not replicate the content to git.

**Historical trading records (by default).** The manual-trade logs, reconciliation logs, operator-availability logs, and window-close analytical outputs are not in the public repo as a matter of default. They are preserved in the platform's persistent storage and in the project's nightly backup. Whether individual window-close results are eventually published (in whole, in part, or in anonymized summary) is an operator decision at the time, logged to DecisionJournal when made.

**The captured archive itself.** The JSONL files containing per-tick order-book state, score events, and manual-trade envelopes are not in the repo. They would be unsuitable for git regardless of sensitivity (they are large, append-only, and gzipped nightly), but they are also sensitive under the preceding paragraph. They live on the Render persistent disk and are synced nightly to the managed object-storage backup. Any decision to publish any portion of the archive is explicit and logged.

## B.3 What this project does put in the repository

The following material is in the repository. Publication is deliberate and supports the project's governance model.

**The build plan.** The full specification of what the project is, what it captures, how it analyzes, what its decision criteria are, and what it will and will not do. The plan is versioned; prior versions are preserved in git history.

**The governance artifacts.** STATE, Playbook, Orientation, DecisionJournal, RAID, PreCommitmentRegister, SECRETS_POLICY, session handoff documents, and any future governance artifact produced by the project. These are public for auditability — the pre-commitment discipline depends on them being inspectable, not on them being hidden.

**The source code.** All capture code, API code, replay simulator code, dashboard code, admin-UI code, test harnesses, diagnostic tooling, and scripts. This includes code that reads secrets from environment variables; the code is public but the values are not.

**The commitment files.** `signal_thresholds.json`, `fees.json`, `breakeven.json`, and `sackmann/build_log.json` once they exist. These are *pre-commitments* — values frozen before observation begins, against which outcomes are measured. Their publication is load-bearing for the project's epistemic integrity. Changes to these files during an active observation window are prohibited by the soft lock described in the build plan's Section 9.6 and Playbook §6.

**Infrastructure-as-code and configuration.** Dockerfiles, docker-compose files, Render service configuration, Netlify build settings, GitHub Actions workflows if any, and similar. These describe how the project is deployed; they reference secrets by environment-variable name but do not contain values.

**Tests, parity vectors, and fixtures.** The JS/Python fair-price parity test vector, the Sackmann pipeline validation fixtures, replay simulator unit tests, and similar. Tests are part of the project's audit trail.

## B.4 How secrets are handled in practice

The mechanism by which secrets stay out of the repo is simple and has three layers.

**Layer 1: Operator self-discipline.** The operator, before any commit, reviews the files to be committed against the list in B.2. This is the primary defense. The Part A quick-reference exists to make this review fast.

**Layer 2: Claude as a check.** Per the build plan's Section 1.5.4, Claude is obligated to flag any file it produces that contains what appears to be a secret, and to propose an alternative structure (read from environment variable, move to a non-repo location, redact). The operator is obligated to act on the flag. A file flagged as containing secrets is not committed without resolution.

**Layer 3: GitHub secret scanning.** GitHub provides automated secret scanning on public repositories as a free built-in feature. This is a post-hoc backstop — it catches certain classes of leaked credentials after they are pushed, triggers an alert, and in some cases can automatically revoke tokens at the credential-issuing platform. It does not prevent leaks, but it shortens the window between a leak and its detection, and it catches common-format secrets that the operator might miss on manual review.

A pre-commit hook layer, which would block secret-containing commits before they are created, is deliberately *not* in the initial policy. It would require CI tooling that the project has not yet set up, and it would need careful pattern configuration to avoid false positives. Adding this layer is a candidate future enhancement once the repo and CI infrastructure exist. It is tracked as an optional improvement; its absence is compensated by the three layers above.

## B.5 Response to a suspected secret leak

If a secret is suspected to have entered the repository — whether detected by the operator, by Claude, by GitHub secret scanning, or by a third party — the response procedure is:

1. **Rotate the credential at its source.** Revoke the token at the platform that issued it; generate a new one. Do not rely on removing the file from the repo, because git preserves history and a leaked value is compromised regardless of whether it is later deleted from the tip of the branch. The credential is burned; a new one replaces it.

2. **Update the platform environment variable** to use the new credential.

3. **Remove the offending content** from the repo. For a leak that has already been pushed, this may require force-pushing a history rewrite; the simpler and recommended alternative is to leave the git history as is (since the credential is already rotated and the old value is now inert) and proceed.

4. **Log the incident to DecisionJournal.** A full entry: what was leaked, how it was discovered, what was rotated, what remediation was applied, and whether any downstream effects are possible (e.g., if the token had write access to anything that a bad actor might have abused in the window between leak and rotation).

5. **Review the chat transcript** for the session in which the leak originated. If the secret was pasted into chat by the operator (rather than inserted by Claude into a generated file), the transcript contains the leaked value and should be treated as compromised. Subsequent sessions do not reference the transcript for continuity.

6. **If the project is in active observation**, evaluate whether the incident materially affects the integrity of the window. Credential leaks typically do not — they are an access-control issue, not a data-integrity issue — but the evaluation is explicit rather than assumed.

## B.6 What this policy does not cover

**The operator's personal security.** This document governs project-level handling of secrets and identifiers. It does not cover the operator's broader personal security posture (password manager hygiene, device security, physical security, OPSEC for the Polymarket account). Those are the operator's responsibility and are outside the project's scope.

**Legal and regulatory compliance.** The project operates on Polymarket US, a CFTC-regulated Designated Contract Market. Compliance with CFTC rules, tax reporting, and any other legal obligations is the operator's responsibility and is outside the scope of this document.

**Adversarial threat modeling.** This document assumes the threat model is inadvertent leakage (forgot to gitignore a file, pasted a token into the wrong place, committed a file that mixed sensitive and public content) rather than targeted attack. A determined attacker with some knowledge of the project could probably fingerprint the operator through indirect evidence in the public repo. Hardening against that level of threat is not a goal; the goal is to keep casual observers out of credentials and identity.

**Claude's own behavior outside chat.** This document governs what enters the repo. It does not make claims about what Anthropic's infrastructure does with chat content, what Claude's model weights encode about conversations, or any other aspect of the AI-assistant provider's data handling. The operator's use of Claude is subject to Anthropic's own terms and privacy policy, which are outside this document.

## B.7 Changes to this policy

This policy itself is a governance artifact. Changes to it follow the same pattern as other governance documents: a new DecisionJournal entry names the change and its reasoning, the document is revised, the change is committed with the revision in the commit message. Policy changes during active observation are permitted if they do not affect the observation's integrity; changes that would affect the observation (e.g., relaxing what counts as a secret in a way that would make prior window data interpretable differently) are subject to the same constraint as commitment-file changes — they end the current window if made during one.

---

*End of SECRETS_POLICY.md at end of session H-002.*
