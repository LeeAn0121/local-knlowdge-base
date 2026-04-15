"use client";

import { useEffect, useState } from "react";

export type Theme = "dark" | "light";

export function useTheme() {
  const [theme, setTheme] = useState<Theme>("dark");

  useEffect(() => {
    const stored = (localStorage.getItem("kb-theme") as Theme) ?? "dark";
    apply(stored);
    setTheme(stored);
  }, []);

  function toggle() {
    const next: Theme = theme === "dark" ? "light" : "dark";
    apply(next);
    setTheme(next);
    localStorage.setItem("kb-theme", next);
  }

  return { theme, toggle };
}

function apply(theme: Theme) {
  document.documentElement.setAttribute("data-theme", theme);
}
