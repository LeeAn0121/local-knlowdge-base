"use client";

import { useEffect, useState } from "react";

export interface Settings {
  topK: number;
  minScore: number;
}

const DEFAULTS: Settings = { topK: 8, minScore: 0.2 };
const KEY = "kb-settings";

export function useSettings() {
  const [settings, setSettings] = useState<Settings>(DEFAULTS);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(KEY);
      if (stored) setSettings({ ...DEFAULTS, ...JSON.parse(stored) });
    } catch {
      // ignore
    }
  }, []);

  function update(partial: Partial<Settings>) {
    setSettings((prev) => {
      const next = { ...prev, ...partial };
      localStorage.setItem(KEY, JSON.stringify(next));
      return next;
    });
  }

  return { settings, update };
}
