import { useEffect, useRef } from "react";

declare global {
  interface Window {
    liquidGL?: (options: Record<string, unknown>) => unknown;
  }
}

function getInstanceCleanup(instance: unknown): (() => void) | undefined {
  if (!instance || typeof instance !== "object") {
    return undefined;
  }

  for (const methodName of ["destroy", "cleanup"] as const) {
    const method = (instance as Record<string, unknown>)[methodName];
    if (typeof method === "function") {
      return () => method.call(instance);
    }
  }

  return undefined;
}

export function LiquidGlassDecor() {
  const initializedRef = useRef(false);
  const cleanupRef = useRef<(() => void) | undefined>(undefined);
  const pendingCleanupRef = useRef<number | undefined>(undefined);

  useEffect(() => {
    if (pendingCleanupRef.current !== undefined) {
      window.clearTimeout(pendingCleanupRef.current);
      pendingCleanupRef.current = undefined;
    }

    const scheduleCleanup = () => {
      if (!cleanupRef.current) {
        return;
      }

      // liquidGL v2.0.1 has no cleanup API; defer a future instance cleanup so
      // Strict Mode's immediate replay keeps one lens while a real unmount cleans up.
      pendingCleanupRef.current = window.setTimeout(() => {
        cleanupRef.current?.();
        cleanupRef.current = undefined;
        initializedRef.current = false;
        pendingCleanupRef.current = undefined;
      }, 0);
    };

    if (initializedRef.current) {
      return scheduleCleanup;
    }

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      document.documentElement.classList.add("liquidgl-reduced-motion");
      return;
    }

    if (!document.querySelector(".liquid-glass-decor") || typeof window.liquidGL !== "function") {
      document.documentElement.classList.add("liquidgl-unavailable");
      return;
    }

    try {
      const instance = window.liquidGL({
        target: ".liquid-glass-decor",
        snapshot: "body",
        refraction: 0.018,
        frost: 0.18,
        tilt: false,
      });
      initializedRef.current = true;
      cleanupRef.current = getInstanceCleanup(instance);
      return scheduleCleanup;
    } catch {
      document.documentElement.classList.add("liquidgl-unavailable");
    }
  }, []);

  return <div className="liquid-glass-decor pointer-events-none" aria-hidden="true" />;
}
