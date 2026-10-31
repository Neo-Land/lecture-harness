"use client";

import { useState } from "react";
import { type DeckDetail, slideImageUrl } from "@/lib/api";
import { CheckNote } from "./CheckNote";
import { Visual } from "./Visuals";

/** The lecture page: notes with citations on one side, the cited slide pinned on the other. */
export function LectureView({ detail, initialSlide }: { detail: DeckDetail; initialSlide?: number }) {
  const { deck, summary } = detail;
  const numbers = deck.slides.map((s) => s.number);
  const [slideNumber, setSlideNumber] = useState(
    initialSlide && numbers.includes(initialSlide) ? initialSlide : numbers[0],
  );
  const [activeClaim, setActiveClaim] = useState<number | null>(null);
  const slide = deck.slides.find((s) => s.number === slideNumber);
  const index = numbers.indexOf(slideNumber);

  function show(n: number, claim: number | null = null) {
    setSlideNumber(n);
    setActiveClaim(claim);
  }

  return (
    <>
      <h1>{deck.title}</h1>
      <div className="lecture">
        <section aria-label="Notes">
          <CheckNote detail={detail} />
          {summary && summary.abstract.length > 0 && (
            <ol className="claims">
              {summary.abstract.map((claim, i) => (
                <li key={claim.text}>
                  <span className={`claim-text${activeClaim === i ? " active" : ""}`}>{claim.text}</span>
                  {claim.slides.map((n) => (
                    <button
                      key={n}
                      type="button"
                      className="cite"
                      aria-pressed={activeClaim === i && slideNumber === n}
                      aria-label={`Show slide ${n}`}
                      onClick={() => show(n, i)}
                    >
                      slide {n}
                    </button>
                  ))}
                </li>
              ))}
            </ol>
          )}
          {summary?.visuals?.map((v) => <Visual key={v.title} visual={v} onCite={(n) => show(n)} />)}
        </section>

        {slide && (
          <section className="slide-pane" aria-label={`Slide ${slide.number}`}>
            {slide.has_image ? (
              // eslint-disable-next-line @next/next/no-img-element -- served by our API, sizes vary per deck
              <img
                key={slide.number} // a new element, so the old slide never shows under the new label
                src={slideImageUrl(deck.id, slide.number)}
                alt={`Slide ${slide.number}: ${slide.text.slice(0, 300) || "no readable text"}`}
              />
            ) : (
              <pre className="slide-text">{slide.text || "This slide has no readable text."}</pre>
            )}
            <div className="slide-nav">
              <button type="button" disabled={index <= 0} onClick={() => show(numbers[index - 1])}>
                Previous
              </button>
              <span aria-live="polite">
                Slide {slide.number} of {numbers.length}
              </span>
              <button type="button" disabled={index >= numbers.length - 1} onClick={() => show(numbers[index + 1])}>
                Next
              </button>
            </div>
          </section>
        )}
      </div>
    </>
  );
}
