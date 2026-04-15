"use client";

import { useEffect, useState } from "react";
import { fetchIndexStatus } from "@/lib/api";
import { IndexStatus } from "@/lib/types";

export function useIndexStatus(pollIntervalMs = 3000) {
  const [status, setStatus] = useState<IndexStatus | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let active = true;

    async function poll() {
      try {
        const s = await fetchIndexStatus();
        if (active) { setStatus(s); setError(false); }
      } catch {
        if (active) setError(true);
      }
    }

    poll();
    const id = setInterval(poll, pollIntervalMs);
    return () => { active = false; clearInterval(id); };
  }, [pollIntervalMs]);

  return { status, error };
}
