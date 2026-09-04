import { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, type Farm, type Polyhouse } from "./api";
import { DEMO_MODE, demoFarm, demoPolyhouse } from "./demo-data";

const STORAGE_KEY = "sp_active_polyhouse";

interface PolyhouseState {
  farms: Farm[];
  polyhouses: Polyhouse[];
  activeId: string | null;
  active: Polyhouse | null;
  setActiveId: (id: string) => void;
  isLoading: boolean;
  error: unknown;
  refetch: () => void;
}

const Ctx = createContext<PolyhouseState | null>(null);

export function PolyhouseProvider({ children }: { children: ReactNode }) {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["farms"],
    queryFn: () => api.listFarms(),
    enabled: !DEMO_MODE,
  });

  const [activeId, setActiveIdState] = useState<string | null>(null);

  const farms = useMemo(() => DEMO_MODE ? [demoFarm] : (data?.farms ?? []), [data]);
  const polyhouses = useMemo(() => farms.flatMap((f) => f.polyhouses ?? []), [farms]);

  useEffect(() => {
    if (polyhouses.length === 0) return;
    const stored = typeof window !== "undefined" ? window.localStorage.getItem(STORAGE_KEY) : null;
    const valid = stored && polyhouses.some((p) => p.id === stored) ? stored : polyhouses[0]!.id;
    setActiveIdState((cur) => (cur && polyhouses.some((p) => p.id === cur) ? cur : valid));
  }, [polyhouses]);

  const setActiveId = (id: string) => {
    setActiveIdState(id);
    if (typeof window !== "undefined") window.localStorage.setItem(STORAGE_KEY, id);
  };

  const value: PolyhouseState = {
    farms,
    polyhouses,
    activeId,
    active: polyhouses.find((p) => p.id === activeId) ?? null,
    setActiveId,
    isLoading,
    error,
    refetch: () => void refetch(),
  };

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function usePolyhouse(): PolyhouseState {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("usePolyhouse must be used inside PolyhouseProvider");
  return ctx;
}
