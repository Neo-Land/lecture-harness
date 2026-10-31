"use client";

import { useState } from "react";
import { api, CANT_REACH_API } from "@/lib/api";

const plural = (n: number) => `${n} new or updated ${n === 1 ? "lecture" : "lectures"}`;

/** Pulls new lectures from Canvas. Only shown when the API has Canvas configured. */
export function SyncButton({ onSynced }: { onSynced: () => void }) {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function sync() {
    setBusy(true);
    setMessage(null);
    try {
      const { data, error } = await api.POST("/sync");
      if (data) {
        setMessage(data.length ? `Added ${plural(data.length)}.` : "Everything is up to date.");
        onSynced();
      } else {
        setMessage((error as { detail?: string })?.detail ?? "Sync failed. Try again.");
      }
    } catch {
      setMessage(CANT_REACH_API);
    }
    setBusy(false);
  }

  return (
    <div className="sync">
      <button type="button" className="on-cover" onClick={sync} disabled={busy}>
        {busy ? "Syncing…" : "Sync with Canvas"}
      </button>
      <p className="note" aria-live="polite">
        {message}
      </p>
    </div>
  );
}
