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
    const targetSelector = ".liquid-glass-surface:not([data-liquidgl-bound])";
    const pendingSelector = ".liquid-glass-surface[data-liquidgl-pending]";

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

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      document.documentElement.classList.add("liquidgl-reduced-motion");
      return;
    }

    if (typeof window.liquidGL !== "function") {
      document.documentElement.classList.add("liquidgl-unavailable");
      return;
    }

    const hydrateSurfaces = () => {
      const surfaces = Array.from(document.querySelectorAll<HTMLElement>(targetSelector));
      if (surfaces.length === 0) return;

      surfaces.forEach((surface) => {
        surface.dataset.liquidglPending = "true";
      });

      const instance = window.liquidGL?.({
        target: pendingSelector,
        snapshot: "body",
        refraction: 0.004,
        frost: 0.08,
        bevelDepth: 0.035,
        bevelWidth: 0.08,
        shadow: false,
        tilt: false,
      });
      surfaces.forEach((surface) => {
        delete surface.dataset.liquidglPending;
        surface.dataset.liquidglBound = "true";
      });
      initializedRef.current = true;
      cleanupRef.current = getInstanceCleanup(instance);
    };

    try {
      hydrateSurfaces();
      const observer = new MutationObserver(() => {
        try {
          hydrateSurfaces();
        } catch {
          document.documentElement.classList.add("liquidgl-unavailable");
        }
      });
      observer.observe(document.body, { childList: true, subtree: true });
      return () => {
        observer.disconnect();
        scheduleCleanup();
      };
    } catch {
      document.documentElement.classList.add("liquidgl-unavailable");
    }
  }, []);

  return null;
}
