// Typed API client. Types come from the backend's schema: `npm run gen:api`.
import createClient from "openapi-fetch";
import type { components, paths } from "./api-types";

export type Schemas = components["schemas"];
export type DeckDetail = Schemas["DeckDetail"];
export type AskResponse = Schemas["AskResponse"];
export type IngestResult = Schemas["IngestResult"];
export type VisualSpec = Schemas["VisualSpec"];
export type VerificationReport = Schemas["VerificationReport"];
export type Slide = Schemas["Slide"];

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const api = createClient<paths>({ baseUrl: API_URL });

export const slideImageUrl = (deckId: string, n: number) =>
  `${API_URL}/decks/${encodeURIComponent(deckId)}/slides/${n}/image`;

export const coursePath = (course: string) => `/courses/${encodeURIComponent(course)}`;
export const deckPath = (deckId: string, slide?: number) =>
  `/decks/${encodeURIComponent(deckId)}${slide ? `?slide=${slide}` : ""}`;

export const CANT_REACH_API = `Can't reach the API at ${API_URL}. Start it with: uvicorn app.api:app --reload`;

/** Upload a lecture. Plain fetch, since the file is multipart form data. */
export async function uploadLecture(course: string, file: File): Promise<IngestResult> {
  const form = new FormData();
  form.append("course", course);
  form.append("file", file);
  const res = await fetch(`${API_URL}/upload`, { method: "POST", body: form });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `Upload failed with status ${res.status}`);
  }
  return res.json();
}
