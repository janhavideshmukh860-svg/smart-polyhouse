import { createFileRoute } from "@tanstack/react-router";
import { DEMO_MODE, DEMO_BADGE, demoDiseaseHistory, demoSensorHistory, demoRecommendations, demoAlerts } from "@/lib/demo-data";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { History as HistoryIcon } from "lucide-react";
import { PageHeader } from "@/components/AppShell";
import { EmptyState, ErrorState, LoadingState } from "@/components/states";
import { LayerLabel, Pill, SectionCard, severityTone, urgencyTone } from "@/components/data-bits";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { fmt, fmtTime } from "@/lib/features";
import { usePolyhouse } from "@/lib/polyhouse";

export const Route = createFileRoute("/app/history")({
  head: () => ({
    meta: [
      { title: "History — Smart Polyhouse" },
      {
        name: "description",
        content: "Recorded sensor readings, recommendations, alerts and disease predictions.",
      },
      { property: "og:title", content: "History — Smart Polyhouse" },
      {
        property: "og:description",
        content: "Recorded sensor readings, recommendations, alerts and disease predictions.",
      },
    ],
  }),
  component: HistoryPage,
});

const TABS = ["readings", "recommendations", "alerts", "disease"] as const;
type Tab = (typeof TABS)[number];

function HistoryPage() {
  const { activeId, active } = usePolyhouse();
  const [tab, setTab] = useState<Tab>("readings");

  const readings = useQuery({
    queryKey: ["sensor-history", activeId, 200],
    queryFn: DEMO_MODE ? () => Promise.resolve(demoSensorHistory) : () => api.sensorHistory(activeId!, 200),
    enabled: DEMO_MODE || (!!activeId && tab === "readings"),
  });
  const recs = useQuery({
    queryKey: ["recommendations", activeId, "all"],
    queryFn: DEMO_MODE ? () => Promise.resolve(demoRecommendations) : () => api.listRecommendations(activeId ?? undefined, 50),
    enabled: DEMO_MODE || (!!activeId && tab === "recommendations"),
  });
  const alerts = useQuery({
    queryKey: ["alerts", activeId, false],
    queryFn: DEMO_MODE ? () => Promise.resolve(demoAlerts) : () => api.listAlerts(activeId ?? undefined, false, 50),
    enabled: DEMO_MODE || (!!activeId && tab === "alerts"),
  });
  const disease = useQuery({
    queryKey: ["disease-history", activeId],
    queryFn: DEMO_MODE ? () => Promise.resolve(demoDiseaseHistory) : () => api.diseaseHistory(activeId!, 50),
    enabled: DEMO_MODE || (!!activeId && tab === "disease"),
    retry: false,
  });

  const current = { readings, recommendations: recs, alerts, disease }[tab];

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <PageHeader
        title="History"
        description={`Everything the backend has recorded${active ? ` for ${active.name}` : ""}.`}
      />

      {DEMO_MODE ? <Pill tone="warning" className="text-[10px]">{DEMO_BADGE}</Pill> : null}

      <div className="flex flex-wrap items-center gap-2">
        <LayerLabel layer="measured" />
        {TABS.map((t) => (
          <Button key={t} size="sm" variant={tab === t ? "default" : "outline"} onClick={() => setTab(t)}>
            {t}
          </Button>
        ))}
      </div>

      {!activeId ? (
        <EmptyState title="No polyhouse selected" description="History is scoped to a polyhouse." />
      ) : current.isLoading ? (
        <LoadingState label="Loading history…" />
      ) : current.error ? (
        <ErrorState error={current.error} onRetry={() => void current.refetch()} />
      ) : (
        <SectionCard title={`Recorded ${tab}`} description="Newest entries first, straight from the API.">
          {tab === "readings" ? (
            (readings.data?.readings.length ?? 0) === 0 ? (
              <EmptyState icon={<HistoryIcon className="h-5 w-5" />} title="No readings recorded" />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[640px] text-sm">
                  <thead>
                    <tr className="border-b border-border text-left text-muted-foreground">
                      <th className="py-2 font-medium">Recorded</th>
                      <th className="py-2 text-right font-medium">Moisture %</th>
                      <th className="py-2 text-right font-medium">Soil °C</th>
                      <th className="py-2 text-right font-medium">Air °C</th>
                      <th className="py-2 text-right font-medium">Pressure inHg</th>
                    </tr>
                  </thead>
                  <tbody>
                    {readings.data!.readings.map((r) => (
                      <tr key={r.id} className="border-b border-border/60 last:border-0">
                        <td className="py-2 text-muted-foreground">{fmtTime(r.recorded_at)}</td>
                        <td className="py-2 text-right">{fmt(r.volumetric_moisture_pct, 2)}</td>
                        <td className="py-2 text-right">{fmt(r.soil_temperature_c, 2)}</td>
                        <td className="py-2 text-right">{fmt(r.atm_temperature_c, 2)}</td>
                        <td className="py-2 text-right">{fmt(r.atm_pressure_inhg, 2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )
          ) : null}

          {tab === "recommendations" ? (
            (recs.data?.recommendations.length ?? 0) === 0 ? (
              <EmptyState icon={<HistoryIcon className="h-5 w-5" />} title="No recommendations recorded" />
            ) : (
              <ul className="space-y-3">
                {recs.data!.recommendations.map((r) => (
                  <li key={r.id} className="border-b border-border/60 pb-3 last:border-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <Pill tone={urgencyTone(r.urgency)}>{r.urgency}</Pill>
                      <span className="text-xs text-muted-foreground">{fmtTime(r.created_at)}</span>
                      <span className="text-xs text-muted-foreground">· {r.domain}</span>
                    </div>
                    <p className="mt-1 text-sm text-foreground">{r.recommendation_text}</p>
                    <p className="text-sm text-muted-foreground">{r.reason}</p>
                  </li>
                ))}
              </ul>
            )
          ) : null}

          {tab === "alerts" ? (
            (alerts.data?.alerts.length ?? 0) === 0 ? (
              <EmptyState icon={<HistoryIcon className="h-5 w-5" />} title="No alerts recorded" />
            ) : (
              <ul className="space-y-3">
                {alerts.data!.alerts.map((a) => (
                  <li key={a.id} className="border-b border-border/60 pb-3 last:border-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <Pill tone={severityTone(a.severity)}>{a.severity}</Pill>
                      <span className="text-xs text-muted-foreground">{fmtTime(a.created_at)}</span>
                      <span className="text-xs text-muted-foreground">· {a.status}</span>
                    </div>
                    <p className="mt-1 text-sm text-foreground">{a.message}</p>
                  </li>
                ))}
              </ul>
            )
          ) : null}

          {tab === "disease" ? (
            (disease.data?.predictions.length ?? 0) === 0 ? (
              <EmptyState icon={<HistoryIcon className="h-5 w-5" />} title="No disease predictions recorded" />
            ) : (
              <ul className="space-y-3">
                {disease.data!.predictions.map((p) => (
                  <li key={p.id} className="flex flex-wrap items-center justify-between gap-2 border-b border-border/60 pb-3 last:border-0">
                    <div>
                      <p className="text-sm text-foreground">{p.predicted_class}</p>
                      <p className="text-xs text-muted-foreground">{fmtTime(p.created_at)}</p>
                    </div>
                    <span className="text-sm">{fmt(p.confidence * 100, 2, " %")}</span>
                  </li>
                ))}
              </ul>
            )
          ) : null}
        </SectionCard>
      )}
    </div>
  );
}
