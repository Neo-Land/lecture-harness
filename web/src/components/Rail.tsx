"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { api, coursePath, type Schemas } from "@/lib/api";
import { SyncButton } from "./SyncButton";

/** Left rail: every course, refreshed on navigation so a new upload appears. */
export function Rail() {
  const pathname = usePathname();
  const [courses, setCourses] = useState<Schemas["CourseOut"][] | null>(null);
  const [canvas, setCanvas] = useState(false);

  const load = useCallback(() => {
    api
      .GET("/courses")
      .then(({ data }) => setCourses(data ?? []))
      .catch(() => setCourses([]));
  }, []);

  useEffect(load, [load, pathname]);

  useEffect(() => {
    api
      .GET("/config")
      .then(({ data }) => setCanvas(!!data?.canvas))
      .catch(() => setCanvas(false));
  }, []);

  return (
    <nav className="rail" aria-label="Courses">
      <Link className="wordmark" href="/">
        Lecture Harness
      </Link>
      {courses?.length ? (
        <ul>
          {courses.map((c) => (
            <li key={c.course}>
              <Link href={coursePath(c.course)}>
                <span>{c.course}</span>
                <span>{c.decks}</span>
              </Link>
              {c.last_synced && (
                <small className="synced">Synced {new Date(c.last_synced).toLocaleString()}</small>
              )}
            </li>
          ))}
        </ul>
      ) : (
        courses && <p className="note">No courses yet.</p>
      )}
      <Link className="add-lecture" href="/">
        Add a lecture
      </Link>
      {canvas && <SyncButton onSynced={load} />}
    </nav>
  );
}
