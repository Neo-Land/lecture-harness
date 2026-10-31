import type { DeckDetail } from "@/lib/api";

const plural = (n: number, word: string) => `${n} ${word}${n === 1 ? "" : "s"}`;

/** Says in plain words what the verifier did, and flags anything the reader should know. */
export function CheckNote({ detail }: { detail: DeckDetail }) {
  const { report, deck, model, attempts } = detail;
  const scanned = deck.slides.filter((s) => s.needs_ocr).map((s) => s.number);
  const revisions = Math.max((attempts ?? 1) - 1, 0);
  const removed = report ? report.claims_total - report.claims_supported : 0;

  return (
    <>
      {report && report.claims_total > 0 && (
        <p className="check-note">
          {report.claims_supported} of {plural(report.claims_total, "claim")} checked against the slides
          {revisions > 0 && `, after ${plural(revisions, "revision")}`}.
          {removed > 0 && ` ${plural(removed, "claim")} failed the check and ${removed === 1 ? "was" : "were"} removed.`}
        </p>
      )}
      {model === "extractive-offline" && (
        <p className="notice">Offline mode: these lines are copied from the slides, not written by AI.</p>
      )}
      {scanned.length > 0 && scanned.length < deck.slides.length && (
        <p className="notice">
          {scanned.length === 1 ? "Slide" : "Slides"} {scanned.join(", ")} {scanned.length === 1 ? "is" : "are"} scanned,
          so the notes don&apos;t cover {scanned.length === 1 ? "it" : "them"}.
        </p>
      )}
      {scanned.length > 0 && scanned.length === deck.slides.length && (
        <p className="notice">This lecture is scanned, so there is no text to summarize. Upload a version with selectable text.</p>
      )}
    </>
  );
}
