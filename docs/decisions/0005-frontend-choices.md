# 0005 — Frontend: client-fetched Next.js with generated API types

- **Status:** accepted
- **Date:** 2026-10-31

## Context
The frontend shows verified notes next to their slides and asks questions per course. It must stay in
step with the backend's API and render visuals that come from model output.

## Options considered
1. Hand-written API types: no tooling, but they drift from the backend without anyone noticing.
2. Types generated from FastAPI's OpenAPI schema: one source of truth, and a test fails if the committed
   schema is stale.
3. Server-rendered data fetching: faster first paint, but the API then has to be reachable from the web
   host as well as the browser, which complicates local use and the demo.

## Decision
Option 2 for types, using `openapi-typescript` and `openapi-fetch`, with data fetched in the browser.
Plain CSS instead of a component library, because the page's look is its own and small. Mermaid only
draws concept maps; tables, timelines, and key terms are native HTML, which is simpler and more accessible.

## Consequences
- Pages show a brief loading state, which is fine for a personal study tool.
- Mermaid is heavy, so it is imported only when a concept map appears.
- Model text reaches Mermaid, so labels are quoted and Mermaid runs in `strict` security mode. Every concept
  map also has a text version for screen readers.
- TypeScript stays on version 5, which `openapi-typescript` requires.
