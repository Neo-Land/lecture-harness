"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";
import { deckPath, uploadLecture } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(true);
    setError(null);
    try {
      const result = await uploadLecture(String(form.get("course")).trim(), form.get("file") as File);
      router.push(deckPath(result.deck_id));
    } catch (err) {
      setError(err instanceof TypeError ? "Can't reach the API. Check that it's running." : String((err as Error).message));
      setBusy(false);
    }
  }

  return (
    <div className="narrow">
      <h1>Lecture notes you can check against the slides</h1>
      <p className="lede">
        Add a lecture and get a summary where every claim links to the slide it came from. Claims that
        fail the check against their slide are removed.
      </p>
      <form className="stack" onSubmit={onSubmit}>
        <label>
          Course
          <input type="text" name="course" required placeholder="CS 2" />
        </label>
        <label>
          Slides (PDF or PPTX)
          <input type="file" name="file" required accept=".pdf,.pptx" />
        </label>
        <div>
          <button type="submit" disabled={busy}>
            {busy ? "Reading the slides…" : "Add lecture"}
          </button>
        </div>
        <div aria-live="polite">{error && <p className="error">{error}</p>}</div>
      </form>
    </div>
  );
}
