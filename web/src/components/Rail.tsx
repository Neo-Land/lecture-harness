"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { api, coursePath, type Schemas } from "@/lib/api";

/** Left rail: every course, refreshed on navigation so a new upload appears. */
export function Rail() {
  const pathname = usePathname();
  const [courses, setCourses] = useState<Schemas["CourseOut"][] | null>(null);

  useEffect(() => {
    api
      .GET("/courses")
      .then(({ data }) => setCourses(data ?? []))
      .catch(() => setCourses([]));
  }, [pathname]);

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
            </li>
          ))}
        </ul>
      ) : (
        courses && <p className="note">No courses yet.</p>
      )}
      <Link className="add-lecture" href="/">
        Add a lecture
      </Link>
    </nav>
  );
}
