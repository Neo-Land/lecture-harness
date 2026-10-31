"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import { AskBox } from "@/components/AskBox";
import { api, CANT_REACH_API, deckPath, type Schemas } from "@/lib/api";

export default function CoursePage({ params }: { params: Promise<{ course: string }> }) {
  const course = decodeURIComponent(use(params).course);
  const [decks, setDecks] = useState<Schemas["DeckListItem"][] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .GET("/courses/{course}/decks", { params: { path: { course } } })
      .then(({ data }) => setDecks(data ?? []))
      .catch(() => setError(CANT_REACH_API));
  }, [course]);

  return (
    <>
      <h1>{course}</h1>
      {error && <p className="error">{error}</p>}
      {decks?.length === 0 && (
        <p>
          This course has no lectures yet. <Link href="/">Add a lecture</Link>.
        </p>
      )}
      {!!decks?.length && (
        <>
          <ul className="lectures">
            {decks.map((d) => (
              <li key={d.id}>
                <Link href={deckPath(d.id)}>{d.title}</Link>
                <span className="muted">{d.slides} slides</span>
              </li>
            ))}
          </ul>
          <h2>Ask about this course</h2>
          <AskBox course={course} />
        </>
      )}
    </>
  );
}
