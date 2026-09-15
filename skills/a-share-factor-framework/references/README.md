# Active reference index

This directory contains the active, portable method references for the factor harness. Machine control rules live under `runtime/`; these documents explain how workers should apply them.

## 01-architecture

Factor layering, single-factor meaning, prompt/reference boundaries, codex structure, and first-principles startup.

## 02-data-pipeline-and-neutralization

Data fields, coverage, accounting definitions, stock-pool handling, neutralization, and data troubleshooting.

## 03-factor-patterns

Reusable factor construction and backtest patterns. Historical examples are method references, not conclusions to copy.

## 04-audit-and-governance

Review gates, deduplication, failure history, Kanban handoff, pipeline health, retry and direction governance.

`archive/` material is intentionally excluded from the portable release. The active set is organized by topic so workers can load only the references needed for a phase.
