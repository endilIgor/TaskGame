import { useEffect } from "react";

declare global {
  interface Window {
    liquidGL?: (options: Record<string, unknown>) => unknown;
  }
}

export function LiquidGlassDecor() {
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      document.documentElement.classList.add("liquidgl-reduced-motion");
      return;
    }

    try {
      window.liquidGL?.({
        target: ".liquid-glass-decor",
        snapshot: "body",
        refraction: 0.018,
        frost: 0.18,
        tilt: false,
      });
    } catch {
      document.documentElement.classList.add("liquidgl-unavailable");
    }
  }, []);

  return <div className="liquid-glass-decor pointer-events-none" aria-hidden="true" />;
}
