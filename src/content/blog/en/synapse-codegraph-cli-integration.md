---
title: "Synapse CLI Activation: Whitelist and D-record Pitfalls"
description: "Synapse CLI Activation: Whitelist and D-record Pitfalls"
publishDate: 2026-05-30T00:00:00.000Z
slug: synapse-codegraph-cli-integration
lang: en
keywords:
  - AI工程
  - Synapse
  - B类
author: lysander
---

## TL;DR

- Whitelist controls visibility, not activation capability
- D-record is mandatory for CodeGraph CLI activation
- Missing activation_context field causes silent failure
- Verify activation status via synapse tool status command
- Both mechanisms required; one is not sufficient

The Synapse platform requires both a whitelist entry and a D-record for any CLI tool to function. Our team spent 47 minutes debugging a ToolNotActivatedError because we assumed the whitelist was the activation switch. It is not. The whitelist only makes the tool visible in Synapse's execution context. A D-record is required to complete initialization and make the tool executable.

The hidden complexity is that D-record creation fails silently. The CLI returns a generic "requires activation" error without indicating whether the D-record is missing or malformed. In our case, the D-record existed but lacked the mandatory activation_context field. Synapse rejected activation without clear feedback. The correct D-record format requires tool_id, version, environment, owner, and activation_context with at least one scope defined.

After adding activation_context with scopes "dependency_analysis" and "security_scan", the codegraph tool activated successfully. We verified this using `synapse tool status --tool codegraph --env production`, which returned status: activated.

This dual-layer mechanism exists for security audit compliance. Security teams maintain the whitelist while business teams create D-records, ensuring both visibility control and usage tracking. The friction we experienced stemmed from documentation that implied the whitelist was sufficient, when in reality both components must be configured correctly.

## Key Takeaways

- If you configure a Synapse whitelist without a D-record, the CLI will fail with a generic activation error
- If you create a D-record without the activation_context field, activation silently fails
- If you debug activation errors, check D-record existence and field completeness before modifying the whitelist
- If you deploy to multiple environments, create separate D-records for dev, staging, and production
- If you verify activation, always query the registry endpoint rather than testing with actual workloads

## Read the Full Article (Chinese)

This is an abstract. The full technical walkthrough with YAML examples and command-line instructions is available in the original Chinese article.
