import { useEffect, useState } from "react";
import type { DependencyList } from "react";

export type AsyncData<T> =
  | { status: "loading"; data: null; error: null }
  | { status: "ready"; data: T; error: null }
  | { status: "error"; data: null; error: string };

export function useAsyncData<T>(loader: () => Promise<T>, deps: DependencyList): AsyncData<T> {
  const [state, setState] = useState<AsyncData<T>>({ status: "loading", data: null, error: null });

  useEffect(() => {
    let active = true;
    setState({ status: "loading", data: null, error: null });

    loader()
      .then((data) => {
        if (active) setState({ status: "ready", data, error: null });
      })
      .catch((error: unknown) => {
        if (active) {
          setState({
            status: "error",
            data: null,
            error: error instanceof Error ? error.message : "Erro inesperado",
          });
        }
      });

    return () => {
      active = false;
    };
  }, deps);

  return state;
}
