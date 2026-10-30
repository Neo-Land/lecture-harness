# 0004 — Eval metrics, and downloading decks instead of committing them

- **Status:** accepted
- **Date:** 2026-10-30

## Context
Resume numbers need to be defensible, and the plan called for committing open-license decks. Reading
them showed MIT excludes some third-party images on specific slides from its license.

## Options considered
1. Commit the PDFs: simple, but republishes excluded images in a public repo.
2. Commit links and checksums, and download on demand: same files every time, nothing republished, but
   evals need network access.
3. Edit the PDFs to remove those slides: changes the source and slide numbers.

## Decision
Option 2. Golden and planted sets use TOML, which the standard library reads, so no YAML dependency.
Metrics are first-attempt grounding, golden coverage, planted-error recall by kind, false alarms on true
controls, revisions per deck, and estimated cost.

## Consequences
- Coverage is a keyword check: a claim can capture a point in other words and not be counted, so it runs low.
- Recall is reported by kind because one blended number would hide that the deterministic layers catch
  mechanical errors and not errors of meaning.
- The sets were written by the verifier's author, which flatters the score until Neo reviews them.
- A public demo must omit the three excluded slide images.
