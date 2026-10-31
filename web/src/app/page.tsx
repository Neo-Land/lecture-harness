"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { api, coursePath, deckPath, uploadLecture } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [demo, setDemo] = useState(false);

  useEffect(() => {
    api
      .GET("/config")
      .then(({ data }) => setDemo(!!data?.demo))
      .catch(() => setDemo(false));
  }, []);

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
        Every claim in these notes links to the slide it came from. Claims that fail the check against
        their slide are removed.
      </p>
      {demo ? (
        <>
          <p>
            <Link href={coursePath("MIT 6.0001")}>Open the sample course</Link>. This demo is read-only and
            copies lines from the slides instead of using AI, so it shows the app, not the model&apos;s writing.
          </p>
          <p className="muted-note">
            Slides: Ana Bell, Eric Grimson, and John Guttag, 6.0001 Introduction to Computer Science and
            Programming in Python, Fall 2016, MIT OpenCourseWare,{" "}
            <a href="https://ocw.mit.edu/courses/6-0001-introduction-to-computer-science-and-programming-in-python-fall-2016/">
              ocw.mit.edu
            </a>
            , <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/">CC BY-NC-SA</a>.
          </p>
        </>
      ) : (
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
      )}
    </div>
  );
}
