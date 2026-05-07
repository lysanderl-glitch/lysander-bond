---
title: "Detecting Dormant n8n Workflows with REST API"
description: "Detecting Dormant n8n Workflows with REST API"
publishDate: 2026-05-05T00:00:00.000Z
slug: n8n-workflow-governance-slumber-cleanup
lang: en
keywords:
  - AI工程
  - Synapse
  - B类
author: lysander
---

## TL;DR
- Use n8n REST API to fetch workflow metadata and identify inactive workflows
- Dormant threshold: last execution more than 30 days ago
- Scanned 21 workflows, flagged 7 for cleanup evaluation
- Export JSON configuration backups before deleting any workflow
- Establish monthly audit cadence as standard engineering practice

We discovered during Q3 2024 that our n8n admin dashboard workflow list had grown unmanageable. Out of 21 workflows, 7 had zero executions in over 30 days. The oldest—named "data sync-old CRM"—had not run since January 2024, eight months before the audit. Nobody could confirm whether it was still needed.

The root cause: n8n stores workflow metadata (creation time, update time, active status) and execution data (execution timestamps, status) in separate API endpoints. Correlating them requires custom queries. The UI shows "last edited time" which is misleading—one workflow was edited 3 days ago but had no executions for 47 days; another ran daily but was not touched for months. Additionally, the UI offers no way to sort by last execution or batch-export metadata.

Our solution was a Python script (audit_n8n_workflows.py) that calls the /rest/workflows and /rest/executions endpoints, fetches the latest execution record for each workflow, calculates days since last run, and flags those exceeding the dormant threshold. Before deleting anything, we export JSON configurations for backup.

## Key Takeaways
- If you manage multiple workflows, use execution history rather than edit timestamps as the cleanup signal
- If you rely on the n8n UI for audits, expect incomplete data and manual effort
- If you automate audits with the REST API, cross-reference workflow metadata with execution endpoints
- If you clean up stale workflows, export JSON backups first to prevent accidental data loss
- If you want to prevent reoccurrence, schedule monthly audits and document your threshold criteria

## Read the Full Article (Chinese)
This is an abstract. The full technical walkthrough, including the complete Python script, is available in the original Chinese article.
