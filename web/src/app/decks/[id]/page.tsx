"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, use, useEffect, useState } from "react";
import { LectureView } from "@/components/LectureView";
import { api, CANT_REACH_API, type DeckDetail } from "@/lib/api";

function Lecture({ id }: { id: string }) {
  const slide = Number(useSearchParams().get("slide")) || undefined;
  const [detail, setDetail] = useState<DeckDetail | null>(null);
  const [error, setError] = useState<React.ReactNode>(null);

  useEffect(() => {
    api
      .GET("/decks/{deck_id}", { params: { path: { deck_id: id } } })
      .then(({ data }) => {
        if (data) setDetail(data);
        else setError(<>This lecture doesn&apos;t exist. <Link href="/">Add a lecture</Link>.</>);
      })
      .catch(() => setError(CANT_REACH_API));
  }, [id]);

  if (error) return <p className="error">{error}</p>;
  if (!detail) return <p aria-live="polite">Loading the lecture…</p>;
  return <LectureView key={`${id}-${slide}`} detail={detail} initialSlide={slide} />;
}

export default function DeckPage({ params }: { params: Promise<{ id: string }> }) {
  const id = decodeURIComponent(use(params).id);
  return (
    <Suspense>
      <Lecture id={id} />
    </Suspense>
  );
}
