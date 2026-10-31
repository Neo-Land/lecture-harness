# 0006 — Public demo: offline by default, Vercel and Render

- **Status:** accepted
- **Date:** 2026-10-31

## Context
A public demo link helps recruiters, but it is open to anyone. It must not leak course material or spend
money without limit, and its owner has a $5 API budget.

## Options considered
1. Live model on every question: the most impressive, but every visitor spends money.
2. Offline, quoting slides: free and safe, but it shows the app and not the model's writing.
3. Live summaries generated once, then offline: real AI output at a fixed cost, and the same code.

## Decision
Start with option 2, and move to option 3 by rebuilding the image with a key once live runs are done. Host
the web app on Vercel and the API on Render, since both connect to GitHub and have free tiers. Their terms
and limits should be checked at setup.

## Consequences
- The page says plainly that the demo copies lines from slides.
- Render's free tier sleeps when idle, so the first visit can take up to a minute.
- Limits are in memory and reset on restart, which is acceptable because the default demo costs nothing. A
  live demo also needs a spend limit on its API key.
