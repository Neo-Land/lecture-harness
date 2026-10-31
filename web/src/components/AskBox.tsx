"use client";

import Link from "next/link";
import { type FormEvent, useState } from "react";
import { api, type AskResponse, CANT_REACH_API, deckPath } from "@/lib/api";

/** Question box scoped to one course. Answers only come back with slide citations. */
export function AskBox({ course }: { course: string }) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<AskResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setAnswer(null);
    try {
      const { data, error: failure } = await api.POST("/ask", { body: { course, question } });
      if (data) setAnswer(data);
      else {
        const detail = (failure as { detail?: unknown })?.detail;
        setError(typeof detail === "string" ? detail : "The question couldn't be answered. Try again.");
      }
    } catch {
      setError(CANT_REACH_API);
    }
    setBusy(false);
  }

  return (
    <>
      <form className="ask-row" onSubmit={onSubmit}>
        <label>
          Question
          <input
            type="text"
            required
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="What is merge sort's worst case?"
          />
        </label>
        <button type="submit" disabled={busy}>
          {busy ? "Checking the slides…" : "Ask"}
        </button>
      </form>
      <div aria-live="polite" className="narrow" style={{ marginTop: "var(--line)" }}>
        {error && <p className="error">{error}</p>}
        {answer?.insufficient_evidence && <p>Not covered in the slides.</p>}
        {answer && !answer.insufficient_evidence && (
          <ul className="claims">
            {answer.claims.map((claim) => (
              <li key={claim.text}>
                <span className="claim-text">{claim.text}</span>
                {claim.sources.map((s) => (
                  <Link className="cite" key={`${s.deck_id}-${s.slide}`} href={deckPath(s.deck_id, s.slide)}>
                    {s.deck_title}, slide {s.slide}
                  </Link>
                ))}
              </li>
            ))}
          </ul>
        )}
      </div>
    </>
  );
}
