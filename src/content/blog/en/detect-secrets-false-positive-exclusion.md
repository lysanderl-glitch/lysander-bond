---
title: "Tuning Detect-Secrets to Ignore Business Identifiers"
description: "Tuning Detect-Secrets to Ignore Business Identifiers"
publishDate: 2026-06-07T00:00:00.000Z
slug: detect-secrets-false-positive-exclusion
lang: en
keywords:
  - AI工程
  - Synapse
  - T类
author: lysander
---

## TL;DR

- 32-char hex projectIds trigger false positives (entropy ≈ 4.3, threshold 0.5)
- Shannon entropy measures randomness, not sensitivity or secret-ness
- Configure exclude rules in .detect-secrets.yaml for business identifiers
- Use baseline files to manage existing false positives before scanning
- Prefer precise field name matching over broad file exclusions

## Body

Our CI/CD pipeline started failing because detect-secrets kept flagging 32-character hexadecimal strings as "High Entropy Secret" warnings. These strings were projectId values—plain business identifiers, not secrets at all. A standard projectId yields an entropy value around 4.3, while detect-secrets defaults to a threshold of 0.5. Because entropy approaches 1.0 for purely random strings, hex strings get flagged almost inevitably.

The real issue stems from a fundamental misunderstanding: we assumed entropy越高等于越可能是密钥. In reality, entropy only quantifies randomness, not sensitivity. A 32-character hex string can be a JWT secret or simply a projectId. Lowering entropy_threshold to fix this causes true secrets to slip through undetected.

The correct approach is to configure exclude rules in .detect-secrets.yaml. We added field names like 'projectId', 'appId', and 'deviceId' to the exclude list under the HighEntropyStrings plugin. For more precise matching, we used regex patterns targeting specific hex formats. For existing false positives in our codebase, we generated a baseline file with `detect-secrets scan > .detect-secrets-baseline.json`, then ran `detect-secrets audit` to interactively mark projectId entries as allowlisted. These markings persist in the baseline file and skip future scans automatically.

The takeaway: treat entropy as a randomness metric, not a sensitivity indicator. Exclude business identifiers through precise field matching rather than lowering detection standards.

## Key Takeaways

If you encounter business ID false positives, exclude them by exact field name in .detect-secrets.yaml rather than lowering entropy_threshold.

If you have existing false positives in your codebase, generate a baseline file with detect-secrets scan, then use detect-secrets audit to mark them as allowlisted before configuring new exclude rules.

If you are evaluating whether to exclude a string, ask "Is this actually a secret?" instead of "Does this have high entropy?"

If you are rolling out detect-secrets to a team, configure exclude rules upfront—retrofitting false positive fixes costs significantly more than prevention.

## Read the Full Article (Chinese)

This is an abstract. The full technical walkthrough, including YAML configuration examples and the Shannon Entropy formula, is in Chinese.
